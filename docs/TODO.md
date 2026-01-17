# FX Insight Bot - TODO & 実装前チェックリスト

## 決定済み事項

### ✅ Firestore データベース設計
- **インデックス**: 初期段階では作成せず、必要に応じて追加
- **データ保持期間**: Firestore 3ヶ月、BigQuery 永久保存
- **構造**: サブコレクション不要、非正規化で設計
- **セキュリティ**: 管理者のみアクセス可能
- **詳細ドキュメント**: [FIRESTORE_DESIGN.md](design/FIRESTORE_DESIGN.md)
- **BigQueryエクスポート**: 1日1回(午前2時)

### ✅ バックエンドフレームワーク
- **採用**: FastAPI
- **理由**: 非同期対応、自動ドキュメント生成、型ヒント、開発経験あり

### ✅ 認証・セキュリティ
- **ダッシュボード**: 個人利用のみ（Firebase Authentication）
- **API認証**: Firebase Authentication（JWT）
- **公開予定**: なし（個人利用限定）

### ✅ ニュースソース
- **採用ソース**: Gemini Grounding with Google Search
- **収集方法**: Grounding機能によるリアルタイム検索
- **頻度**: 1回/日（9:00 JST）

### ✅ デプロイ戦略
- **バックエンド**: Cloud Run（FastAPI全体をデプロイ）
- **定期実行**: Cloud Scheduler → Cloud Run API エンドポイント
- **フロントエンド**: Firebase Hosting（予定）
- **理由**: シンプル、柔軟、無料枠が大きい

### ✅ X(Twitter)投稿の運用方針
- **初期フェーズ**: 完全手動（ドラフトのみ生成）
- **将来**: 承認フロー付き自動投稿に移行予定
- **投稿頻度**: 未定（手動運用のため）

### ✅ 開発環境・CI/CD
- **リポジトリ構成**: モノレポ（backend + frontend）
- **CI/CD**: GitHub Actions
- **バージョン管理**: Git + GitHub

### ✅ ルールエンジン
- **記述形式**: Pythonコード（シンプルなif-else）
- **将来**: ルールが増えたらYAML形式に移行検討
- **評価方式**: 条件分岐による判定

---

## 次に決定すべき事項（実装フェーズで決定）

### 1. LLMプロンプト設計（Phase 3で決定）
- [ ] AI要約・分類のプロンプトテンプレート作成
- [ ] センチメント分析の詳細基準
- [ ] プロンプトのバージョン管理方法

### 2. ニュース収集の詳細（Phase 2で決定）
- [x] 収集方法の決定（Grounding採用）
- [x] Gemini Grounding動作確認（成功）
- [x] Gemini Grounding検索クエリの最適化（完了）
- [x] レート制限(Rate Limit)への対応方針（指数バックオフ実装）
- [x] エラーハンドリング方針（リトライロジック実装）

---

## 次のアクション(優先順位順)

### Phase 0: 環境準備(最優先)
- [x] GCPプロジェクト作成
- [x] 必要なAPIの有効化
  - Firestore API
  - BigQuery API
  - Cloud Run API
  - Cloud Scheduler API
- [x] Firestore有効化とセキュリティルールデプロイ
- [x] Vertex AI API有効化
- [ ] X(Twitter) API キー取得
- [x] GMOコイン デモ口座開設

### Phase 1: バックエンド基盤構築
- [x] Pythonプロジェクトのセットアップ
- [x] FastAPI の基本構成
- [x] Firestore接続確認
- [x] 初期設定データ投入

### Phase 2: ニュース収集機能(Grounding) ✅ 完了
- [x] Gemini Grounding動作確認（完了）
- [x] テストスクリプト作成（完了）
- [x] Vertex AI (Gemini 2.5 Flash) 本実装
- [x] プロンプトテンプレート作成
- [x] JSON出力のパース・バリデーション
- [x] Firestoreへの保存機能
- [x] 検索クエリの最適化
- [x] エラーハンドリング・リトライロジック実装
- [x] FastAPIニュース収集エンドポイント実装
- [x] Cloud Run デプロイ準備（Dockerfile, .dockerignore）
- [x] Cloud Run デプロイ手順ドキュメント作成
- [x] ローカルテスト実行成功

### Phase 3: ルールエンジン実装 ✅ 完了
- [x] GMOコインクライアント実装（ローソク足データ取得）
- [x] テクニカル指標計算（MA, RSI, MACD）
- [x] ルールエンジン実装（ニュース+テクニカル統合判定）
- [x] トレードシグナル生成（buy/sell/hold + 信頼度）
- [x] Firestoreシグナル保存機能
- [x] テストスクリプト作成・実行成功

### Phase 4: 自動売買機能 ✅ 完了
- [x] GMOコイン プライベートAPI認証実装
- [x] 注文発注・キャンセル機能（place_order, cancel_order）
- [x] ポジション照会・決済機能（get_positions, close_position）
- [x] 売買ロジック実装（TradeExecutor）
- [x] リスク管理機能実装（RiskManager）
- [x] DRY-RUNモードテスト（7/7成功）
- [x] IFDOCO/IFD注文実装
- [x] GMOコインAPIキー取得
- [x] 実APIでの接続テスト（4/4成功）
- [x] FastAPIエンドポイント追加

### Phase 5: フロントエンド構築（表示専用ダッシュボード）

**設計ドキュメント**: [FRONTEND_SPEC.md](design/FRONTEND_SPEC.md)

#### Phase 5.1: 環境構築・最小構成 ✅ 完了
- [x] Vite + React + TypeScript プロジェクト作成
- [x] Tailwind CSS セットアップ
- [x] **シンプルな1ページダッシュボード作成**
  - 口座残高表示（APIから取得）
  - ポジション一覧表示
  - ヘルスチェック表示
- [x] バックエンドAPI連携確認（localhost:8000）

#### Phase 5.2: 認証・ルーティング
- [ ] Firebase Authentication セットアップ
- [ ] Googleログイン実装
- [ ] React Router v6 ルーティング設定
- [ ] 認証ガード（ProtectedRoute）

#### Phase 5.3: ダッシュボード拡張
- [ ] shadcn/ui コンポーネント導入
- [ ] React Query（TanStack Query）導入
- [ ] 口座サマリーカード
- [ ] リスク状況表示
- [ ] 自動更新機能（ポーリング）

#### Phase 5.4: 追加画面
- [ ] ポジション詳細画面
- [ ] ニュース一覧画面（Firestore連携）
- [ ] シグナル履歴画面
- [ ] 設定画面（表示設定のみ）

#### Phase 5.5: 仕上げ
- [ ] ダークモード対応
- [ ] エラーハンドリング・ローディング表示
- [ ] Firebase Hosting デプロイ

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

- [ドキュメント一覧](./README.md)
- [要件定義書](design/requirements.md)
- [Firestore設計書](design/FIRESTORE_DESIGN.md)
- [開発ガイド](guides/DEVELOPMENT_GUIDE.md)
- [進捗記録](progress/)

---

---

## 変更履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-01-17 | Phase 5設計完了、フロントエンド画面仕様書作成 |
| 2026-01-17 | Phase 4完了（プライベートAPI、TradeExecutor、RiskManager、FastAPIエンドポイント） |
| 2026-01-12 | Phase 3完了、ルールエンジン実装完了（テクニカル指標+ニュース分析統合） |
| 2026-01-11 | Cloud Functions → Cloud Run 移行決定、デプロイ準備完了 |
| 2026-01-10 | Phase 2完了、エラーハンドリング・リトライロジック実装完了 |
| 2026-01-03 | Gemini 3 Flash採用、Grounding機能追加、Phase 2.1/2.2追加 |
| 2025-12-31 | Phase 0-1完了、ドキュメント整理、リンク修正 |
| 2025-12-29 | 未確定事項をすべて決定、決定済み事項セクションに追加 |
| 2025-01-13 | 初版作成 |

**最終更新日**: 2026-01-17
