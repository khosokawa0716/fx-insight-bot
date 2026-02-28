# Cloud Run デプロイ手順

このドキュメントでは、FX Insight BotのバックエンドをCloud Runにデプロイする手順を説明します。

---

## 📋 アーキテクチャ概要

本システムは **2つの Cloud Run サービス** で構成されています。

| サービス | 用途 | 認証 | 呼び出し元 |
|---------|------|------|-----------|
| `fx-insight-bot` | 読み取り専用API（ダッシュボード向け） | allUsers（公開） | Firebase Hosting |
| `fx-insight-bot-exec` | 取引実行専用API | cloud-scheduler-sa のみ | Cloud Scheduler |

> **重要**: 取引実行エンドポイント（`/api/v1/trade/execute`）は `fx-insight-bot-exec` にのみ存在します。
> `fx-insight-bot` は読み取り専用のため、取引実行はできません。

---

## 📋 前提条件

### 1. GCP プロジェクトの準備

```bash
export GCP_PROJECT_ID="fx-insight-bot-prod"
export GCP_REGION="asia-northeast1"
export SERVICE_ACCOUNT="fx-insight-bot-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project ${GCP_PROJECT_ID}
```

### 2. 必要なAPIの有効化

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 3. Secret Manager にAPIキーを登録（初回のみ）

GMOコインのAPIキーは環境変数ではなく Secret Manager で管理します。

```bash
# GMO API Key
echo -n "YOUR_GMO_API_KEY" | gcloud secrets create gmo-api-key --data-file=-

# GMO API Secret
echo -n "YOUR_GMO_API_SECRET" | gcloud secrets create gmo-api-secret --data-file=-

# サービスアカウントにアクセス権を付与
gcloud secrets add-iam-policy-binding gmo-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gmo-api-secret \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

### 4. サービスアカウントへの権限付与

```bash
# Firestore
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/datastore.user"

# Vertex AI
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

# ログ書き込み
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/logging.logWriter"
```

---

## 🚀 デプロイ方法

### Service A: 読み取り専用API（`fx-insight-bot`）

```bash
cd backend

gcloud run deploy fx-insight-bot \
  --source=. \
  --region=${GCP_REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=${SERVICE_ACCOUNT} \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},FIRESTORE_DATABASE_ID=fx-insight-bot-db,GCP_LOCATION=${GCP_REGION}" \
  --set-secrets="GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --max-instances=10 \
  --min-instances=0
```

### Service B: 取引実行専用API（`fx-insight-bot-exec`）

```bash
cd backend

gcloud run deploy fx-insight-bot-exec \
  --source=. \
  --region=${GCP_REGION} \
  --platform=managed \
  --no-allow-unauthenticated \
  --service-account=${SERVICE_ACCOUNT} \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},FIRESTORE_DATABASE_ID=fx-insight-bot-db,GCP_LOCATION=${GCP_REGION}" \
  --set-secrets="GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --max-instances=3 \
  --min-instances=0
```

---

## 🔄 Cloud Scheduler との連携

Cloud Scheduler は Service B（`fx-insight-bot-exec`）を OIDC 認証付きで呼び出します。

```bash
# Cloud Scheduler 用サービスアカウント
SCHEDULER_SA="cloud-scheduler-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Service B の URL を取得
EXEC_URL=$(gcloud run services describe fx-insight-bot-exec \
  --region=${GCP_REGION} \
  --format='value(status.url)')

# ニュース収集（毎日 8:00 / 20:00 JST）
gcloud scheduler jobs create http fx-news-collect \
  --location=${GCP_REGION} \
  --schedule="0 8,20 * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="${EXEC_URL}/api/v1/news/collect" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{}' \
  --attempt-deadline=300s \
  --oidc-service-account-email=${SCHEDULER_SA} \
  --oidc-token-audience=${EXEC_URL}

# 取引実行（月〜金 9:00 / 21:00 JST、dry_run=false）
gcloud scheduler jobs create http fx-trade-execute \
  --location=${GCP_REGION} \
  --schedule="0 9,21 * * 1-5" \
  --time-zone="Asia/Tokyo" \
  --uri="${EXEC_URL}/api/v1/trade/execute" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"dry_run": false}' \
  --attempt-deadline=300s \
  --oidc-service-account-email=${SCHEDULER_SA} \
  --oidc-token-audience=${EXEC_URL}
```

---

## 🔧 更新・再デプロイ

コードを修正した後は、両サービスを再デプロイします。

```bash
cd backend

# Service A
gcloud run deploy fx-insight-bot --source=. --region=${GCP_REGION}

# Service B
gcloud run deploy fx-insight-bot-exec --source=. --region=${GCP_REGION}
```

---

## 🧪 デプロイ後の動作確認

```bash
# Service A の URL を取得
SERVICE_A_URL=$(gcloud run services describe fx-insight-bot \
  --region=${GCP_REGION} \
  --format='value(status.url)')

# ヘルスチェック
curl ${SERVICE_A_URL}/health

# 取引履歴の確認（Service A 経由）
curl ${SERVICE_A_URL}/api/v1/trade/history
```

---

## 📊 モニタリング

```bash
# Service A のログ
gcloud run services logs tail fx-insight-bot --region=${GCP_REGION}

# Service B のログ
gcloud run services logs tail fx-insight-bot-exec --region=${GCP_REGION}
```

---

## 🗑️ 削除

```bash
gcloud run services delete fx-insight-bot --region=${GCP_REGION}
gcloud run services delete fx-insight-bot-exec --region=${GCP_REGION}
```

---

## ✅ デプロイチェックリスト

- [ ] Secret Manager に `gmo-api-key` / `gmo-api-secret` を登録済み
- [ ] サービスアカウントに必要な権限を付与済み
- [ ] Service A をデプロイ（`--allow-unauthenticated`）
- [ ] Service B をデプロイ（`--no-allow-unauthenticated`）
- [ ] Firebase Hosting のリライト設定で Service A を参照していることを確認
- [ ] Cloud Scheduler のジョブが Service B を OIDC 認証で呼び出していることを確認
- [ ] `/health` エンドポイントが正常に応答することを確認
- [ ] ログが正しく出力されていることを確認

---

**最終更新日**: 2026-02-28
