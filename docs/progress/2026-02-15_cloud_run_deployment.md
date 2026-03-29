# Cloud Run デプロイ & Cloud Scheduler 設定 完了レポート

**日付**: 2026-02-15
**フェーズ**: v2.0 デプロイ
**ステータス**: 完了

---

## 概要

v2.0（AIロット決定機能）の実装完了を受け、Cloud Runへの本番デプロイおよびCloud Schedulerによる定期実行を設定しました。

---

## 実施内容

### 1. gcloud CLI セットアップ

```bash
# インストール
brew install --cask google-cloud-sdk

# 認証
gcloud auth login

# プロジェクト・リージョン設定
gcloud config set project fx-insight-bot-prod
gcloud config set run/region asia-northeast1
```

### 2. GCP API 有効化

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
```

### 3. requirements.txt 修正

デプロイ時に `from google import genai` の ImportError が発生。
`google-genai` パッケージが不足していたため追加。

```diff
 # Google Cloud Platform
 google-cloud-firestore==2.14.0
 google-cloud-bigquery==3.14.1
 google-cloud-aiplatform==1.39.0
+google-genai>=1.0.0
```

### 4. Cloud Run デプロイ

> **⚠️ 注意（2026-02-27 更新）**: 現在は2サービス構成に移行済み。最新のデプロイコマンドは `README.md` または `docs/progress/2026-02-27_service_split_auth.md` を参照。

```bash
# 旧コマンド（1サービス構成 / 現在は非推奨）
gcloud run deploy fx-insight-bot \
  --source backend/ \
  --set-env-vars ENVIRONMENT=production \
  --allow-unauthenticated
```

- **サービスURL**: https://fx-insight-bot-755346299346.asia-northeast1.run.app
- **リージョン**: asia-northeast1
- **認証**: 未認証アクセス許可（`--allow-unauthenticated`）

### 5. Secret Manager 設定（GMO APIキー）

```bash
# シークレット作成
echo -n "YOUR_API_KEY" | gcloud secrets create gmo-api-key --data-file=-
echo -n "YOUR_API_SECRET" | gcloud secrets create gmo-api-secret --data-file=-

# サービスアカウントに権限付与
gcloud projects add-iam-policy-binding fx-insight-bot-prod \
  --member="serviceAccount:755346299346-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Run にシークレットをマッピング
gcloud run services update fx-insight-bot \
  --update-secrets=GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest
```

### 6. Cloud Scheduler 設定

#### ニュース収集（毎日 8:00 / 20:00 JST）

```bash
gcloud scheduler jobs create http fx-news-collect \
  --location=asia-northeast1 \
  --schedule="0 8,20 * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="https://fx-insight-bot-755346299346.asia-northeast1.run.app/api/v1/news/collect" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body="{}"
```

#### 取引実行（月〜金 9:00 / 21:00 JST、本番注文）

```bash
gcloud scheduler jobs create http fx-trade-execute \
  --location=asia-northeast1 \
  --schedule="0 9,21 * * 1-5" \
  --time-zone="Asia/Tokyo" \
  --uri="https://fx-insight-bot-755346299346.asia-northeast1.run.app/api/v1/trade/execute" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body="{\"dry_run\":false}"
```

---

## デプロイアーキテクチャ

```
┌─────────────────────────────────────────────┐
│           Cloud Scheduler                   │
│                                             │
│  fx-news-collect:   毎日 8:00/20:00 JST     │
│  fx-trade-execute:  月〜金 9:00/21:00 JST    │
└──────────┬───────────────┬──────────────────┘
           │               │
           │ POST          │ POST
           │ /news/collect │ /trade/execute
           ↓               ↓
┌─────────────────────────────────────────────┐
│           Cloud Run                         │
│  fx-insight-bot                             │
│                                             │
│  FastAPI Application (PORT=8080)            │
│  ├── GET  /health                           │
│  ├── POST /api/v1/news/collect              │
│  ├── POST /api/v1/trade/execute             │
│  ├── GET  /api/v1/trade/monthly-summary     │
│  └── ...                                    │
│                                             │
│  環境変数:                                   │
│  ├── ENVIRONMENT=production                 │
│  ├── GMO_API_KEY    (Secret Manager)        │
│  └── GMO_API_SECRET (Secret Manager)        │
└──────────┬───────────────┬──────────────────┘
           │               │
           ↓               ↓
┌──────────────┐  ┌────────────────┐
│  Firestore   │  │  GMO Coin API  │
│  fx-insight  │  │  (FX取引)      │
│  -bot-db     │  │                │
└──────────────┘  └────────────────┘
```

---

## 発生した問題と解決

### 問題1: コンテナ起動失敗（ImportError）

**エラー**:
```
ImportError: cannot import name 'genai' from 'google' (unknown location)
```

**原因**: `news_analyzer.py` が `from google import genai` をインポートしているが、`requirements.txt` に `google-genai` パッケージが未記載だった。

**解決**: `requirements.txt` に `google-genai>=1.0.0` を追加して再デプロイ。

### 問題2: Secret Manager アクセス権限エラー

**エラー**:
```
Permission denied on secret: projects/.../secrets/gmo-api-key/versions/latest
for Revision service account 755346299346-compute@developer.gserviceaccount.com
```

**原因**: Cloud Runのデフォルトサービスアカウントに Secret Manager へのアクセス権限がなかった。

**解決**: `roles/secretmanager.secretAccessor` ロールを付与。

---

## 注意事項

1. **取引は `dry_run: false`**: Cloud Schedulerからの取引実行は本番注文。一時停止するには:
   ```bash
   gcloud scheduler jobs pause fx-trade-execute --location=asia-northeast1
   ```
   再開:
   ```bash
   gcloud scheduler jobs resume fx-trade-execute --location=asia-northeast1
   ```

2. **GMO取引時間**: 月曜7:00〜土曜6:00（JST）。土日のスケジュールは `1-5`（月〜金）で除外済み。

3. **コスト**: Cloud Run無料枠（月200万リクエスト、360,000 vCPU秒）内で収まる見込み。

4. **未認証アクセス**: `--allow-unauthenticated` で公開中。将来的にはCloud Scheduler用のOIDC認証を検討。

---

## 今後のタスク

- [ ] Real APIテスト（Task 9）: 平日に手動で `/trade/execute` を実行して動作確認
- [ ] Cloud Monitoring / アラート設定
- [ ] CORS設定を本番ドメインに制限
- [ ] CI/CD パイプライン構築（GitHub Actions）

---

**作成者**: Claude Opus 4.6
**最終更新**: 2026-02-15
