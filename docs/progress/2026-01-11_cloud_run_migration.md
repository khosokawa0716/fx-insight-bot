# Cloud Run デプロイ方式への移行完了レポート

**日付**: 2026-01-11
**フェーズ**: Phase 2 - デプロイ戦略変更
**ステータス**: ✅ 完了

---

## 概要

当初のCloud Functions方式から、より柔軟でシンプルなCloud Run方式に変更しました。バックエンド全体を1つのサービスとしてデプロイし、Cloud SchedulerからAPIエンドポイントを呼び出す構成に変更しました。

---

## 変更の背景

### 当初の設計（Cloud Functions方式）の課題

**問題点:**
1. `deployment/cloud-scheduler/main.py` に `backend/src` が含まれていない
2. コードの重複管理が必要
3. デプロイが2箇所（Cloud Functions + 将来のCloud Run）

**発覚した経緯:**
- デプロイ手順書を確認中に `--source=.` が `deployment/cloud-scheduler/` のみを対象としていることが判明
- `from src.services.news_pipeline import run_news_collection` が動作しない設計だった

### 新しい設計（Cloud Run方式）の利点

1. **シンプル**: backend/ 全体を1箇所で管理
2. **柔軟**: FastAPIの全機能が使える
3. **簡単**: デプロイコマンド1つで完結
4. **拡張可能**: 後で他のAPIエンドポイントを追加しやすい
5. **コスト効率**: 無料枠が大きい（月200万リクエスト）

---

## 実施内容

### 1. Cloud Functions関連ファイルの削除

削除したファイル:
- `deployment/cloud-scheduler/main.py`
- `deployment/cloud-scheduler/requirements.txt`
- `deployment/cloud-scheduler/scheduler.yaml`
- `deployment/cloud-scheduler/README.md`

### 2. Cloud Run デプロイ準備

#### 新規作成ファイル:

**Dockerfile** ([backend/Dockerfile](../../backend/Dockerfile))
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY scripts/ ./scripts/
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT}
```

**.dockerignore** ([backend/.dockerignore](../../backend/.dockerignore))
- Python関連ファイル（__pycache__, *.pyc）
- 仮想環境（venv/）
- テスト・サンプルコード（examples/, tests/）
- 認証情報（credentials/）

**デプロイ手順書** ([deployment/cloud-run/README.md](../../deployment/cloud-run/README.md))
- gcloud コマンドでのデプロイ手順
- Cloud Scheduler連携設定
- モニタリング・トラブルシューティング
- コスト管理

### 3. FastAPI エンドポイント追加

[backend/src/main.py](../../backend/src/main.py) に以下を追加:

**新規エンドポイント:**
```python
POST /api/v1/news/collect
```

**リクエストモデル:**
```python
class NewsCollectionRequest(BaseModel):
    query: Optional[str] = "USD/JPY EUR/JPY 為替 最新ニュース"
    news_count: Optional[int] = 5
    skip_duplicate: Optional[bool] = True
```

**レスポンスモデル:**
```python
class NewsCollectionResponse(BaseModel):
    status: str
    message: str
    stats: dict
```

**実装:**
- Cloud Schedulerからの空リクエストに対応（デフォルトパラメータ使用）
- エラーハンドリング（HTTPException）
- ログ出力

### 4. TODO.md の更新

**追加した決定事項:**
```markdown
### ✅ デプロイ戦略
- **バックエンド**: Cloud Run（FastAPI全体をデプロイ）
- **定期実行**: Cloud Scheduler → Cloud Run API エンドポイント
- **フロントエンド**: Firebase Hosting（予定）
- **理由**: シンプル、柔軟、無料枠が大きい
```

---

## デプロイアーキテクチャ

### 新しい構成

```
┌─────────────────────────────────────────┐
│        Cloud Scheduler                  │
│     （1日1回、9:00 JST）                │
└──────────────┬──────────────────────────┘
               │ POST /api/v1/news/collect
               ↓
┌─────────────────────────────────────────┐
│        Cloud Run                        │
│  fx-insight-bot-api                     │
│                                         │
│  FastAPI Application                    │
│  ├── GET  /                            │
│  ├── GET  /health                      │
│  ├── GET  /test/firestore              │
│  └── POST /api/v1/news/collect ←      │
│                                         │
│  backend/src/ 全体                      │
│  ├── services/                         │
│  │   ├── news_analyzer.py              │
│  │   ├── news_pipeline.py              │
│  │   └── news_storage.py               │
│  └── ...                                │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│        Firestore                        │
│  news コレクション                       │
└─────────────────────────────────────────┘
```

---

## デプロイ方法

### 簡単デプロイ（推奨）

```bash
cd backend

gcloud run deploy fx-insight-bot-api \
  --source=. \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=${SERVICE_ACCOUNT} \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},FIRESTORE_DATABASE_ID=fx-insight-bot-db" \
  --memory=512Mi \
  --timeout=300
```

**これだけで完了！**

### Cloud Scheduler 設定

```bash
SERVICE_URL=$(gcloud run services describe fx-insight-bot-api \
  --region=asia-northeast1 \
  --format='value(status.url)')

gcloud scheduler jobs create http fx-news-collection-daily \
  --location=asia-northeast1 \
  --schedule="0 9 * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="${SERVICE_URL}/api/v1/news/collect" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{}' \
  --attempt-deadline=300s
```

---

## コスト試算

### 月間コスト（1日1回実行）

**Cloud Run:**
- リクエスト数: 30回/月
- 実行時間: 約16秒/回
- メモリ: 512MB
- CPU: 1 vCPU
- **コスト**: $0（無料枠内）

**Cloud Scheduler:**
- ジョブ数: 1個
- 実行回数: 30回/月
- **コスト**: $0（無料枠内）

**合計月間コスト: $0**

---

## 今後の拡張性

### 追加しやすいエンドポイント

```python
# ニュース一覧取得
@app.get("/api/v1/news")
async def get_news_list(limit: int = 10):
    pass

# ニュース詳細取得
@app.get("/api/v1/news/{news_id}")
async def get_news_detail(news_id: str):
    pass

# トレードシグナル取得
@app.get("/api/v1/signals")
async def get_trade_signals():
    pass
```

すべて同じCloud Runサービス内で実装可能。

---

## Cloud Functions への切り替え可能性

後でコスト最適化が必要になった場合、定期実行部分だけCloud Functionsに分離することも可能:

```python
# Cloud Functions エントリポイント
def collect_fx_news(request):
    from src.services.news_pipeline import run_news_collection
    stats = run_news_collection()
    return {"status": "success", "stats": stats}
```

**切り替え時間**: 約2-3時間

---

## まとめ

Cloud Run方式への移行により、以下を実現しました:

**✅ 達成事項:**
1. シンプルなアーキテクチャ（1つのコードベース）
2. 簡単なデプロイ（gcloud コマンド1つ）
3. 柔軟な拡張性（FastAPI全機能）
4. コスト効率（無料枠内で運用）
5. 後での最適化余地（Cloud Functions分離可能）

**📝 デプロイ準備完了:**
- Dockerfile作成
- .dockerignore作成
- FastAPIエンドポイント実装
- デプロイ手順書作成

**🎯 次のステップ:**
- Phase 3: ルールエンジン実装
- Phase 5: フロントエンド構築
- 完成後にCloud Runデプロイ

---

**作成者**: Claude Sonnet 4.5
**最終更新**: 2026-01-11
