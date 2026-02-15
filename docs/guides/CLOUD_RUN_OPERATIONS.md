# Cloud Run 運用ガイド

**対象サービス**: fx-insight-bot
**URL**: https://fx-insight-bot-755346299346.asia-northeast1.run.app
**リージョン**: asia-northeast1

---

## よく使うコマンド

### サービス状態確認

```bash
# ヘルスチェック
curl https://fx-insight-bot-755346299346.asia-northeast1.run.app/health

# サービス詳細
gcloud run services describe fx-insight-bot

# リビジョン一覧
gcloud run revisions list --service=fx-insight-bot
```

### ログ確認

```bash
# 直近のログ（30件）
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fx-insight-bot" --limit 30 --format "value(textPayload)"

# エラーログのみ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fx-insight-bot AND severity>=ERROR" --limit 20 --format "value(textPayload)"

# 特定時間以降のログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fx-insight-bot AND timestamp>=\"2026-02-15T00:00:00Z\"" --limit 50
```

### デプロイ

```bash
# 通常デプロイ（ソースからビルド）
gcloud run deploy fx-insight-bot --source backend/ --set-env-vars ENVIRONMENT=production --allow-unauthenticated

# 環境変数の更新（再ビルド不要）
gcloud run services update fx-insight-bot --set-env-vars KEY=VALUE

# シークレットの更新
echo -n "NEW_VALUE" | gcloud secrets versions add gmo-api-key --data-file=-
# ※ シークレットは :latest 参照のため、新バージョン追加で自動反映（次回起動時）
```

---

## Cloud Scheduler 管理

### ジョブ一覧

```bash
gcloud scheduler jobs list --location=asia-northeast1
```

### 取引の一時停止 / 再開

```bash
# 停止
gcloud scheduler jobs pause fx-trade-execute --location=asia-northeast1

# 再開
gcloud scheduler jobs resume fx-trade-execute --location=asia-northeast1
```

### ニュース収集の一時停止 / 再開

```bash
# 停止
gcloud scheduler jobs pause fx-news-collect --location=asia-northeast1

# 再開
gcloud scheduler jobs resume fx-news-collect --location=asia-northeast1
```

### 手動実行（テスト用）

```bash
# ニュース収集を即時実行
gcloud scheduler jobs run fx-news-collect --location=asia-northeast1

# 取引実行を即時実行（本番注文が走るので注意）
gcloud scheduler jobs run fx-trade-execute --location=asia-northeast1
```

### スケジュール変更

```bash
# 取引実行の時間を変更（例: 10:00/22:00 に変更）
gcloud scheduler jobs update http fx-trade-execute \
  --location=asia-northeast1 \
  --schedule="0 10,22 * * 1-5"

# ニュース収集の時間を変更
gcloud scheduler jobs update http fx-news-collect \
  --location=asia-northeast1 \
  --schedule="0 8,20 * * *"
```

---

## Secret Manager 管理

```bash
# シークレット一覧
gcloud secrets list

# シークレットの値を確認
gcloud secrets versions access latest --secret=gmo-api-key

# シークレットの更新（新バージョン追加）
echo -n "NEW_API_KEY" | gcloud secrets versions add gmo-api-key --data-file=-

# 古いバージョンを無効化
gcloud secrets versions disable VERSION_ID --secret=gmo-api-key
```

---

## API エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | ルート（ステータス確認） |
| GET | `/health` | ヘルスチェック |
| GET | `/test/firestore` | Firestore接続テスト |
| POST | `/api/v1/news/collect` | ニュース収集 |
| GET | `/api/v1/news` | ニュース一覧 |
| GET | `/api/v1/signals` | シグナル一覧 |
| POST | `/api/v1/trade/execute` | 取引実行（v2.0） |
| GET | `/api/v1/trade/account` | 口座情報 |
| GET | `/api/v1/trade/positions` | ポジション一覧 |
| GET | `/api/v1/trade/orders` | 注文一覧 |
| GET | `/api/v1/trade/risk/summary` | リスクサマリー |
| GET | `/api/v1/trade/monthly-summary` | 月間損益（研究用） |

### curl での手動実行例

```bash
BASE_URL="https://fx-insight-bot-755346299346.asia-northeast1.run.app"

# ニュース収集
curl -X POST "$BASE_URL/api/v1/news/collect" \
  -H "Content-Type: application/json" \
  -d '{}'

# 取引実行（DRY-RUN）
curl -X POST "$BASE_URL/api/v1/trade/execute" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'

# 取引実行（本番）
curl -X POST "$BASE_URL/api/v1/trade/execute" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'

# 口座情報
curl "$BASE_URL/api/v1/trade/account"

# ポジション確認
curl "$BASE_URL/api/v1/trade/positions"

# 月間サマリー
curl "$BASE_URL/api/v1/trade/monthly-summary"
```

---

## トラブルシューティング

### コンテナが起動しない

```bash
# ログで原因を確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fx-insight-bot" --limit 30 --format "value(textPayload)"
```

よくある原因:
- **ImportError**: `requirements.txt` にパッケージが不足
- **ポート不一致**: Dockerfileの `PORT` と `CMD` のポートが一致しているか確認
- **環境変数不足**: 必要な環境変数が設定されているか確認

### 前のリビジョンに戻す

```bash
# リビジョン一覧を確認
gcloud run revisions list --service=fx-insight-bot

# 特定のリビジョンにトラフィックを切り替え
gcloud run services update-traffic fx-insight-bot --to-revisions=REVISION_NAME=100
```

### サービスの完全削除

```bash
# ※ 注意: 全リビジョンが削除される
gcloud run services delete fx-insight-bot
```

---

## 現在のスケジュール

| ジョブ名 | スケジュール | エンドポイント | dry_run |
|---------|------------|--------------|---------|
| fx-news-collect | 毎日 8:00/20:00 JST | POST /api/v1/news/collect | - |
| fx-trade-execute | 月〜金 9:00/21:00 JST | POST /api/v1/trade/execute | false |
