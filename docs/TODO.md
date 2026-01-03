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
- **頻度**: 2回/日

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
- [ ] Gemini Grounding検索クエリの最適化
- [ ] レート制限(Rate Limit)への対応方針
- [ ] エラーハンドリング方針

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

### Phase 2: ニュース収集機能(Grounding)
- [x] Gemini Grounding動作確認（完了）
- [x] テストスクリプト作成（完了）
- [ ] Vertex AI (Gemini 3 Flash) 本実装
- [ ] プロンプトテンプレート作成
- [ ] JSON出力のパース・バリデーション
- [ ] Firestoreへの保存機能
- [ ] 検索クエリの最適化
- [ ] 定期実行スクリプト作成

### Phase 4: 自動売買機能
- [ ] GMOコイン API連携実装
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
| 2026-01-03 | Gemini 3 Flash採用、Grounding機能追加、Phase 2.1/2.2追加 |
| 2025-12-31 | Phase 0-1完了、ドキュメント整理、リンク修正 |
| 2025-12-29 | 未確定事項をすべて決定、決定済み事項セクションに追加 |
| 2025-01-13 | 初版作成 |

**最終更新日**: 2026-01-03
