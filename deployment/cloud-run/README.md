# Cloud Run デプロイ手順

このドキュメントでは、FX Insight BotのバックエンドをCloud Runにデプロイする手順を説明します。

---

## 📋 前提条件

### 1. GCP プロジェクトの準備

```bash
# プロジェクトIDを設定
export GCP_PROJECT_ID="fx-insight-bot-prod"
export GCP_REGION="asia-northeast1"

# gcloud CLIでプロジェクトを設定
gcloud config set project ${GCP_PROJECT_ID}
```

### 2. 必要なAPIの有効化

```bash
# Cloud Run API
gcloud services enable run.googleapis.com

# Container Registry API (イメージ保存用)
gcloud services enable containerregistry.googleapis.com

# Artifact Registry API (推奨)
gcloud services enable artifactregistry.googleapis.com

# Cloud Build API (自動ビルド用)
gcloud services enable cloudbuild.googleapis.com
```

### 3. サービスアカウントの準備

Cloud Runで使用するサービスアカウントに以下の権限を付与:

```bash
# サービスアカウント名
SERVICE_ACCOUNT="fx-insight-bot-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# 必要な権限を付与
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/logging.logWriter"
```

---

## 🚀 デプロイ方法

### Option 1: gcloud コマンドで直接デプロイ（推奨・最も簡単）

```bash
cd backend

# Cloud Runにデプロイ（自動でビルド→デプロイ）
gcloud run deploy fx-insight-bot-api \
  --source=. \
  --region=${GCP_REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=${SERVICE_ACCOUNT} \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},FIRESTORE_DATABASE_ID=fx-insight-bot-db,GCP_LOCATION=${GCP_REGION}" \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --max-instances=10 \
  --min-instances=0
```

**このコマンド1つで完了します！**

---

### Option 2: Dockerイメージを手動ビルド→デプロイ

より細かい制御が必要な場合:

#### Step 1: Dockerイメージをビルド

```bash
cd backend

# Artifact Registryにリポジトリを作成（初回のみ）
gcloud artifacts repositories create fx-insight-bot \
  --repository-format=docker \
  --location=${GCP_REGION} \
  --description="FX Insight Bot container images"

# Dockerイメージをビルド
docker build -t ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/fx-insight-bot/api:latest .

# イメージをプッシュ
docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/fx-insight-bot/api:latest
```

#### Step 2: Cloud Runにデプロイ

```bash
gcloud run deploy fx-insight-bot-api \
  --image=${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/fx-insight-bot/api:latest \
  --region=${GCP_REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=${SERVICE_ACCOUNT} \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},FIRESTORE_DATABASE_ID=fx-insight-bot-db,GCP_LOCATION=${GCP_REGION}" \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300
```

---

## 🔄 Cloud Scheduler との連携

### Cloud Schedulerジョブの作成

```bash
# デプロイされたCloud RunのURLを取得
SERVICE_URL=$(gcloud run services describe fx-insight-bot-api \
  --region=${GCP_REGION} \
  --format='value(status.url)')

echo "Service URL: ${SERVICE_URL}"

# Cloud Schedulerジョブを作成（1日1回、9:00 JST）
gcloud scheduler jobs create http fx-news-collection-daily \
  --location=${GCP_REGION} \
  --schedule="0 9 * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="${SERVICE_URL}/api/v1/news/collect" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{}' \
  --attempt-deadline=300s \
  --max-retry-attempts=3 \
  --oidc-service-account-email=${SERVICE_ACCOUNT}
```

### スケジューラーのテスト実行

```bash
# 手動でジョブを実行
gcloud scheduler jobs run fx-news-collection-daily \
  --location=${GCP_REGION}

# ログを確認
gcloud run services logs read fx-insight-bot-api \
  --region=${GCP_REGION} \
  --limit=50
```

---

## 🧪 デプロイ後の動作確認

### 1. ヘルスチェック

```bash
SERVICE_URL=$(gcloud run services describe fx-insight-bot-api \
  --region=${GCP_REGION} \
  --format='value(status.url)')

# ヘルスチェック
curl ${SERVICE_URL}/health
```

**期待される出力:**
```json
{
  "status": "healthy",
  "gcp_project": "fx-insight-bot-prod",
  "firestore_db": "fx-insight-bot-db",
  "location": "asia-northeast1"
}
```

### 2. ニュース収集エンドポイントのテスト

```bash
# ニュース収集を手動実行
curl -X POST ${SERVICE_URL}/api/v1/news/collect \
  -H "Content-Type: application/json" \
  -d '{}'
```

**期待される出力:**
```json
{
  "status": "success",
  "message": "Collected 5 news items, saved 5 items",
  "stats": {
    "analyzed": 5,
    "saved": 5,
    "skipped": 0,
    "failed": 0,
    "saved_ids": ["news_xxx", "news_yyy", ...]
  }
}
```

### 3. APIドキュメントの確認

```bash
# Swagger UIにアクセス
open ${SERVICE_URL}/docs
```

---

## 📊 モニタリング

### ログの確認

```bash
# リアルタイムログ
gcloud run services logs tail fx-insight-bot-api \
  --region=${GCP_REGION}

# 最新50件のログ
gcloud run services logs read fx-insight-bot-api \
  --region=${GCP_REGION} \
  --limit=50
```

### メトリクスの確認

Cloud Consoleでメトリクスを確認:
```
https://console.cloud.google.com/run/detail/${GCP_REGION}/fx-insight-bot-api/metrics
```

---

## 💰 コスト管理

### 無料枠

Cloud Runの無料枠（毎月）:
- **リクエスト数**: 200万リクエスト
- **CPU時間**: 180,000 vCPU秒
- **メモリ**: 360,000 GiB秒
- **ネットワーク**: 1 GB（北米のみ）

### コスト試算（1日1回の定期実行）

**想定負荷:**
- リクエスト: 30回/月（1日1回 × 30日）
- 実行時間: 約20秒/回
- メモリ: 512MB

**月間コスト: $0**（無料枠内）

### コスト最適化の設定

```bash
# 最小インスタンス数を0に設定（アイドル時は課金なし）
gcloud run services update fx-insight-bot-api \
  --region=${GCP_REGION} \
  --min-instances=0

# 最大インスタンス数を制限
gcloud run services update fx-insight-bot-api \
  --region=${GCP_REGION} \
  --max-instances=5
```

---

## 🔧 更新・再デプロイ

### コードを修正した後

```bash
cd backend

# 再デプロイ（自動で新しいリビジョンが作成される）
gcloud run deploy fx-insight-bot-api \
  --source=. \
  --region=${GCP_REGION}
```

### ロールバック

```bash
# リビジョン一覧を確認
gcloud run revisions list \
  --service=fx-insight-bot-api \
  --region=${GCP_REGION}

# 特定のリビジョンにロールバック
gcloud run services update-traffic fx-insight-bot-api \
  --region=${GCP_REGION} \
  --to-revisions=REVISION_NAME=100
```

---

## 🗑️ 削除

### Cloud Runサービスの削除

```bash
gcloud run services delete fx-insight-bot-api \
  --region=${GCP_REGION}
```

### Cloud Schedulerジョブの削除

```bash
gcloud scheduler jobs delete fx-news-collection-daily \
  --location=${GCP_REGION}
```

---

## ❓ トラブルシューティング

### よくある問題

#### 1. デプロイ時のエラー

**エラー:** `Permission denied`

**解決方法:**
```bash
# サービスアカウントに必要な権限を確認
gcloud projects get-iam-policy ${GCP_PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT}"
```

#### 2. ニュース収集のタイムアウト

**エラー:** `Deadline exceeded`

**解決方法:**
```bash
# タイムアウトを延長（最大3600秒）
gcloud run services update fx-insight-bot-api \
  --region=${GCP_REGION} \
  --timeout=600
```

#### 3. メモリ不足

**エラー:** `Memory limit exceeded`

**解決方法:**
```bash
# メモリを増やす
gcloud run services update fx-insight-bot-api \
  --region=${GCP_REGION} \
  --memory=1Gi
```

---

## 📚 参考リンク

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud Scheduler ドキュメント](https://cloud.google.com/scheduler/docs)
- [Cloud Run 料金](https://cloud.google.com/run/pricing)

---

## ✅ チェックリスト

デプロイ前の確認事項:

- [ ] GCPプロジェクトが作成済み
- [ ] 必要なAPIが有効化済み
- [ ] サービスアカウントが作成済み
- [ ] サービスアカウントに必要な権限が付与済み
- [ ] Firestoreが有効化済み
- [ ] ローカルでFastAPIが正常に動作することを確認済み

デプロイ後の確認事項:

- [ ] `/health` エンドポイントが正常に応答
- [ ] `/api/v1/news/collect` が正常に動作
- [ ] Cloud Schedulerが設定済み
- [ ] ログが正しく出力されている

---

**最終更新日**: 2026-01-10
