# FX Insight Bot - TODO & 実装前チェックリスト

## 決定済み事項

### ✅ Firestore データベース設計
- **インデックス**: 初期段階では作成せず、必要に応じて追加
- **データ保持期間**: Firestore 3ヶ月、BigQuery 永久保存
- **構造**: サブコレクション不要、非正規化で設計
- **セキュリティ**: 管理者のみアクセス可能
- **詳細ドキュメント**: [FIRESTORE_DESIGN.md](./FIRESTORE_DESIGN.md)
- **BigQueryエクスポート**: 1日1回(午前2時)

---

## 次に決定すべき事項

### 1. バックエンドフレームワークの選定
- [ ] **FastAPI vs Flask どちらを採用するか?**
  - FastAPI: 非同期対応、自動ドキュメント生成、型ヒント必須、モダン
  - Flask: シンプル、軽量、実績豊富
  - **推奨**: FastAPI

### 2. 認証・セキュリティ
- [ ] ダッシュボードへのアクセス制御
  - 個人利用のみ(Firebase Authentication)
  - 公開ダッシュボード(認証なし)
- [ ] API エンドポイントの認証方式
  - API Key方式
  - JWT方式
  - GCP IAMベース

### 3. ニュースソースの具体化
- [ ] **どのRSSフィードを使用するか?**
  - Bloomberg RSS
  - Reuters RSS
  - その他金融ニュースサイト
- [ ] スクレイピング対象サイトの利用規約確認
- [ ] レート制限(Rate Limit)への対応方針

### 4. LLMプロンプト設計
- [ ] AI要約・分類のプロンプトテンプレート作成
- [ ] センチメント分析の詳細基準
- [ ] プロンプトのバージョン管理方法

### 5. ルールエンジンの詳細設計
- [ ] ルール記述フォーマットの決定
  - YAML形式
  - JSON形式
  - Pythonコード(DSL)
- [ ] ルール評価エンジンの実装方式

### 6. X(Twitter)投稿の運用方針
- [ ] 初期フェーズの投稿方式
  - 完全手動(ドラフトのみ生成)
  - 承認フロー付き自動投稿
  - 完全自動投稿
- [ ] 投稿頻度の制限

### 7. 開発環境・CI/CD
- [ ] リポジトリ構成
  - モノレポ(backend + frontend)
  - 分離リポジトリ
- [ ] CI/CDパイプライン
  - GitHub Actions
  - Cloud Build

---

## 次のアクション(優先順位順)

### Phase 0: 環境準備(最優先)
- [ ] GCPプロジェクト作成
- [ ] 必要なAPIの有効化
  - Firestore API
  - BigQuery API
  - Cloud Run API
  - Cloud Scheduler API
- [ ] Firestore有効化とセキュリティルールデプロイ
- [ ] Vertex AI API有効化
- [ ] X(Twitter) API キー取得
- [ ] GMOコイン デモ口座開設

### Phase 1: バックエンド基盤構築
- [ ] Pythonプロジェクトのセットアップ
- [ ] FastAPI の基本構成
- [ ] Firestore接続確認
- [ ] 初期設定データ投入

### Phase 2: ニュース収集機能(MVP)
- [ ] RSS取得機能実装
- [ ] Firestoreへの保存機能
- [ ] 定期実行スクリプト作成

### Phase 3: AI要約・分類機能
- [ ] OpenAI API連携実装
- [ ] プロンプトテンプレート作成
- [ ] JSON出力のパース・バリデーション

### Phase 4: 自動売買機能
- [ ] OANDA API連携実装
- [ ] 売買ロジック実装
- [ ] リスク管理機能実装

### Phase 5: フロントエンド構築
- [ ] React + TypeScript プロジェクト作成
- [ ] ダッシュボードUI実装
- [ ] API連携実装

### Phase 6: BigQuery連携
- [ ] Firestore → BigQuery エクスポート設定
- [ ] 分析クエリ作成

### Phase 7: X投稿機能
- [ ] X API連携実装
- [ ] 投稿テキスト生成
- [ ] 手動承認フロー実装

### Phase 8: デプロイ・運用
- [ ] Dockerファイル作成
- [ ] Cloud Runデプロイ設定
- [ ] 監視・アラート設定

---

## 参考ドキュメント

- [要件定義書](./requirements.md)
- [Firestore設計書](./FIRESTORE_DESIGN.md)
- [開発ガイド](./DEVELOPMENT_GUIDE.md)

---

**最終更新日**: 2025-01-13
