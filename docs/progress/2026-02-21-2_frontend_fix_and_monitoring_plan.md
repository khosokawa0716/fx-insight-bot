# 2026-02-21-2 本番環境修正 & フロントエンド監視機能 実装計画

## 実施日時
2026年2月21日（午後）

---

## 本日完了した作業

### 1. 本番環境 API接続エラーの修正

**原因**:
- Firebase Hosting と Cloud Run が別の GCP プロジェクトに存在していたため、Firebase の `run` リライトが使用不可
  - Firebase project number: `737798608273`
  - Cloud Run project number: `755346299346`
- `firebase.json` の `**` → `index.html` SPA フォールバックが `/api/**` のリクエストも全てキャッチし、HTMLを返却
- フロントエンドが HTML を JSON としてパースしようとして `Unexpected token '<'` エラーが発生

**修正内容**:
- `frontend/.env.production` を新規作成し、`VITE_API_BASE_URL` に Cloud Run URL を設定
  ```
  VITE_API_BASE_URL=https://fx-insight-bot-755346299346.asia-northeast1.run.app
  ```
- `frontend/src/lib/client.ts` を環境変数対応に修正
  - `API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''`
  - 開発時は vite proxy（`localhost:8000`）、本番時は Cloud Run URL に向く

### 2. GMOコイン メンテナンス対応（フロントエンド）

**問題**:
- GMOコイン が ERR-5201（MAINTENANCE）を返す際、バックエンドが 500 を返す
- React Query がデフォルトリトライ×3 + 30秒ポーリングを繰り返し、ローディング→エラーのループが発生

**修正内容（フロントエンドのみ）**:

| ファイル | 変更内容 |
|---------|---------|
| `src/lib/client.ts` | エラーボディを解析し、ERR-5201 なら `'MAINTENANCE'` エラーを投げる |
| `src/hooks/useAccount.ts` | `retry: false` + エラー時は `refetchInterval: false`（ポーリング停止） |
| `src/hooks/usePositions.ts` | 同上 |
| `src/pages/DashboardPage.tsx` | メンテナンス時は黄色バナーで専用メッセージを表示 |

**動作**:
- メンテナンス中 → エラー1回でポーリング停止 → 黄色バナー表示
- メンテナンス終了後 → Retry ボタンで手動更新
- 通常エラー → 従来通り赤バナーで表示

**コミット**: `ff1bb0c fix: 本番環境のAPI接続エラーとメンテナンス対応`

### 3. Cloud Run メモリ設定

- Cloud Run サービス `fx-insight-bot` のメモリを **512Mi** に設定

---

## 今後の実装計画：フロントエンド監視機能

### 背景
取引実行状況の確認が `gcloud logging` への手動アクセスに依存しており、非効率。
フロントエンドから判定結果・実行履歴を確認できる機能を追加する。

### 前提：データ保存状況の確認

Firestore `trades` コレクションへの書き込み状況（`trade_executor.py`）:

| ケース | Firestore保存 |
|--------|--------------|
| BUY/SELL 実行 | ✅ `_save_v2_trade_record()` |
| AI反対でlot=0（SKIP） | ✅ `_save_skip_log()` |
| テクニカル HOLD | ❌ **未保存（要修正）** |

HOLD 判定がFirestoreに記録されないため、実行履歴に空白が生まれている。

---

### Task 1: HOLD判定の Firestore 保存（バックエンド修正）

**対象ファイル**: `backend/src/services/trade_executor.py`

**変更内容**:
- `signal == "hold"` の分岐で `_save_hold_log()` または既存の `_save_skip_log()` を呼ぶ
- 保存項目: timestamp, symbol, reason, technical_score, ai_decision（HOLD判定の根拠を残す）

**優先度**: High（この修正がないと履歴APIのデータが不完全）

---

### Task 2: 取引履歴 API 追加（バックエンド）

**エンドポイント**: `GET /api/v1/trade/history?limit=20`

**対象ファイル**: `backend/src/api/trade.py`

**レスポンス例**:
```json
{
  "status": "success",
  "count": 10,
  "history": [
    {
      "trade_id": "trade_20260221_090000",
      "timestamp": "2026-02-21T09:00:00",
      "action": "HOLD",
      "symbol": "USD_JPY",
      "size": 0,
      "reason": "買い要因 (1pt) vs 売り要因 (1pt) - 判断保留",
      "technical_score": { "buy_score": 1, "sell_score": 1 },
      "ai_decision": { "avg_sentiment": -0.2 }
    }
  ]
}
```

**実装メモ**:
- Firestore `trades` コレクションから `order_by("created_at", desc).limit(N)` で取得
- `dry_run` フラグでフィルタリング（本番実行のみ表示）

---

### Task 3: フロントエンド 取引履歴表示

**方針**: 既存の DashboardPage に履歴セクションを追加（別ページ不要）

**新規ファイル**:
- `frontend/src/api/trade.ts` に `fetchTradeHistory()` を追加
- `frontend/src/hooks/useTradeHistory.ts` を新規作成

**表示内容**:
```
┌──────────────────────────────────────────────────────┐
│ 取引実行履歴（最新10件）                               │
├────────────────┬──────┬────────┬────────────────────-─┤
│ 日時           │ 判定  │ サイズ │ 理由                  │
├────────────────┼──────┼────────┼───────────────────────┤
│ 02/21 09:00   │ HOLD │   -   │ 買い1pt vs 売り1pt    │
│ 02/20 21:00   │ HOLD │   -   │ ニュース -0.2         │
│ 02/20 09:00   │ BUY  │ 1000  │ 買い3pt、AI強気       │
└────────────────┴──────┴────────┴───────────────────────┘
```

**判定バッジの色分け**:
- BUY → 緑
- SELL → 赤
- HOLD → グレー
- SKIP → 黄色

---

### Task 4: 月間統計カードの拡充

既存の `/api/v1/trade/monthly-summary` エンドポイントを活用して DashboardPage に統計カードを追加。

**表示内容**:
- 当月の実行回数（BUY / SELL / HOLD / SKIP の内訳）
- 実現損益（実際に約定した取引のみ）

---

### スキップする機能

| 機能 | 理由 |
|------|------|
| `current-assessment` API（リアルタイム予測） | GMO API + Gemini AI をオンデマンド呼び出し → コスト・レイテンシが高い |
| WebSocket | 30秒ポーリングで十分 |
| ブラウザ通知 / メール通知 | Cloud Monitoring のアラートポリシーで代替可能（コードゼロ） |

---

### 実装優先順位

```
① Task 1: HOLD保存（バックエンド、~1時間）    ← ここから再開
② Task 2: /trade/history API（バックエンド、~1時間）
③ Task 3: 取引履歴テーブル（フロントエンド、~2時間）
④ Task 4: 月間統計カード（フロントエンド、~1時間）

合計目安: 5〜6時間
```

---

## 関連ファイル

- `backend/src/services/trade_executor.py` — HOLD保存の追加対象
- `backend/src/api/trade.py` — 履歴APIの追加対象
- `frontend/src/api/trade.ts` — fetchTradeHistory() 追加対象
- `frontend/src/pages/DashboardPage.tsx` — 履歴セクション追加対象
