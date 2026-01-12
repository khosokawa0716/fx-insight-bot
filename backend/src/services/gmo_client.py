"""
GMO Coin Client

GMOコインのREST APIと通信するためのクライアントクラス
Phase 3: ローソク足取得（公開API）
Phase 4: 注文・ポジション管理（プライベートAPI）
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

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
    ):
        """
        初期化

        Args:
            api_key: APIキー（プライベートAPI用、Phase 4で使用）
            api_secret: APIシークレット（プライベートAPI用、Phase 4で使用）
            timeout: タイムアウト（秒）
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # レート制限管理
        self._last_request_time = 0.0
        self._request_interval = 1.0 / self.RATE_LIMIT_GET  # 約0.17秒

        logger.info("GMOCoinClient initialized (Public API mode)")

    def _wait_for_rate_limit(self):
        """レート制限のための待機"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self._request_interval:
            wait_time = self._request_interval - elapsed
            logger.debug(f"Rate limit wait: {wait_time:.2f}s")
            time.sleep(wait_time)

        self._last_request_time = time.time()

    def _request(
        self, method: str, endpoint: str, params: Optional[Dict] = None
    ) -> Dict:
        """
        HTTPリクエスト実行（リトライ付き）

        Args:
            method: HTTPメソッド（GET, POST）
            endpoint: エンドポイントURL
            params: クエリパラメータ

        Returns:
            APIレスポンス

        Raises:
            APIError: API呼び出しエラー
            RateLimitError: レート制限エラー
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                # レート制限待機
                self._wait_for_rate_limit()

                # リクエスト実行
                logger.debug(f"Request: {method} {endpoint} (attempt {attempt})")

                if method == "GET":
                    response = requests.get(
                        endpoint, params=params, timeout=self.timeout
                    )
                else:
                    raise NotImplementedError(f"Method {method} not implemented yet")

                # ステータスコードチェック
                if response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")

                response.raise_for_status()

                # JSONパース
                data = response.json()

                # GMOコインAPIのエラーチェック
                if "status" in data and data["status"] != 0:
                    error_msg = data.get("messages", ["Unknown error"])
                    raise APIError(f"API Error: {error_msg}")

                logger.debug(f"Request successful: {endpoint}")
                return data

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
                    raise APIError(f"Request failed after {self.max_retries} attempts: {e}")

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

    def place_order(self):
        """注文発注（Phase 4で実装）"""
        raise NotImplementedError("Private API not implemented yet (Phase 4)")

    def get_positions(self):
        """ポジション照会（Phase 4で実装）"""
        raise NotImplementedError("Private API not implemented yet (Phase 4)")

    def close_position(self):
        """ポジション決済（Phase 4で実装）"""
        raise NotImplementedError("Private API not implemented yet (Phase 4)")


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
