# 2026-02-27 エンドポイント認証：Cloud Run サービス分割

## 背景・目的

`/api/v1/trade/execute` など POST エンドポイントは、URLを知っていれば誰でも実行できる状態。
Cloud Run の IAM 認証を使って Cloud Scheduler 以外からのアクセスを遮断する。

### 方針：Cloud Run を2サービスに分割

```
【変更前】
ダッシュボード ─┐
                ├→ Firebase Hosting → fx-insight-bot（1つのサービス）← Cloud Scheduler
Cloud Scheduler ┘

【変更後】
ダッシュボード → Firebase Hosting → fx-insight-bot（Service A: 読み取り専用）
                                          --allow-unauthenticated（誰でも読める）

Cloud Scheduler → fx-insight-bot-exec（Service B: 取引実行専用）
                        --no-allow-unauthenticated（cloud-scheduler-sa のみ実行可）
```

- **firebase.json の変更は不要**（ダッシュボードは GET しか使わないため Service A のまま）
- **同じ Docker イメージ**を2つの Cloud Run サービスとして動かす

---

## 現在の IAM 状態（作業前）

Step 2〜3 の作業で以下の状態になっている：
- `allUsers`（誰でもOK）← 復元済み
- `cloud-scheduler-sa@fx-insight-bot-prod.iam.gserviceaccount.com`
- `service-755346299346@gcp-sa-firebase.iam.gserviceaccount.com`

Service B を新設後、Service A はそのまま（触らない）。
Cloud Scheduler の向き先を Service B の URL に変更するだけ。

---

## 作業手順

### Step 1: 既存サービスの設定を確認する

Service B に同じ設定をコピーするため、現在の構成を確認する。

```bash
gcloud run services describe fx-insight-bot \
  --region asia-northeast1 \
  --project fx-insight-bot-prod
```

**意味:** `fx-insight-bot` サービスの詳細（環境変数・シークレット・メモリ設定など）を表示する。

---

### Step 2: Service B（取引実行専用）をデプロイする

```bash
gcloud run deploy fx-insight-bot-exec \
  --source backend/ \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --no-allow-unauthenticated \
  --set-secrets "GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --set-env-vars "ENVIRONMENT=production,FIRESTORE_DATABASE_ID=fx-insight-bot-db" \
  --memory 512Mi \
  --concurrency 1 \
  --max-instances 2 \
  --timeout 300
```

**意味:**
- `gcloud run deploy fx-insight-bot-exec` → `fx-insight-bot-exec` という名前で新しい Cloud Run サービスを作成
- `--source backend/` → `backend/` フォルダのコードを Docker ビルドしてデプロイ
- `--no-allow-unauthenticated` → 認証なしのアクセスを拒否（IAM 認証のみ許可）
- `--set-secrets` → Secret Manager からシークレットを注入（GMO API キーなど）
- `--set-env-vars` → 環境変数を設定

> **注意:** デプロイ完了後に Service B の URL が表示される（例: `https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app`）。この URL を次の手順で使う。

---

### Step 3: Service B に Cloud Scheduler の実行権限を付与する

```bash
gcloud run services add-iam-policy-binding fx-insight-bot-exec \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --member "serviceAccount:cloud-scheduler-sa@fx-insight-bot-prod.iam.gserviceaccount.com" \
  --role "roles/run.invoker"
```

**意味:** `cloud-scheduler-sa` というサービスアカウントに、`fx-insight-bot-exec` を呼び出す権限（`run.invoker`）を付与する。Cloud Scheduler はこのアカウントを使って Service B を呼び出す。

---

### Step 4: Cloud Scheduler のジョブを Service B に向け直す

> **前提:** Step 2〜3 の作業で Cloud Scheduler のジョブはすでに OIDC トークン付きになっている。URL だけ変更する。

**`fx-news-collect` の更新:**
```bash
gcloud scheduler jobs update http fx-news-collect \
  --location asia-northeast1 \
  --project fx-insight-bot-prod \
  --uri https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app/api/v1/news/collect
```

**`fx-trade-execute` の更新:**
```bash
gcloud scheduler jobs update http fx-trade-execute \
  --location asia-northeast1 \
  --project fx-insight-bot-prod \
  --uri https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app/api/v1/trade/execute
```

**意味:** Cloud Scheduler ジョブが POST を送る先の URL を、新しい Service B の URL に変更する。

> **注意:** `fx-insight-bot-exec-755346299346` の部分は Step 2 で表示された実際の URL に置き換える。

---

### Step 5: 動作確認

#### 5-1. ダッシュボード（Service A）が動いているか
```
ブラウザで https://fx-insight-bot-prod.web.app を開き、
取引履歴・月間統計カードが表示されることを確認
```

#### 5-2. Service B に認証なし curl → 403 が返るか（セキュリティ確認）
```bash
curl -X POST "https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app/api/v1/trade/execute" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"USD_JPY","dry_run":true}'
# → 403 Forbidden が返れば成功
```

#### 5-3. IDトークン付き curl → 正常実行されるか
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -X POST "https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app/api/v1/trade/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"USD_JPY","dry_run":true}'
# → 正常なレスポンスが返れば成功
```

**意味:**
- `gcloud auth print-identity-token` → 自分の GCP アカウントの ID トークン（=一時的な身分証明書）を取得
- `Authorization: Bearer $TOKEN` → リクエストヘッダーに ID トークンを付けて送信
- Cloud Run がトークンを検証し、プロジェクト内の正規ユーザーと判断したら実行を許可

#### 5-4. Cloud Scheduler から手動実行
```bash
# fx-news-collect を今すぐ実行
gcloud scheduler jobs run fx-news-collect \
  --location asia-northeast1 \
  --project fx-insight-bot-prod

# fx-trade-execute を今すぐ実行（dry_run=false なので注意）
gcloud scheduler jobs run fx-trade-execute \
  --location asia-northeast1 \
  --project fx-insight-bot-prod
```

**意味:** スケジュール時刻を待たずに今すぐジョブを実行する。Cloud Scheduler ログで成功（`SUCCESS`）を確認する。

---

## 完了後のクリーンアップ（オプション）

Service A に残っている不要な IAM バインディングを削除しておくと整理できる：

```bash
# Service A から cloud-scheduler-sa を削除（もう Service A を呼ばないので不要）
gcloud run services remove-iam-policy-binding fx-insight-bot \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --member "serviceAccount:cloud-scheduler-sa@fx-insight-bot-prod.iam.gserviceaccount.com" \
  --role "roles/run.invoker"

# Service A から gcp-sa-firebase を削除（allUsers で開いているので不要）
gcloud run services remove-iam-policy-binding fx-insight-bot \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --member "serviceAccount:service-755346299346@gcp-sa-firebase.iam.gserviceaccount.com" \
  --role "roles/run.invoker"
```

---

## まとめ

| | Service A（fx-insight-bot） | Service B（fx-insight-bot-exec） |
|---|---|---|
| 用途 | 読み取り（ダッシュボード） | 取引実行・ニュース収集 |
| アクセス元 | Firebase Hosting 経由のブラウザ | Cloud Scheduler のみ |
| IAM 設定 | allUsers（誰でも読める） | cloud-scheduler-sa のみ |
| firebase.json | 変更なし | 登録しない |
