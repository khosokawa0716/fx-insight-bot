# Cloud Scheduler デプロイ手順

このディレクトリには、ニュース収集の定期実行をCloud Schedulerで設定するためのファイルが含まれています。

## 📋 ファイル構成

```
deployment/cloud-scheduler/
├── README.md              # このファイル
├── scheduler.yaml         # Cloud Scheduler設定
├── main.py               # Cloud Functions エントリポイント
└── requirements.txt      # Cloud Functions 依存パッケージ
```

## 🚀 デプロイ方法

### Option 1: Cloud Functions を使用（推奨 - シンプル）

#### 1. Cloud Functions のデプロイ

```bash
# プロジェクトルートから実行
cd deployment/cloud-scheduler

# Cloud Functionsにデプロイ
gcloud functions deploy fx-news-collection \
  --gen2 \
  --runtime=python310 \
  --region=asia-northeast1 \
  --source=. \
  --entry-point=collect_fx_news \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=300s \
  --memory=512MB \
  --set-env-vars GCP_PROJECT_ID=fx-insight-bot-prod,FIRESTORE_DATABASE_ID=fx-insight-bot-db \
  --service-account=YOUR_SERVICE_ACCOUNT@fx-insight-bot-prod.iam.gserviceaccount.com
```

**重要:**
- `YOUR_SERVICE_ACCOUNT` を実際のサービスアカウント名に置き換えてください
- サービスアカウントには以下の権限が必要です:
  - Vertex AI User
  - Cloud Datastore User
  - Logs Writer

#### 2. Cloud Scheduler の作成

```bash
# デプロイされたCloud FunctionsのURLを取得
FUNCTION_URL=$(gcloud functions describe fx-news-collection \
  --region=asia-northeast1 \
  --gen2 \
  --format='value(serviceConfig.uri)')

echo "Function URL: $FUNCTION_URL"

# Cloud Schedulerジョブを作成
gcloud scheduler jobs create http fx-news-collection-daily \
  --location=asia-northeast1 \
  --schedule="0 9 * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"query":"USD/JPY EUR/JPY 為替 最新ニュース","news_count":5,"skip_duplicate":true}' \
  --attempt-deadline=300s \
  --max-retry-attempts=3
```

#### 3. スケジューラーのテスト実行

```bash
# 手動でジョブを実行してテスト
gcloud scheduler jobs run fx-news-collection-daily \
  --location=asia-northeast1
```

#### 4. ログ確認

```bash
# Cloud Functionsのログを確認
gcloud functions logs read fx-news-collection \
  --region=asia-northeast1 \
  --gen2 \
  --limit=50
```

---

### Option 2: ローカルスクリプトを直接実行（開発用）

Cloud Schedulerを使わず、ローカルで手動実行する場合:

```bash
cd backend
source venv/bin/activate

# 環境変数の確認
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# スクリプト実行
python scripts/run_news_collection.py
```

---

## ⚙️ スケジュール設定

デフォルト設定:
- **頻度**: 毎日1回
- **実行時刻**: 9:00 JST (0:00 UTC)
- **タイムゾーン**: Asia/Tokyo

### スケジュールの変更

```bash
# スケジュールを更新（例: 毎日18:00に変更）
gcloud scheduler jobs update http fx-news-collection-daily \
  --location=asia-northeast1 \
  --schedule="0 18 * * *"

# 1日2回実行（9:00と18:00）
gcloud scheduler jobs update http fx-news-collection-daily \
  --location=asia-northeast1 \
  --schedule="0 9,18 * * *"
```

**cron形式:**
- `0 9 * * *` - 毎日9:00
- `0 9,18 * * *` - 毎日9:00と18:00
- `0 */6 * * *` - 6時間ごと
- `0 0 * * 1` - 毎週月曜日0:00

---

## 🔍 モニタリング・トラブルシューティング

### ログ確認

```bash
# Cloud Functionsのログ
gcloud functions logs read fx-news-collection \
  --region=asia-northeast1 \
  --gen2 \
  --limit=50

# Cloud Schedulerのログ
gcloud scheduler jobs describe fx-news-collection-daily \
  --location=asia-northeast1
```

### よくある問題

#### 1. 認証エラー

```
Error: Your default credentials were not found
```

**解決方法:**
- Cloud Functionsのデプロイ時に正しいサービスアカウントを指定
- サービスアカウントに必要な権限を付与

#### 2. モデルが見つからないエラー

```
404 NOT_FOUND: Publisher Model not found
```

**解決方法:**
- `backend/src/services/news_analyzer.py` のモデル名を確認
- 正しいモデル名: `gemini-2.5-flash` (not `gemini-2.5-flash-lite`)

#### 3. タイムアウト

```
Function execution took too long
```

**解決方法:**
- Cloud Functionsのタイムアウトを延長（最大540秒）
- `news_count` を減らす（デフォルト5件 → 3件）

---

## 💰 コスト管理

### 実行頻度とコストの目安

1日1回の実行:
- **Gemini API**: 約5件 × 30日 = 150件/月
- **Cloud Functions**: 30回/月（無料枠内）
- **Cloud Scheduler**: 30ジョブ/月（無料枠内）

**推奨:**
- 初期段階は1日1回から開始
- 必要に応じて頻度を調整

### コスト削減のヒント

1. **ニュース件数を調整**
   ```json
   {"news_count": 3}  // 5件 → 3件に削減
   ```

2. **重複スキップを有効化**
   ```json
   {"skip_duplicate": true}  // 常にtrue推奨
   ```

3. **実行頻度を最適化**
   - 市場が開いている時間帯のみ実行
   - 週末は実行しない

---

## 🔄 更新・削除

### Cloud Functionsの更新

```bash
cd deployment/cloud-scheduler

# コードを修正後、再デプロイ
gcloud functions deploy fx-news-collection \
  --gen2 \
  --runtime=python310 \
  --region=asia-northeast1 \
  --source=. \
  --entry-point=collect_fx_news \
  --trigger-http
```

### Cloud Schedulerの削除

```bash
# スケジューラージョブを削除
gcloud scheduler jobs delete fx-news-collection-daily \
  --location=asia-northeast1

# Cloud Functionsを削除
gcloud functions delete fx-news-collection \
  --region=asia-northeast1 \
  --gen2
```

---

## 📚 関連ドキュメント

- [Cloud Functions ドキュメント](https://cloud.google.com/functions/docs)
- [Cloud Scheduler ドキュメント](https://cloud.google.com/scheduler/docs)
- [Cron 形式ガイド](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)

---

## ✅ チェックリスト

デプロイ前の確認事項:

- [ ] GCP プロジェクトが作成済み
- [ ] Vertex AI API が有効化済み
- [ ] Cloud Functions API が有効化済み
- [ ] Cloud Scheduler API が有効化済み
- [ ] サービスアカウントが作成済み
- [ ] サービスアカウントに必要な権限が付与済み
- [ ] Firestore が有効化済み
- [ ] ローカルでスクリプトが正常に動作することを確認済み

---

**最終更新日**: 2026-01-10
