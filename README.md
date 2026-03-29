# FX Compass

AI駆動のニュース分析とテクニカル指標を組み合わせたFX自動売買システム

## 🚀 概要

本システムは、金融ニュースをAI（Vertex AI - Gemini 1.5 Flash）で分析し、従来のテクニカル指標と組み合わせて自動的にFX取引を実行するツールです。リスク管理を重視し、長期的な安定運用を目指します。

### 主な特徴

- 📰 **AIニュース分析**: Vertex AI (Gemini 1.5 Flash) によるセンチメント分析と影響度評価
- 📊 **ハイブリッド戦略**: ニュース分析 + テクニカル指標の組み合わせ
- 🛡️ **リスク管理**: 厳格な損失制限とポジションサイジング
- 📈 **可視化ダッシュボード**: リアルタイムでの取引状況確認
- 🐦 **自動レポート**: X（Twitter）への分析結果自動投稿
- 🔄 **バックテスト**: 過去データによる戦略検証

## 📋 要件

### システム要件
- Python 3.10以上
- Node.js 18以上
- Google Cloud Platform アカウント
- GMOコイン アカウント（デモ口座可）

### API要件
- GMOコイン FX API アクセス（WebSocket + REST）
- Google Cloud Platform (Vertex AI 有効化)
- X Developer アカウント（オプション）

## 🛠️ 技術スタック

### バックエンド
- **Python** - メイン処理言語
- **FastAPI** - REST API サーバー
- **Backtrader** - バックテストフレームワーク
- **pandas/numpy** - データ処理

### フロントエンド  
- **React** - UIフレームワーク
- **TypeScript** - 型安全な開発
- **Recharts** - データ可視化

### インフラ
- **Google Cloud Firestore** - リアルタイムデータ
- **Google Cloud BigQuery** - 履歴データ分析
- **Cloud Functions** - 定期実行処理
- **Cloud Run** - Webアプリケーションホスティング

## 🚦 クイックスタート

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/fx-auto-trading.git
cd fx-auto-trading
```

### 2. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集して必要なAPIキーを設定
```

必要な環境変数:
```env
# GMOコイン API
GMO_API_KEY=your_gmo_api_key
GMO_SECRET_KEY=your_gmo_secret_key
GMO_ENVIRONMENT=demo  # or production

# Google Cloud
GCP_PROJECT_ID=your_project_id
GCP_SERVICE_ACCOUNT_KEY=path/to/service_account.json
VERTEX_AI_LOCATION=asia-northeast1

# X API (Optional)
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
```

### 3. 依存関係のインストール

#### バックエンド
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### フロントエンド
```bash
cd frontend
npm install
```

### 4. 設定ファイルの編集
```bash
# config/config.jsonを編集して取引パラメータを設定
cp config/config.example.json config/config.json
```

### 5. 開発サーバーの起動

#### バックエンド
```bash
cd backend
uvicorn main:app --reload --port 8000
```

#### フロントエンド
```bash
cd frontend
npm start
```

## 📁 プロジェクト構成

```
fx-auto-trading/
├── backend/
│   ├── api/                 # FastAPI エンドポイント
│   ├── core/                # コアビジネスロジック
│   │   ├── news_collector.py
│   │   ├── ai_analyzer.py
│   │   ├── trading_engine.py
│   │   └── risk_manager.py
│   ├── strategies/          # 取引戦略
│   ├── indicators/          # テクニカル指標
│   ├── models/              # データモデル
│   ├── services/            # 外部サービス連携
│   ├── utils/               # ユーティリティ
│   └── tests/               # テストコード
├── frontend/
│   ├── src/
│   │   ├── components/      # Reactコンポーネント
│   │   ├── pages/           # ページコンポーネント
│   │   ├── hooks/           # カスタムフック
│   │   ├── services/        # API通信
│   │   └── utils/           # ユーティリティ
│   └── public/
├── config/
│   ├── config.json          # 取引設定
│   └── indicators.json      # インジケーター設定
├── scripts/
│   ├── backtest.py          # バックテスト実行
│   ├── deploy.sh            # デプロイスクリプト
│   └── setup_gcp.sh         # GCP初期設定
├── docs/
│   ├── requirements.md      # 要件定義書
│   ├── api.md               # API仕様書
│   └── architecture.md      # アーキテクチャ設計
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## 🔧 設定

### 取引設定 (config/config.json)
```json
{
  "trading": {
    "pairs": ["USD_JPY", "EUR_USD"],
    "max_positions": 2,
    "position_size": 0.002
  },
  "risk_management": {
    "max_loss_per_trade": 1000,
    "stop_loss_pips": 20,
    "take_profit_pips": 40,
    "max_drawdown": 0.1
  },
  "news_analysis": {
    "fetch_interval_hours": 12,
    "sentiment_threshold": 1.5,
    "max_news_age_hours": 24
  }
}
```

## 📊 バックテスト

過去データで戦略を検証:
```bash
python scripts/backtest.py \
  --strategy hybrid \
  --start-date 2020-01-01 \
  --end-date 2024-01-01 \
  --initial-capital 500000
```

## 🚀 デプロイ

### Google Cloud Platform（2サービス構成）

**Service A（読み取り専用 / Firebase Hosting 経由）:**
```bash
GCP_PROJECT_ID=fx-insight-bot-prod gcloud run deploy fx-insight-bot \
  --source backend/ \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --allow-unauthenticated \
  --set-secrets "GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --set-env-vars "ENVIRONMENT=production,GCP_PROJECT_ID=fx-insight-bot-prod,FIRESTORE_DATABASE_ID=fx-insight-bot-db"
```

**Service B（取引実行専用 / Cloud Scheduler のみ）:**
```bash
GCP_PROJECT_ID=fx-insight-bot-prod gcloud run deploy fx-insight-bot-exec \
  --source backend/ \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --no-allow-unauthenticated \
  --set-secrets "GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --set-env-vars "ENVIRONMENT=production,GCP_PROJECT_ID=fx-insight-bot-prod,FIRESTORE_DATABASE_ID=fx-insight-bot-db" \
  --memory 512Mi \
  --concurrency 1 \
  --max-instances 2 \
  --timeout 300
```

> **注意**: `GCP_PROJECT_ID` をシェル変数かつ `--set-env-vars` の両方に指定する（未設定だと `RESOURCE_PROJECT_INVALID` エラー）。

**フロントエンド（Firebase Hosting）:**
```bash
cd frontend && npm run build && firebase deploy --only hosting
```

## 📖 ドキュメント

- [要件定義書](docs/requirements.md) - 詳細な機能要件と非機能要件
- [API仕様書](docs/api.md) - REST APIエンドポイントの仕様
- [アーキテクチャ設計](docs/architecture.md) - システム構成と設計思想

## ⚠️ 注意事項

### リスク警告
- **本システムは投資の参考ツールです。投資は自己責任で行ってください**
- 実際の資金を投入する前に、必ずデモ口座で十分なテストを行ってください
- 過去のパフォーマンスは将来の結果を保証するものではありません

### 法的注意
- 本システムは投資助言業に該当しない範囲で運用してください
- X（Twitter）への投稿は情報提供のみとし、投資推奨は行いません

## 🧪 テスト

```bash
# ユニットテスト
cd backend
pytest tests/

# 統合テスト
pytest tests/integration/

# カバレッジレポート
pytest --cov=core tests/
```

## 📈 パフォーマンス目標

- **年間収益率**: プラス収支維持
- **最大ドローダウン**: 10%以内
- **勝率**: 55%以上
- **リスクリワード比**: 1:2以上

## 🤝 コントリビューション

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください

## 👨‍💻 作者

細川 - Freelance Frontend Engineer

## 🙏 謝辞

- [GMOコイン](https://coin.z.com/jp/) - FX取引API
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai) - Gemini 1.5 Flash
- [Backtrader](https://www.backtrader.com) - バックテストフレームワーク

## 📞 サポート

問題が発生した場合は、[Issues](https://github.com/yourusername/fx-auto-trading/issues)でお知らせください。

---

**免責事項**: 本ソフトウェアは「現状有姿」で提供され、いかなる保証も行いません。投資に関する決定は自己責任で行ってください。