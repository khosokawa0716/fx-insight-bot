"""
GMO Coin Client

GMOコインのREST APIと通信するためのクライアントクラス
Phase 3: ローソク足取得（公開API）
Phase 4: 注文・ポジション管理（プライベートAPI）
"""

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

import requests
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

logger = logging.getLogger(__name__)


class GMOClientError(Exception):
    """GMOクライアント基底例外"""

    pass


class APIError(GMOClientError):
    """API呼び出しエラー"""

    pass


class RateLimitError(GMOClientError):
    """レート制限エラー"""

    pass


class AuthenticationError(GMOClientError):
    """認証エラー（APIキー未設定など）"""

    pass


class OrderError(GMOClientError):
    """注文関連エラー"""

    pass


class InsufficientFundsError(OrderError):
    """残高不足エラー"""

    pass


class GMOCoinClient:
    """
    GMOコイン APIクライアント

    Phase 3: 公開API（ローソク足取得）
    Phase 4: プライベートAPI（注文・ポジション管理）
    """

    # API Base URL
    BASE_URL = "https://forex-api.coin.z.com"
    PUBLIC_ENDPOINT = f"{BASE_URL}/public/v1"
    PRIVATE_ENDPOINT = f"{BASE_URL}/private/v1"

    # レート制限
    RATE_LIMIT_GET = 6  # GET: 6リクエスト/秒
    RATE_LIMIT_POST = 1  # POST: 1リクエスト/秒

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        dry_run: bool = False,
    ):
        """
        初期化

        Args:
            api_key: APIキー（プライベートAPI用、未指定時は環境変数GMO_API_KEYから取得）
            api_secret: APIシークレット（プライベートAPI用、未指定時は環境変数GMO_API_SECRETから取得）
            timeout: タイムアウト（秒）
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
            dry_run: Trueの場合、実際の注文は行わずシミュレーションのみ
        """
        # 環境変数からAPIキーを取得（引数が優先）
        self.api_key = api_key or os.getenv("GMO_API_KEY")
        self.api_secret = api_secret or os.getenv("GMO_API_SECRET")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dry_run = dry_run

        # レート制限管理
        self._last_request_time_get = 0.0
        self._last_request_time_post = 0.0
        self._request_interval_get = 1.0 / self.RATE_LIMIT_GET  # 約0.17秒
        self._request_interval_post = 1.0 / self.RATE_LIMIT_POST  # 1秒

        mode = "DRY-RUN" if dry_run else ("Private" if api_key else "Public")
        logger.info(f"GMOCoinClient initialized ({mode} API mode)")

    def _has_private_credentials(self) -> bool:
        """プライベートAPI用の認証情報があるか確認"""
        return bool(self.api_key and self.api_secret)

    def _generate_signature(
        self, timestamp: str, method: str, path: str, body: str = ""
    ) -> str:
        """
        API署名を生成

        Args:
            timestamp: UNIXタイムスタンプ（ミリ秒）
            method: HTTPメソッド（GET/POST）
            path: リクエストパス（/v1/...）
            body: リクエストボディ（POSTの場合）

        Returns:
            HMAC-SHA256署名
        """
        text = timestamp + method + path + body
        sign = hmac.new(
            bytes(self.api_secret.encode("ascii")),
            bytes(text.encode("ascii")),
            hashlib.sha256,
        ).hexdigest()
        return sign

    def _get_private_headers(self, method: str, path: str, body: str = "") -> Dict:
        """
        プライベートAPI用のHTTPヘッダーを生成

        Args:
            method: HTTPメソッド
            path: リクエストパス
            body: リクエストボディ

        Returns:
            認証ヘッダーを含むDict
        """
        timestamp = str(int(time.time() * 1000))
        sign = self._generate_signature(timestamp, method, path, body)

        return {
            "API-KEY": self.api_key,
            "API-TIMESTAMP": timestamp,
            "API-SIGN": sign,
            "Content-Type": "application/json",
        }

    def _wait_for_rate_limit(self, method: str = "GET"):
        """
        レート制限のための待機

        Args:
            method: HTTPメソッド（GET/POST）
        """
        current_time = time.time()

        if method == "POST":
            elapsed = current_time - self._last_request_time_post
            interval = self._request_interval_post
        else:
            elapsed = current_time - self._last_request_time_get
            interval = self._request_interval_get

        if elapsed < interval:
            wait_time = interval - elapsed
            logger.debug(f"Rate limit wait ({method}): {wait_time:.2f}s")
            time.sleep(wait_time)

        if method == "POST":
            self._last_request_time_post = time.time()
        else:
            self._last_request_time_get = time.time()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None,
        private: bool = False,
    ) -> Dict:
        """
        HTTPリクエスト実行（リトライ付き）

        Args:
            method: HTTPメソッド（GET, POST）
            endpoint: エンドポイントURL
            params: クエリパラメータ（GETリクエスト用）
            body: リクエストボディ（POSTリクエスト用）
            private: プライベートAPI使用フラグ

        Returns:
            APIレスポンス

        Raises:
            APIError: API呼び出しエラー
            RateLimitError: レート制限エラー
            AuthenticationError: 認証エラー
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                # レート制限待機
                self._wait_for_rate_limit(method)

                # リクエスト実行
                logger.debug(f"Request: {method} {endpoint} (attempt {attempt})")

                # ヘッダー準備
                headers = {}
                if private:
                    if not self._has_private_credentials():
                        raise AuthenticationError(
                            "API key and secret required for private API"
                        )
                    # パスを抽出（/v1/...の形式で署名に使用）
                    # PRIVATE_ENDPOINTから/v1部分を含めてパスを取得
                    base_url = f"{self.BASE_URL}/private"
                    path = endpoint.replace(base_url, "")  # /v1/account/assets 形式
                    body_str = json.dumps(body) if body else ""
                    headers = self._get_private_headers(method, path, body_str)

                if method == "GET":
                    response = requests.get(
                        endpoint, params=params, headers=headers, timeout=self.timeout
                    )
                elif method == "POST":
                    response = requests.post(
                        endpoint, json=body, headers=headers, timeout=self.timeout
                    )
                else:
                    raise NotImplementedError(f"Method {method} not implemented")

                # ステータスコードチェック
                if response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")

                if response.status_code == 401:
                    raise AuthenticationError("Authentication failed")

                response.raise_for_status()

                # JSONパース
                data = response.json()

                # GMOコインAPIのエラーチェック
                if "status" in data and data["status"] != 0:
                    error_msg = data.get("messages", ["Unknown error"])
                    error_code = data.get("responsecode", "")
                    raise APIError(f"API Error [{error_code}]: {error_msg}")

                logger.debug(f"Request successful: {endpoint}")
                return data

            except (RateLimitError, AuthenticationError):
                # 認証エラーはリトライしない
                raise

            except RateLimitError as e:
                logger.warning(f"Rate limit hit (attempt {attempt}): {e}")
                if attempt < self.max_retries:
                    # 指数バックオフ
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt}): {e}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * attempt
                    logger.info(f"Retrying after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise APIError(
                        f"Request failed after {self.max_retries} attempts: {e}"
                    )

            except APIError:
                raise

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise APIError(f"Unexpected error: {e}")

        raise APIError("Max retries exceeded")

    # ============================================================
    # 公開API - Phase 3
    # ============================================================

    def get_klines(
        self,
        symbol: str,
        interval: str,
        date: Optional[str] = None,
        price_type: str = "ASK",
    ) -> List[Dict]:
        """
        ローソク足データを取得

        Args:
            symbol: 通貨ペア（例: USD_JPY, EUR_JPY）
            interval: 時間足（1min, 5min, 10min, 15min, 30min, 1hour, 4hour, 8hour, 12hour, 1day, 1week, 1month）
            date: 日付（YYYYMMDD形式、省略時は今日）
            price_type: BID or ASK（デフォルト: ASK）

        Returns:
            ローソク足データのリスト
            [
                {
                    "openTime": "1618588800000",
                    "open": "141.365",
                    "high": "141.368",
                    "low": "141.360",
                    "close": "141.362"
                },
                ...
            ]

        Raises:
            APIError: API呼び出しエラー
        """
        # 日付が指定されていない場合は今日
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        # パラメータ
        params = {
            "symbol": symbol,
            "priceType": price_type,
            "interval": interval,
            "date": date,
        }

        # APIリクエスト
        endpoint = f"{self.PUBLIC_ENDPOINT}/klines"
        logger.info(
            f"Fetching klines: {symbol} {interval} {date} ({price_type})"
        )

        response = self._request("GET", endpoint, params=params)

        # データ取得
        klines = response.get("data", [])
        logger.info(f"Fetched {len(klines)} klines")

        return klines

    def get_klines_range(
        self,
        symbol: str,
        interval: str,
        days: int = 7,
        price_type: str = "ASK",
    ) -> List[Dict]:
        """
        指定期間のローソク足データを取得

        Args:
            symbol: 通貨ペア
            interval: 時間足
            days: 取得日数（デフォルト: 7日）
            price_type: BID or ASK

        Returns:
            複数日のローソク足データを統合したリスト

        Raises:
            APIError: API呼び出しエラー
        """
        all_klines = []
        today = datetime.now()

        logger.info(
            f"Fetching klines range: {symbol} {interval} (past {days} days)"
        )

        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y%m%d")
            try:
                klines = self.get_klines(symbol, interval, date, price_type)
                all_klines.extend(klines)
            except APIError as e:
                logger.warning(f"Failed to fetch klines for {date}: {e}")
                # 失敗しても続行

        # 時刻順にソート
        all_klines.sort(key=lambda x: int(x["openTime"]))

        logger.info(f"Total klines fetched: {len(all_klines)}")
        return all_klines

    # ============================================================
    # プライベートAPI - Phase 4
    # ============================================================

    def get_account_assets(self) -> Dict:
        """
        口座資産情報を取得

        Returns:
            口座資産情報
            {
                "availableAmount": "1000000",  # 取引余力
                "balance": "1000000",          # 口座残高
                "margin": "0",                 # 必要証拠金
                "profitLoss": "0",             # 評価損益
                "transferableAmount": "1000000"  # 振替可能額
            }

        Raises:
            AuthenticationError: 認証エラー
            APIError: API呼び出しエラー
        """
        endpoint = f"{self.PRIVATE_ENDPOINT}/account/assets"
        logger.info("Fetching account assets")

        response = self._request("GET", endpoint, private=True)
        return response.get("data", {})

    def place_order(
        self,
        symbol: str,
        side: Literal["BUY", "SELL"],
        size: int,
        execution_type: Literal["MARKET", "LIMIT", "STOP"] = "MARKET",
        price: Optional[str] = None,
        stop_price: Optional[str] = None,
        time_in_force: Literal["FAK", "FAS", "FOK"] = "FAK",
    ) -> Dict:
        """
        新規注文を発注

        Args:
            symbol: 通貨ペア（例: USD_JPY, EUR_JPY）
            side: 売買区分（BUY: 買い, SELL: 売り）
            size: 注文数量（1 = 1万通貨）
            execution_type: 注文タイプ
                - MARKET: 成行注文
                - LIMIT: 指値注文
                - STOP: 逆指値注文
            price: 注文価格（LIMIT注文時に必須）
            stop_price: 逆指値価格（STOP注文時に必須）
            time_in_force: 執行条件
                - FAK: Fill and Kill（一部約定後、残りはキャンセル）
                - FAS: Fill and Store（一部約定後、残りは有効）
                - FOK: Fill or Kill（全数量約定しなければキャンセル）

        Returns:
            注文結果
            {
                "orderId": "123456789",
                "symbol": "USD_JPY",
                "side": "BUY",
                "size": "1",
                "executionType": "MARKET",
                "status": "ORDERED"
            }

        Raises:
            AuthenticationError: 認証エラー
            OrderError: 注文エラー
            APIError: API呼び出しエラー
        """
        # DRY-RUNモード
        if self.dry_run:
            logger.info(f"[DRY-RUN] Order: {side} {size} {symbol} @ {execution_type}")
            return self._simulate_order(symbol, side, size, execution_type, price)

        # リクエストボディ
        body: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "size": str(size),
            "executionType": execution_type,
            "timeInForce": time_in_force,
        }

        if execution_type == "LIMIT" and price:
            body["price"] = price
        elif execution_type == "STOP" and stop_price:
            body["stopPrice"] = stop_price

        endpoint = f"{self.PRIVATE_ENDPOINT}/order"
        logger.info(f"Placing order: {side} {size} {symbol} @ {execution_type}")

        try:
            response = self._request("POST", endpoint, body=body, private=True)
            order_data = response.get("data", {})
            logger.info(f"Order placed: {order_data.get('orderId', 'N/A')}")
            return order_data
        except APIError as e:
            logger.error(f"Order failed: {e}")
            raise OrderError(f"Failed to place order: {e}")

    def get_orders(
        self,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        有効注文一覧を取得

        Args:
            symbol: 通貨ペア（省略時は全通貨ペア）
            order_id: 注文ID（特定の注文のみ取得）

        Returns:
            有効注文のリスト
            [
                {
                    "orderId": "123456789",
                    "symbol": "USD_JPY",
                    "side": "BUY",
                    "size": "1",
                    "executedSize": "0",
                    "price": "150.000",
                    "status": "ORDERED",
                    "timeInForce": "FAK",
                    "timestamp": "2026-01-12T10:00:00.000Z"
                }
            ]

        Raises:
            AuthenticationError: 認証エラー
            APIError: API呼び出しエラー
        """
        endpoint = f"{self.PRIVATE_ENDPOINT}/activeOrders"
        params = {}
        if symbol:
            params["symbol"] = symbol
        if order_id:
            params["orderId"] = order_id

        logger.info(f"Fetching active orders: symbol={symbol}")

        response = self._request("GET", endpoint, params=params, private=True)
        return response.get("data", {}).get("list", [])

    def cancel_order(self, order_id: str) -> Dict:
        """
        注文をキャンセル

        Args:
            order_id: 注文ID

        Returns:
            キャンセル結果

        Raises:
            AuthenticationError: 認証エラー
            APIError: API呼び出しエラー
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Cancel order: {order_id}")
            return {"orderId": order_id, "status": "CANCELED"}

        endpoint = f"{self.PRIVATE_ENDPOINT}/cancelOrder"
        body = {"orderId": order_id}

        logger.info(f"Canceling order: {order_id}")

        response = self._request("POST", endpoint, body=body, private=True)
        return response.get("data", {})

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        建玉（ポジション）一覧を取得

        Args:
            symbol: 通貨ペア（省略時は全通貨ペア）

        Returns:
            ポジションのリスト
            [
                {
                    "positionId": "123456789",
                    "symbol": "USD_JPY",
                    "side": "BUY",
                    "size": "1",
                    "orderdSize": "1",
                    "price": "150.000",
                    "lossGain": "1000",
                    "timestamp": "2026-01-12T10:00:00.000Z"
                }
            ]

        Raises:
            AuthenticationError: 認証エラー
            APIError: API呼び出しエラー
        """
        endpoint = f"{self.PRIVATE_ENDPOINT}/openPositions"
        params = {}
        if symbol:
            params["symbol"] = symbol

        logger.info(f"Fetching positions: symbol={symbol}")

        response = self._request("GET", endpoint, params=params, private=True)
        return response.get("data", {}).get("list", [])

    def close_position(
        self,
        position_id: str,
        symbol: str,
        side: Literal["BUY", "SELL"],
        size: int,
        execution_type: Literal["MARKET", "LIMIT"] = "MARKET",
        price: Optional[str] = None,
        time_in_force: Literal["FAK", "FAS", "FOK"] = "FAK",
    ) -> Dict:
        """
        ポジションを決済

        Args:
            position_id: ポジションID
            symbol: 通貨ペア
            side: 決済の売買区分（BUYポジションならSELL、SELLポジションならBUY）
            size: 決済数量
            execution_type: 注文タイプ（MARKET/LIMIT）
            price: 指値価格（LIMIT時）
            time_in_force: 執行条件

        Returns:
            決済結果
            {
                "orderId": "123456789",
                "status": "ORDERED"
            }

        Raises:
            AuthenticationError: 認証エラー
            OrderError: 決済エラー
            APIError: API呼び出しエラー
        """
        if self.dry_run:
            logger.info(
                f"[DRY-RUN] Close position: {position_id} {side} {size} {symbol}"
            )
            return self._simulate_close_position(position_id, symbol, side, size)

        body: Dict[str, Any] = {
            "positionId": position_id,
            "symbol": symbol,
            "side": side,
            "size": str(size),
            "executionType": execution_type,
            "timeInForce": time_in_force,
        }

        if execution_type == "LIMIT" and price:
            body["price"] = price

        endpoint = f"{self.PRIVATE_ENDPOINT}/closeOrder"
        logger.info(f"Closing position: {position_id} {side} {size} {symbol}")

        try:
            response = self._request("POST", endpoint, body=body, private=True)
            result = response.get("data", {})
            logger.info(f"Position closed: order_id={result.get('orderId', 'N/A')}")
            return result
        except APIError as e:
            logger.error(f"Close position failed: {e}")
            raise OrderError(f"Failed to close position: {e}")

    def close_all_positions(
        self,
        symbol: str,
        side: Literal["BUY", "SELL"],
        execution_type: Literal["MARKET", "LIMIT"] = "MARKET",
        price: Optional[str] = None,
        time_in_force: Literal["FAK", "FAS", "FOK"] = "FAK",
    ) -> Dict:
        """
        指定通貨ペア・サイドの全ポジションを一括決済

        Args:
            symbol: 通貨ペア
            side: 決済の売買区分
            execution_type: 注文タイプ
            price: 指値価格（LIMIT時）
            time_in_force: 執行条件

        Returns:
            一括決済結果

        Raises:
            AuthenticationError: 認証エラー
            OrderError: 決済エラー
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Close all positions: {side} {symbol}")
            return {"status": "ORDERED", "symbol": symbol, "side": side}

        body: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "executionType": execution_type,
            "timeInForce": time_in_force,
        }

        if execution_type == "LIMIT" and price:
            body["price"] = price

        endpoint = f"{self.PRIVATE_ENDPOINT}/closeBulkOrder"
        logger.info(f"Closing all positions: {side} {symbol}")

        try:
            response = self._request("POST", endpoint, body=body, private=True)
            return response.get("data", {})
        except APIError as e:
            logger.error(f"Close all positions failed: {e}")
            raise OrderError(f"Failed to close all positions: {e}")

    def place_ifdoco_order(
        self,
        symbol: str,
        first_side: Literal["BUY", "SELL"],
        first_execution_type: Literal["LIMIT", "STOP"],
        first_size: int,
        first_price: str,
        second_size: int,
        second_limit_price: str,
        second_stop_price: str,
        client_order_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        IFDOCO注文を発注

        新規注文（IFD）と決済注文（OCO: 利確+損切り）を同時に発注します。
        1次注文が約定すると、自動的に2次注文（OCO）が発注されます。

        Args:
            symbol: 通貨ペア（例: USD_JPY, EUR_JPY）
            first_side: 1次注文の売買区分（BUY/SELL）
            first_execution_type: 1次注文タイプ（LIMIT: 指値, STOP: 逆指値）
            first_size: 1次注文数量（1 = 1万通貨）
            first_price: 1次注文レート
            second_size: 2次注文数量（1 = 1万通貨）
            second_limit_price: 2次指値注文レート（利確価格）
            second_stop_price: 2次逆指値注文レート（損切り価格）
            client_order_id: 顧客注文ID（36文字以内、オプション）

        Returns:
            注文結果のリスト（3件: 1次注文 + 2次OCO注文2件）
            [
                {
                    "rootOrderId": 123456789,
                    "orderId": 123456789,
                    "symbol": "USD_JPY",
                    "side": "BUY",
                    "orderType": "IFDOCO",
                    "executionType": "LIMIT",
                    "settleType": "OPEN",
                    "size": "10000",
                    "price": "135",
                    "status": "WAITING"
                },
                {
                    "rootOrderId": 123456789,
                    "orderId": 123456790,
                    "symbol": "USD_JPY",
                    "side": "SELL",
                    "orderType": "IFDOCO",
                    "executionType": "LIMIT",
                    "settleType": "CLOSE",
                    "size": "10000",
                    "price": "140",
                    "status": "WAITING"
                },
                {
                    "rootOrderId": 123456789,
                    "orderId": 123456791,
                    "symbol": "USD_JPY",
                    "side": "SELL",
                    "orderType": "IFDOCO",
                    "executionType": "STOP",
                    "settleType": "CLOSE",
                    "size": "10000",
                    "price": "132",
                    "status": "WAITING"
                }
            ]

        Raises:
            AuthenticationError: 認証エラー
            OrderError: 注文エラー
            APIError: API呼び出しエラー

        Example:
            # USD/JPYを135円で買い、140円で利確、132円で損切り
            result = client.place_ifdoco_order(
                symbol="USD_JPY",
                first_side="BUY",
                first_execution_type="LIMIT",
                first_size=1,
                first_price="135",
                second_size=1,
                second_limit_price="140",  # 利確
                second_stop_price="132",   # 損切り
            )
        """
        # DRY-RUNモード
        if self.dry_run:
            logger.info(
                f"[DRY-RUN] IFDOCO Order: {first_side} {first_size} {symbol} "
                f"@ {first_price}, TP={second_limit_price}, SL={second_stop_price}"
            )
            return self._simulate_ifdoco_order(
                symbol=symbol,
                first_side=first_side,
                first_execution_type=first_execution_type,
                first_size=first_size,
                first_price=first_price,
                second_size=second_size,
                second_limit_price=second_limit_price,
                second_stop_price=second_stop_price,
                client_order_id=client_order_id,
            )

        # リクエストボディ
        body: Dict[str, Any] = {
            "symbol": symbol,
            "firstSide": first_side,
            "firstExecutionType": first_execution_type,
            "firstSize": str(first_size),
            "firstPrice": first_price,
            "secondSize": str(second_size),
            "secondLimitPrice": second_limit_price,
            "secondStopPrice": second_stop_price,
        }

        if client_order_id:
            body["clientOrderId"] = client_order_id

        endpoint = f"{self.PRIVATE_ENDPOINT}/ifoOrder"
        logger.info(
            f"Placing IFDOCO order: {first_side} {first_size} {symbol} "
            f"@ {first_price}, TP={second_limit_price}, SL={second_stop_price}"
        )

        try:
            response = self._request("POST", endpoint, body=body, private=True)
            order_data = response.get("data", [])
            if order_data:
                root_order_id = order_data[0].get("rootOrderId", "N/A")
                logger.info(f"IFDOCO order placed: rootOrderId={root_order_id}")
            return order_data
        except APIError as e:
            logger.error(f"IFDOCO order failed: {e}")
            raise OrderError(f"Failed to place IFDOCO order: {e}")

    def place_ifd_order(
        self,
        symbol: str,
        first_side: Literal["BUY", "SELL"],
        first_execution_type: Literal["LIMIT", "STOP"],
        first_size: int,
        first_price: str,
        second_execution_type: Literal["LIMIT", "STOP"],
        second_size: int,
        second_price: str,
        client_order_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        IFD注文を発注

        新規注文と決済注文を同時に発注します。
        1次注文が約定すると、自動的に2次注文が発注されます。

        Args:
            symbol: 通貨ペア
            first_side: 1次注文の売買区分（BUY/SELL）
            first_execution_type: 1次注文タイプ（LIMIT/STOP）
            first_size: 1次注文数量
            first_price: 1次注文レート
            second_execution_type: 2次注文タイプ（LIMIT/STOP）
            second_size: 2次注文数量
            second_price: 2次注文レート
            client_order_id: 顧客注文ID（オプション）

        Returns:
            注文結果のリスト（2件: 1次注文 + 2次注文）

        Raises:
            AuthenticationError: 認証エラー
            OrderError: 注文エラー
        """
        # DRY-RUNモード
        if self.dry_run:
            logger.info(
                f"[DRY-RUN] IFD Order: {first_side} {first_size} {symbol} "
                f"@ {first_price} -> {second_price}"
            )
            return self._simulate_ifd_order(
                symbol=symbol,
                first_side=first_side,
                first_execution_type=first_execution_type,
                first_size=first_size,
                first_price=first_price,
                second_execution_type=second_execution_type,
                second_size=second_size,
                second_price=second_price,
                client_order_id=client_order_id,
            )

        body: Dict[str, Any] = {
            "symbol": symbol,
            "firstSide": first_side,
            "firstExecutionType": first_execution_type,
            "firstSize": str(first_size),
            "firstPrice": first_price,
            "secondExecutionType": second_execution_type,
            "secondSize": str(second_size),
            "secondPrice": second_price,
        }

        if client_order_id:
            body["clientOrderId"] = client_order_id

        endpoint = f"{self.PRIVATE_ENDPOINT}/ifdOrder"
        logger.info(
            f"Placing IFD order: {first_side} {first_size} {symbol} "
            f"@ {first_price} -> {second_price}"
        )

        try:
            response = self._request("POST", endpoint, body=body, private=True)
            order_data = response.get("data", [])
            if order_data:
                root_order_id = order_data[0].get("rootOrderId", "N/A")
                logger.info(f"IFD order placed: rootOrderId={root_order_id}")
            return order_data
        except APIError as e:
            logger.error(f"IFD order failed: {e}")
            raise OrderError(f"Failed to place IFD order: {e}")

    # ============================================================
    # シミュレーション（DRY-RUNモード用）
    # ============================================================

    def _simulate_order(
        self,
        symbol: str,
        side: str,
        size: int,
        execution_type: str,
        price: Optional[str],
    ) -> Dict:
        """注文のシミュレーション結果を生成"""
        import uuid

        order_id = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().isoformat()

        return {
            "orderId": order_id,
            "symbol": symbol,
            "side": side,
            "size": str(size),
            "executionType": execution_type,
            "price": price or "MARKET",
            "status": "ORDERED",
            "timestamp": timestamp,
            "_dry_run": True,
        }

    def _simulate_close_position(
        self,
        position_id: str,
        symbol: str,
        side: str,
        size: int,
    ) -> Dict:
        """決済のシミュレーション結果を生成"""
        import uuid

        order_id = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().isoformat()

        return {
            "orderId": order_id,
            "positionId": position_id,
            "symbol": symbol,
            "side": side,
            "size": str(size),
            "status": "ORDERED",
            "timestamp": timestamp,
            "_dry_run": True,
        }

    def _simulate_ifdoco_order(
        self,
        symbol: str,
        first_side: str,
        first_execution_type: str,
        first_size: int,
        first_price: str,
        second_size: int,
        second_limit_price: str,
        second_stop_price: str,
        client_order_id: Optional[str] = None,
    ) -> List[Dict]:
        """IFDOCO注文のシミュレーション結果を生成"""
        import uuid

        root_order_id = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        order_id_1 = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        order_id_2 = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        order_id_3 = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().isoformat()

        # 2次注文のサイドは1次注文の逆
        second_side = "SELL" if first_side == "BUY" else "BUY"

        base_order = {
            "rootOrderId": root_order_id,
            "symbol": symbol,
            "orderType": "IFDOCO",
            "timestamp": timestamp,
            "_dry_run": True,
        }

        if client_order_id:
            base_order["clientOrderId"] = client_order_id

        return [
            # 1次注文（新規エントリー）
            {
                **base_order,
                "orderId": order_id_1,
                "side": first_side,
                "executionType": first_execution_type,
                "settleType": "OPEN",
                "size": str(first_size),
                "price": first_price,
                "status": "WAITING",
            },
            # 2次注文（利確 - LIMIT）
            {
                **base_order,
                "orderId": order_id_2,
                "side": second_side,
                "executionType": "LIMIT",
                "settleType": "CLOSE",
                "size": str(second_size),
                "price": second_limit_price,
                "status": "WAITING",
            },
            # 2次注文（損切り - STOP）
            {
                **base_order,
                "orderId": order_id_3,
                "side": second_side,
                "executionType": "STOP",
                "settleType": "CLOSE",
                "size": str(second_size),
                "price": second_stop_price,
                "status": "WAITING",
            },
        ]

    def _simulate_ifd_order(
        self,
        symbol: str,
        first_side: str,
        first_execution_type: str,
        first_size: int,
        first_price: str,
        second_execution_type: str,
        second_size: int,
        second_price: str,
        client_order_id: Optional[str] = None,
    ) -> List[Dict]:
        """IFD注文のシミュレーション結果を生成"""
        import uuid

        root_order_id = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        order_id_1 = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        order_id_2 = f"DRY_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().isoformat()

        # 2次注文のサイドは1次注文の逆
        second_side = "SELL" if first_side == "BUY" else "BUY"

        base_order = {
            "rootOrderId": root_order_id,
            "symbol": symbol,
            "orderType": "IFD",
            "timestamp": timestamp,
            "_dry_run": True,
        }

        if client_order_id:
            base_order["clientOrderId"] = client_order_id

        return [
            # 1次注文（新規エントリー）
            {
                **base_order,
                "orderId": order_id_1,
                "side": first_side,
                "executionType": first_execution_type,
                "settleType": "OPEN",
                "size": str(first_size),
                "price": first_price,
                "status": "WAITING",
            },
            # 2次注文（決済）
            {
                **base_order,
                "orderId": order_id_2,
                "side": second_side,
                "executionType": second_execution_type,
                "settleType": "CLOSE",
                "size": str(second_size),
                "price": second_price,
                "status": "WAITING",
            },
        ]


# ============================================================
# ヘルパー関数
# ============================================================


def parse_kline_to_ohlcv(klines: List[Dict]) -> Dict[str, List[float]]:
    """
    ローソク足データをOHLCV形式に変換

    Args:
        klines: GMOコインAPIから取得したローソク足データ

    Returns:
        {
            "timestamp": [1618588800000, ...],
            "open": [141.365, ...],
            "high": [141.368, ...],
            "low": [141.360, ...],
            "close": [141.362, ...],
        }
    """
    return {
        "timestamp": [int(k["openTime"]) for k in klines],
        "open": [float(k["open"]) for k in klines],
        "high": [float(k["high"]) for k in klines],
        "low": [float(k["low"]) for k in klines],
        "close": [float(k["close"]) for k in klines],
    }
