# Phase 5.4: 追加画面実装 進捗レポート

**日付**: 2026-01-18
**フェーズ**: Phase 5.4 追加画面
**ステータス**: 🔄 進行中

---

## 概要

ダッシュボード以外の追加画面を実装中。ポジション詳細、ニュース一覧、シグナル履歴画面を順次追加。

---

## 実装済み画面

### 1. ポジション詳細画面 (`/position/:positionId`)

| 項目 | 内容 |
|------|------|
| ファイル | `frontend/src/pages/PositionDetailPage.tsx` |
| 機能 | ポジションの詳細情報表示、P/L表示 |
| ナビゲーション | ダッシュボードのポジション行クリックで遷移 |

### 2. ニュース一覧画面 (`/news`)

| 項目 | 内容 |
|------|------|
| バックエンドAPI | `GET /api/v1/news` |
| フロントエンド | `NewsPage.tsx`, `useNews` hook, `fetchNews` API |
| 機能 | AI分析済みニュース一覧、センチメント/シグナル/インパクト表示 |

**表示項目**:
- ニュースタイトル・要約
- センチメント（Bullish/Neutral/Bearish）
- シグナル（BUY/SELL/RISK OFF/IGNORE）
- インパクトバー（USD/JPY, EUR/JPY）
- タイムホライズン
- 外部リンク

### 3. シグナル履歴画面 (`/signals`)

| 項目 | 内容 |
|------|------|
| バックエンドAPI | `GET /api/v1/signals` |
| フロントエンド | `SignalsPage.tsx`, `useSignals` hook, `fetchSignals` API |
| 機能 | BUY_CANDIDATE/SELL_CANDIDATE/RISK_OFF シグナルのみ表示 |

**表示項目**:
- 日付ごとにグループ化
- シグナル種類別の色分け（緑/赤/オレンジ）
- シグナルアイコン（TrendingUp/TrendingDown/AlertTriangle）
- センチメント、インパクトバー、タイムホライズン

---

## ファイル構成

```
frontend/src/
├── pages/
│   ├── PositionDetailPage.tsx  # ポジション詳細
│   ├── NewsPage.tsx            # ニュース一覧
│   └── SignalsPage.tsx         # シグナル履歴
├── api/
│   ├── news.ts                 # fetchNews
│   └── signals.ts              # fetchSignals
├── hooks/
│   ├── useNews.ts              # ニュース取得hook
│   └── useSignals.ts           # シグナル取得hook
└── types/
    └── index.ts                # NewsItem, SignalItem 型定義

backend/src/
└── main.py                     # /api/v1/news, /api/v1/signals エンドポイント
```

---

## ルーティング

| パス | コンポーネント | 認証 |
|------|---------------|------|
| `/` | DashboardPage | 必要 |
| `/login` | LoginPage | 不要 |
| `/position/:positionId` | PositionDetailPage | 必要 |
| `/news` | NewsPage | 必要 |
| `/signals` | SignalsPage | 必要 |

---

## ナビゲーション

ダッシュボードヘッダーに追加:
- **News** - ニュース一覧へ（Newspaper アイコン）
- **Signals** - シグナル履歴へ（Radio アイコン）

---

## 残タスク

- [ ] 設定画面（表示設定のみ）

---

## コミット履歴

| コミット | 内容 |
|---------|------|
| (前回) | ポジション詳細画面 |
| (前回) | ニュース一覧画面 |
| (今回) | シグナル履歴画面 |

---

**作成者**: Claude Opus 4.5
**最終更新**: 2026-01-18
