# FX Insight Bot - ドキュメント

このディレクトリには、FX Insight Botの設計書、ガイド、進捗記録が含まれています。

---

## 📁 ディレクトリ構成

```
docs/
├── README.md              # このファイル
├── TODO.md                # 実装チェックリスト
├── design/                # 設計ドキュメント
│   ├── requirements.md            # 要件定義書
│   ├── FIRESTORE_DESIGN.md        # Firestore設計書
│   ├── AI_COMPARISON.md           # AI選定比較（Vertex AI vs OpenAI）
│   └── COST_ESTIMATE.md           # コスト見積
├── guides/                # 開発ガイド
│   └── DEVELOPMENT_GUIDE.md       # 開発ガイド・Tips
└── progress/              # 進捗記録
    └── 2025-12-31_phase0-1_completion.md  # Phase 0-1完了レポート
```

---

## 📚 ドキュメント一覧

### 設計ドキュメント（design/）

| ファイル | 説明 | 更新日 |
|---------|------|--------|
| [requirements.md](design/requirements.md) | プロジェクト全体の要件定義書 | 2025-12-28 |
| [FIRESTORE_DESIGN.md](design/FIRESTORE_DESIGN.md) | Firestoreデータベース設計書 | 2025-01-13 |
| [AI_COMPARISON.md](design/AI_COMPARISON.md) | Vertex AI vs OpenAI APIの比較 | 2025-12-28 |
| [COST_ESTIMATE.md](design/COST_ESTIMATE.md) | 月間運用コスト見積 | 2025-12-28 |

### 開発ガイド（guides/）

| ファイル | 説明 | 更新日 |
|---------|------|--------|
| [DEVELOPMENT_GUIDE.md](guides/DEVELOPMENT_GUIDE.md) | 開発のコツ、Tips、FAQ | 2025-12-12 |

### 進捗記録（progress/）

| ファイル | 説明 | 日付 |
|---------|------|------|
| [2025-12-31_phase0-1_completion.md](progress/2025-12-31_phase0-1_completion.md) | Phase 0-1完了レポート | 2025-12-31 |

---

## 🎯 開発フェーズ

### ✅ 完了済み

- **Phase 0**: 環境準備
  - GCPプロジェクト作成、API有効化、認証設定
  - ローカル開発環境構築
- **Phase 1**: バックエンド基盤構築
  - Firestore接続テスト
  - データモデル作成
  - 初期設定データ投入

### ⏳ 進行中

なし

### 📋 未着手

- **Phase 2**: ニュース収集機能（MVP）
- **Phase 3**: AI要約・分類機能
- **Phase 4**: 自動売買機能
- **Phase 5**: フロントエンド構築
- **Phase 6**: BigQuery連携
- **Phase 7**: X投稿機能
- **Phase 8**: デプロイ・運用

詳細は [TODO.md](TODO.md) を参照

---

## 🔗 リンク

### GCPコンソール
- [プロジェクトダッシュボード](https://console.cloud.google.com/home/dashboard?project=fx-insight-bot-prod)
- [Firestore](https://console.cloud.google.com/firestore/databases/fx-insight-bot-db/data?project=fx-insight-bot-prod)
- [BigQuery](https://console.cloud.google.com/bigquery?project=fx-insight-bot-prod)

### 外部ドキュメント
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Firestore公式ドキュメント](https://cloud.google.com/firestore/docs)
- [Vertex AI公式ドキュメント](https://cloud.google.com/vertex-ai/docs)

---

## 📝 ドキュメント更新ルール

### 進捗記録の命名規則
```
YYYY-MM-DD_phase<番号>_<内容>.md
```

例:
- `2025-12-31_phase0-1_completion.md` - Phase 0-1完了レポート
- `2026-01-05_phase2_start.md` - Phase 2開始時の記録

### 更新時の注意
- 各ドキュメントの最終更新日を必ず記載
- 重要な変更は変更履歴セクションに記録
- 設計変更は該当する設計書を更新

---

**最終更新**: 2025-12-31
