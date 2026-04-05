# 2026-04-05 決済チェック機能の実装（settle-check）

## 背景・目的

IFDOCO 注文の TP/SL が約定しても `actual_pnl` が Firestore に書き込まれない問題を解消する。

- エントリー注文後、Firestore の `status` は `"open"` で固定されたまま
- `update_trade_settlement()` を自動で呼ぶ仕組みが存在しなかった
- 月次サマリーの `total_trades` が 0 になる原因でもあった

## 実装内容

### 追加したファイル・関数

| ファイル | 追加内容 |
|---|---|
| `backend/src/services/gmo_client.py` | `get_executions(order_id)` |
| `backend/src/services/gmo_client.py` | `get_latest_executions(symbol, count)` |
| `backend/src/services/trade_executor.py` | `settle_open_trades()` |
| `backend/src/api/trade.py` | `POST /api/v1/trade/settle-check` |

### 処理フロー（settle_open_trades）

```
Firestore: status="open" の BUY/SELL を全件取得
    ↓
各トレードの order_id で GET /v1/executions → OPEN execution → positionId 取得
    ↓ OPEN execution がない → エントリー未約定（スキップ）
GET /v1/latestExecutions (シンボル単位でキャッシュ)
    ↓ CLOSE execution が positionId 一致 → なし → still_open（スキップ）
lossGain / price を取得 → update_trade_settlement() → Firestore 更新（WIN/LOSS）
```

### latestExecutions の 24 時間制約について

`GET /v1/latestExecutions` は直近 24 時間のみ対象。
土日の決済も確実にカバーするため、Cloud Scheduler は**毎日（土日含む）8:30 JST**に実行する。

---

## デプロイ手順

→ [docs/guides/CLOUD_RUN_OPERATIONS.md](../guides/CLOUD_RUN_OPERATIONS.md) を参照

---

## テスト手順（API 単位）

> **注意**: macOS では `python3` が Xcode ライセンス同意を要求する場合がある。
> 全コマンドで `venv/bin/python3` を使うこと（`cd backend` 済みの前提）。

### ローカルテスト（サーバー起動）

```bash
cd backend && venv/bin/python3 -m uvicorn src.main:app --reload --port 8080
```

### Step 1: エンドポイントの疎通確認

```bash
curl -s -X POST http://localhost:8080/api/v1/trade/settle-check \
  | venv/bin/python3 -m json.tool
```

期待レスポンス（open トレードがない場合）:
```json
{
  "status": "success",
  "checked": 0,
  "settled": 0,
  "results": []
}
```

### Step 2: GMO API 単体確認（executions）

Firestore から open トレードの `order_id` を確認してから実行する。

```bash
# ORDER_ID を Firestore の実際の値に置き換える
ORDER_ID=123456789

cd backend && venv/bin/python3 - <<'EOF'
import os, sys
sys.path.insert(0, '.')
from src.services.gmo_client import GMOCoinClient

client = GMOCoinClient()
result = client.get_executions(ORDER_ID)
import json; print(json.dumps(result, indent=2, ensure_ascii=False))
EOF
```

期待レスポンス:
```json
[
  {
    "executionId": 92123912,
    "orderId": 123456789,
    "positionId": 2234567,
    "settleType": "OPEN",
    "price": "150.123",
    "lossGain": "0",
    ...
  }
]
```

### Step 3: GMO API 単体確認（latestExecutions）

```bash
cd backend && venv/bin/python3 - <<'EOF'
import os, sys
sys.path.insert(0, '.')
from src.services.gmo_client import GMOCoinClient

client = GMOCoinClient()
result = client.get_latest_executions("USD_JPY")
import json; print(json.dumps(result, indent=2, ensure_ascii=False))
EOF
```

CLOSE execution が含まれる場合の確認ポイント:
- `settleType: "CLOSE"` の行を探す
- `positionId` が Step 2 の値と一致するか
- `lossGain` が実現損益として正しいか

### Step 4: settle-check 全体フローの確認（本番 Service B）

```bash
# OIDC トークンを取得してリクエスト
TOKEN=$(gcloud auth print-identity-token)

curl -s -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app/api/v1/trade/settle-check \
  | venv/bin/python3 -m json.tool
```

期待レスポンス（open トレードが決済済みの場合）:
```json
{
  "status": "success",
  "checked": 1,
  "settled": 1,
  "results": [
    {
      "trade_id": "20260401_090000_USD_JPY",
      "status": "settled",
      "result": "WIN",
      "actual_pnl": 400.0,
      "exit_price": 150.523
    }
  ]
}
```

---

## Cloud Scheduler の設定

→ [docs/guides/CLOUD_RUN_OPERATIONS.md](../guides/CLOUD_RUN_OPERATIONS.md) を参照

**設計の背景（このドキュメントにのみ記載）:**
- `latestExecutions` は直近 24 時間のみ対象
- 土日に決済が起きても月曜まで取りこぼさないよう、**毎日（土日含む）8:30 JST** に独立ジョブとして実行
- trade/execute（月〜金のみ）への組み込みは 24 時間制約により不適切なため採用しなかった
