# Cloud Run 運用ガイド

**構成**: 2サービス構成（2026-02-27 〜）
**GCPプロジェクト**: `fx-insight-bot-prod`
**リージョン**: `asia-northeast1`

| サービス | URL | 認証 | 用途 |
|---|---|---|---|
| fx-insight-bot | https://fx-insight-bot-755346299346.asia-northeast1.run.app | allUsers | ダッシュボード向け読み取り専用 |
| fx-insight-bot-exec | https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app | cloud-scheduler-sa のみ | 取引実行・settle-check |

---

## デプロイ

> **注意**: `export GCP_PROJECT_ID` を忘れると Cloud Run の環境変数が空になり `RESOURCE_PROJECT_INVALID` エラーが発生する。

### フロントエンド

```bash
cd frontend && npm run build
firebase deploy --only hosting --project fx-insight-bot-prod
```

### Service A（読み取り専用 / allUsers）

```bash
export GCP_PROJECT_ID=fx-insight-bot-prod

gcloud run deploy fx-insight-bot \
  --source backend/ \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --allow-unauthenticated \
  --set-secrets "GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --set-env-vars "ENVIRONMENT=production,FIRESTORE_DATABASE_ID=fx-insight-bot-db,GCP_PROJECT_ID=fx-insight-bot-prod"
```

### Service B（取引実行・settle-check / cloud-scheduler-sa のみ）

```bash
export GCP_PROJECT_ID=fx-insight-bot-prod

gcloud run deploy fx-insight-bot-exec \
  --source backend/ \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --no-allow-unauthenticated \
  --set-secrets "GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --set-env-vars "ENVIRONMENT=production,FIRESTORE_DATABASE_ID=fx-insight-bot-db,GCP_PROJECT_ID=fx-insight-bot-prod" \
  --memory 512Mi \
  --concurrency 1 \
  --max-instances 2 \
  --timeout 300
```

---

## サービス状態確認

```bash
# ヘルスチェック
curl https://fx-insight-bot-755346299346.asia-northeast1.run.app/health

# サービス詳細
gcloud run services describe fx-insight-bot --region asia-northeast1 --project fx-insight-bot-prod
gcloud run services describe fx-insight-bot-exec --region asia-northeast1 --project fx-insight-bot-prod

# リビジョン一覧
gcloud run revisions list --service=fx-insight-bot --region asia-northeast1 --project fx-insight-bot-prod
```

---

## ログ確認

```bash
# Service A 直近ログ（30件）
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fx-insight-bot" \
  --limit 30 --format "value(textPayload)" --project fx-insight-bot-prod

# Service B 直近ログ（30件）
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fx-insight-bot-exec" \
  --limit 30 --format "value(textPayload)" --project fx-insight-bot-prod

# エラーログのみ
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 20 --format "value(textPayload)" --project fx-insight-bot-prod
```

---

## Cloud Scheduler 管理

### 現在のジョブ一覧

| ジョブ名 | スケジュール（JST） | 向き先 | 認証 |
|---|---|---|---|
| fx-news-collect | 毎日 8:00 / 20:00 | Service A: POST /api/v1/news/collect | なし |
| fx-trade-execute | 月〜金 9:00 / 21:00 | Service B: POST /api/v1/trade/execute | OIDC |
| fx-settle-check | 毎日 8:30（土日含む） | Service B: POST /api/v1/trade/settle-check | OIDC |

```bash
# ジョブ一覧確認
gcloud scheduler jobs list --location asia-northeast1 --project fx-insight-bot-prod
```

### 取引の一時停止 / 再開

```bash
# 停止
gcloud scheduler jobs pause fx-trade-execute --location asia-northeast1 --project fx-insight-bot-prod

# 再開
gcloud scheduler jobs resume fx-trade-execute --location asia-northeast1 --project fx-insight-bot-prod
```

### 手動実行（テスト用）

```bash
# ニュース収集を即時実行
gcloud scheduler jobs run fx-news-collect --location asia-northeast1 --project fx-insight-bot-prod

# 取引実行を即時実行（本番注文が走るので注意）
gcloud scheduler jobs run fx-trade-execute --location asia-northeast1 --project fx-insight-bot-prod

# settle-check を即時実行
gcloud scheduler jobs run fx-settle-check --location asia-northeast1 --project fx-insight-bot-prod
```

### settle-check を Service B に curl で直接実行（テスト用）

```bash
TOKEN=$(gcloud auth print-identity-token)

curl -s -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app/api/v1/trade/settle-check \
  | python3 -m json.tool
```

---

## Secret Manager 管理

```bash
# シークレット一覧
gcloud secrets list --project fx-insight-bot-prod

# シークレットの値を確認
gcloud secrets versions access latest --secret=gmo-api-key --project fx-insight-bot-prod

# シークレットの更新（新バージョン追加）
echo -n "NEW_API_KEY" | gcloud secrets versions add gmo-api-key --data-file=- --project fx-insight-bot-prod

# 古いバージョンを無効化
gcloud secrets versions disable VERSION_ID --secret=gmo-api-key --project fx-insight-bot-prod
```

---

## API エンドポイント一覧

### Service A（読み取り専用）

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/health` | ヘルスチェック |
| POST | `/api/v1/news/collect` | ニュース収集 |
| GET | `/api/v1/news` | ニュース一覧 |
| GET | `/api/v1/signals` | シグナル一覧 |
| GET | `/api/v1/trade/account` | 口座情報 |
| GET | `/api/v1/trade/positions` | ポジション一覧 |
| GET | `/api/v1/trade/orders` | 注文一覧 |
| GET | `/api/v1/trade/history` | 取引履歴 |
| GET | `/api/v1/trade/monthly-summary` | 月間損益（研究用） |
| GET | `/api/v1/trade/risk/summary` | リスクサマリー |

### Service B（認証必須）

| メソッド | パス | 説明 |
|---|---|---|
| POST | `/api/v1/trade/execute` | 取引実行（IFDOCO） |
| POST | `/api/v1/trade/settle-check` | 決済チェック・Firestore更新 |

---

## トラブルシューティング

### コンテナが起動しない

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fx-insight-bot" \
  --limit 30 --format "value(textPayload)" --project fx-insight-bot-prod
```

よくある原因:
- **ImportError**: `requirements.txt` にパッケージが不足
- **環境変数不足**: `GCP_PROJECT_ID` が未設定 → `RESOURCE_PROJECT_INVALID` エラー
- **ポート不一致**: Dockerfile の `PORT` と `CMD` のポートが一致しているか確認

### 前のリビジョンに戻す

```bash
# リビジョン一覧を確認
gcloud run revisions list --service=fx-insight-bot --region asia-northeast1 --project fx-insight-bot-prod

# 特定のリビジョンにトラフィックを切り替え
gcloud run services update-traffic fx-insight-bot \
  --to-revisions=REVISION_NAME=100 \
  --region asia-northeast1 \
  --project fx-insight-bot-prod
```
