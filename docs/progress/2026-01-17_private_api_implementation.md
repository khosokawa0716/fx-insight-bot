# GMOコイン プライベートAPI実装完了レポート

**日付**: 2026-01-17
**フェーズ**: Phase 4 - 自動売買機能
**ステータス**: ✅ 実装完了（APIキー接続確認済み・FastAPIエンドポイント実装済み）

---

## 概要

Phase 4の自動売買機能の実装が完了しました。GMOコインのプライベートAPIを使った注文発注、ポジション管理、リスク管理機能を実装し、実際のAPIキーでの接続確認も完了しました。FastAPIエンドポイントも追加し、REST API経由での取引操作が可能になりました。

---

## 実装内容

### 1. GMOCoinClient プライベートAPI拡張

更新ファイル: [backend/src/services/gmo_client.py](../../backend/src/services/gmo_client.py)

#### 新規実装メソッド

**認証関連:**
```python
def _has_private_credentials() -> bool
def _generate_signature(timestamp, method, path, body) -> str
def _get_private_headers(method, path, body) -> Dict
```

**注文関連:**
```python
def place_order(symbol, side, size, execution_type, price, stop_price, time_in_force) -> Dict
def get_orders(symbol, order_id) -> List[Dict]
def cancel_order(order_id) -> Dict
```

**ポジション関連:**
```python
def get_positions(symbol) -> List[Dict]
def close_position(position_id, symbol, side, size, execution_type, price, time_in_force) -> Dict
def close_all_positions(symbol, side, execution_type, price, time_in_force) -> Dict
```

**口座関連:**
```python
def get_account_assets() -> Dict
```

#### 認証方式

GMOコインのプライベートAPIは以下のヘッダーで認証:

```python
headers = {
    "API-KEY": api_key,
    "API-TIMESTAMP": timestamp,  # ミリ秒
    "API-SIGN": hmac_sha256_signature,
}
```

署名生成:
```python
text = timestamp + method + path + body
sign = hmac.new(secret.encode(), text.encode(), hashlib.sha256).hexdigest()
```

---

### 2. TradeExecutor クラス

新規ファイル: [backend/src/services/trade_executor.py](../../backend/src/services/trade_executor.py)

#### 機能

**シグナル実行:**
```python
def execute_signals() -> List[TradeResult]
def execute_signal_for_symbol(symbol) -> TradeResult
```

**ポジション管理:**
```python
def close_positions_for_symbol(symbol, side) -> List[TradeResult]
def get_current_positions() -> Dict[str, List[Dict]]
def get_account_summary() -> Dict
```

#### TradeConfig

```python
@dataclass
class TradeConfig:
    symbols: List[str]              # 取引対象通貨ペア
    default_size: int = 1           # デフォルト注文サイズ（1万通貨）
    max_positions_per_symbol: int = 3  # 1通貨ペアあたりの最大ポジション
    max_total_positions: int = 5    # 全体の最大ポジション
    min_confidence: float = 0.7     # 最低信頼度
    execution_type: str = "MARKET"  # 注文タイプ
```

---

### 3. RiskManager クラス

新規ファイル: [backend/src/services/risk_manager.py](../../backend/src/services/risk_manager.py)

#### 機能

**取引前チェック:**
```python
def check_trade_allowed(symbol, side, size, account_assets) -> RiskCheckResult
```

**損益管理:**
```python
def record_trade_result(profit_loss, success)
def get_risk_summary() -> Dict
```

**価格計算:**
```python
def calculate_stop_loss_price(entry_price, side, symbol) -> float
def calculate_take_profit_price(entry_price, side, symbol) -> float
```

**ポジションチェック:**
```python
def should_close_position(position, current_price) -> tuple[bool, str]
def check_position_age(position_timestamp) -> tuple[bool, str]
```

#### RiskConfig

```python
@dataclass
class RiskConfig:
    stop_loss_pips: float = 50.0       # ストップロス（50pips）
    take_profit_pips: float = 100.0    # 利確（100pips）
    max_daily_loss: float = 50000.0    # 1日の最大損失（5万円）
    max_daily_trades: int = 10         # 1日の最大取引回数
    max_position_hours: int = 24       # 最大保有時間
    max_consecutive_losses: int = 3    # 連続損失での取引停止
    min_margin_ratio: float = 100.0    # 最低証拠金率
```

---

### 4. DRY-RUNモード

APIキーなしでも動作確認できるDRY-RUNモードを実装:

```python
client = GMOCoinClient(dry_run=True)

# 注文はシミュレーション結果を返す
result = client.place_order("USD_JPY", "BUY", 1)
# {
#     "orderId": "DRY_ABC12345",
#     "symbol": "USD_JPY",
#     "side": "BUY",
#     "status": "ORDERED",
#     "_dry_run": True
# }
```

---

## テスト結果

### 実行コマンド

```bash
cd backend
source venv/bin/activate
python examples/test_trade_executor.py
```

### テスト結果サマリー

```
結果: 7/7 テスト成功
✅ PASSED: TEST 1: DRY-RUN注文
✅ PASSED: TEST 2: リスク管理
✅ PASSED: TEST 3: TradeExecutor
✅ PASSED: TEST 4: 決済シミュレーション
✅ PASSED: TEST 5: 口座サマリー
✅ PASSED: TEST 6: ストップロス・利確
✅ PASSED: TEST 7: IFDOCO注文
```

### API接続テスト結果

```
結果: 4/4 テスト成功
✅ PASSED: TEST 1: 公開API（ローソク足取得）
✅ PASSED: TEST 2: 口座情報（残高: 7,000円確認）
✅ PASSED: TEST 3: ポジション取得
✅ PASSED: TEST 4: 有効注文取得
```

### テスト詳細

**TEST 1: DRY-RUN注文**
- 買い注文・売り注文のシミュレーションが正常動作

**TEST 2: リスク管理**
- ストップロス・利確価格計算が正確
- 連続損失での取引停止が動作

**TEST 3: TradeExecutor**
- シグナル評価→注文実行の流れが正常

**TEST 4: 決済シミュレーション**
- ポジション決済のシミュレーションが正常

**TEST 5: 口座サマリー**
- 認証なしでもエラーハンドリングされる

**TEST 6: ストップロス・利確**
- 各シナリオで正しく決済判断

---

## ファイル構成

```
backend/src/
├── api/
│   ├── __init__.py           # APIモジュール
│   └── trade.py              # Trade APIルーター（新規）
├── services/
│   ├── gmo_client.py         # GMOコインAPIクライアント（拡張済み）
│   ├── trade_executor.py     # 売買実行クラス（新規）
│   ├── risk_manager.py       # リスク管理クラス（新規）
│   ├── rule_engine.py        # ルールエンジン
│   ├── technical_analyzer.py # テクニカル分析
│   ├── news_analyzer.py      # ニュース分析
│   └── ...
├── config.py                 # 設定（GMO API追加）
└── main.py                   # FastAPIアプリ（ルーター追加）

backend/examples/
├── test_api_connection.py    # API接続テスト（新規）
└── test_trade_executor.py    # テストスクリプト（新規）
```

---

## FastAPI エンドポイント

### Trade API (`/api/v1/trade`)

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | `/account` | 口座資産情報取得 |
| GET | `/positions` | ポジション一覧取得 |
| GET | `/orders` | 有効注文一覧取得 |
| POST | `/order` | 新規注文発注 |
| POST | `/order/ifdoco` | IFDOCO注文発注 |
| POST | `/order/cancel` | 注文キャンセル |
| POST | `/execute` | シグナルに基づく自動売買実行 |
| GET | `/risk/summary` | リスクサマリー取得 |

### エンドポイントテスト結果

```bash
# 口座情報
curl http://localhost:8000/api/v1/trade/account
# {"status":"success","data":{"balance":"7000","availableAmount":"7000",...}}

# DRY-RUN注文
curl -X POST http://localhost:8000/api/v1/trade/order \
  -H "Content-Type: application/json" \
  -d '{"symbol":"USD_JPY","side":"BUY","size":1,"dry_run":true}'
# {"status":"success","message":"[DRY-RUN] Order placed: BUY 1 USD_JPY",...}

# シグナル実行
curl -X POST http://localhost:8000/api/v1/trade/execute \
  -H "Content-Type: application/json" \
  -d '{"symbols":["USD_JPY"],"dry_run":true}'
# {"status":"success","message":"[DRY-RUN] Executed 1/1 signals",...}
```

---

## 使用方法

### 基本的な使用例

```python
from src.services.gmo_client import GMOCoinClient
from src.services.technical_analyzer import TechnicalAnalyzer
from src.services.rule_engine import RuleEngine
from src.services.trade_executor import TradeExecutor, TradeConfig
from src.services.risk_manager import RiskManager, RiskConfig

# クライアント初期化
gmo_client = GMOCoinClient(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    dry_run=False,  # 本番時はFalse
)

# コンポーネント初期化
technical_analyzer = TechnicalAnalyzer(gmo_client)
rule_engine = RuleEngine(technical_analyzer=technical_analyzer)

# 設定
trade_config = TradeConfig(
    symbols=["USD_JPY", "EUR_JPY"],
    default_size=1,
    min_confidence=0.7,
)

# 実行
executor = TradeExecutor(
    gmo_client=gmo_client,
    rule_engine=rule_engine,
    config=trade_config,
)

# シグナルに基づいて自動売買
results = executor.execute_signals()
```

### リスク管理との連携

```python
risk_config = RiskConfig(
    stop_loss_pips=50.0,
    take_profit_pips=100.0,
    max_daily_loss=50000.0,
)

risk_manager = RiskManager(config=risk_config)

# 取引前チェック
check = risk_manager.check_trade_allowed("USD_JPY", "BUY", 1)
if check.can_trade:
    # 取引実行
    pass
else:
    print(f"取引不可: {check.reason}")
```

---

## 次のステップ

### 本番稼働に必要な作業

1. ~~**GMOコインAPIキー取得**~~ ✅ 完了
   - ~~デモ口座でのAPI利用申請~~
   - ~~APIキー・シークレットの取得~~

2. ~~**実APIでのテスト**~~ ✅ 完了
   - ~~DRY-RUN=Falseでの接続テスト~~
   - 口座残高7,000円を確認

3. ~~**FastAPIエンドポイント追加**~~ ✅ 完了
   - ~~`/api/v1/trade/execute` - シグナル実行~~
   - ~~`/api/v1/trade/positions` - ポジション一覧~~
   - ~~`/api/v1/trade/order` - 注文発注~~

4. **Cloud Schedulerとの連携**
   - 定期的なシグナル評価・実行

5. **モニタリング・アラート**
   - 取引履歴のFirestore保存
   - 異常検知アラート

6. **本番デプロイ**
   - Cloud Runへのデプロイ
   - 環境変数の設定

---

## 技術的な注意点

### レート制限

```
GET: 6リクエスト/秒
POST: 1リクエスト/秒
```

実装済みのレート制限待機で対応。

### エラーハンドリング

```python
# 認証エラー
AuthenticationError: APIキー未設定時

# 注文エラー
OrderError: 注文失敗時

# 残高不足
InsufficientFundsError: 残高不足時
```

### セキュリティ

- APIキー・シークレットは環境変数で管理
- コードにハードコードしない
- ログにシークレットを出力しない

---

## まとめ

Phase 4の自動売買機能の実装が完了しました。

**✅ 実装完了:**
1. GMOコインプライベートAPI認証
2. 注文発注・キャンセル
3. ポジション照会・決済
4. TradeExecutor（シグナルベース自動売買）
5. RiskManager（リスク管理）
6. DRY-RUNモードテスト
7. 実APIでの接続確認（口座残高7,000円確認）
8. FastAPI Trade APIエンドポイント（8エンドポイント）
9. 環境変数からのAPI認証情報自動読み込み

**🔜 残タスク:**
1. Cloud Schedulerとの連携
2. モニタリング・アラート
3. 本番デプロイ

---

**作成者**: Claude Opus 4.5
**最終更新**: 2026-01-17
