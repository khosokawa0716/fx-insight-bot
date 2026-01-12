"""
Technical Analyzer Service

テクニカル指標を計算するサービス
MA（移動平均）、RSI、MACDを計算します。

Note: pandas-taがPython 3.12以上を要求するため、自前実装を使用
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.services.gmo_client import GMOCoinClient, parse_kline_to_ohlcv

logger = logging.getLogger(__name__)


class TechnicalAnalyzerError(Exception):
    """TechnicalAnalyzer基底例外"""

    pass


class InsufficientDataError(TechnicalAnalyzerError):
    """データ不足エラー"""

    pass


class TechnicalAnalyzer:
    """
    テクニカル指標分析サービス

    GMOコインからローソク足を取得し、テクニカル指標を計算します。
    """

    def __init__(self, gmo_client: Optional[GMOCoinClient] = None):
        """
        初期化

        Args:
            gmo_client: GMOコインクライアント（省略時は自動生成）
        """
        self.gmo_client = gmo_client or GMOCoinClient()
        logger.info("TechnicalAnalyzer initialized")

    def get_indicators(
        self,
        symbol: str,
        interval: str = "1hour",
        days: int = 7,
        price_type: str = "ASK",
    ) -> Dict:
        """
        テクニカル指標を計算

        Args:
            symbol: 通貨ペア（例: USD_JPY）
            interval: 時間足（デフォルト: 1hour）
            days: 取得日数（デフォルト: 7日）
            price_type: BID or ASK（デフォルト: ASK）

        Returns:
            テクニカル指標の辞書
            {
                "symbol": "USD_JPY",
                "latest_price": 157.698,
                "ma": {...},
                "rsi": {...},
                "macd": {...},
                "trend": "up" or "down",
                "momentum": "bullish" or "bearish" or "neutral"
            }

        Raises:
            InsufficientDataError: データが不足している場合
            TechnicalAnalyzerError: その他のエラー
        """
        try:
            logger.info(f"Calculating indicators: {symbol} {interval} ({days} days)")

            # ローソク足取得
            klines = self.gmo_client.get_klines_range(
                symbol=symbol, interval=interval, days=days, price_type=price_type
            )

            if not klines:
                raise InsufficientDataError(f"No data available for {symbol}")

            if len(klines) < 50:
                raise InsufficientDataError(
                    f"Insufficient data: {len(klines)} bars (need at least 50)"
                )

            # OHLCV形式に変換
            ohlcv = parse_kline_to_ohlcv(klines)

            # DataFrameに変換
            df = pd.DataFrame(ohlcv)

            # テクニカル指標計算
            ma_data = self._calculate_ma(df)
            rsi_data = self._calculate_rsi(df)
            macd_data = self._calculate_macd(df)

            # トレンド判定
            trend = self._determine_trend(ma_data)

            # モメンタム判定
            momentum = self._determine_momentum(rsi_data, macd_data)

            # 結果をまとめる
            result = {
                "symbol": symbol,
                "interval": interval,
                "data_count": len(klines),
                "latest_price": float(df["close"].iloc[-1]),
                "ma": ma_data,
                "rsi": rsi_data,
                "macd": macd_data,
                "trend": trend,
                "momentum": momentum,
            }

            logger.info(
                f"Indicators calculated: trend={trend}, momentum={momentum}, "
                f"latest_price={result['latest_price']:.3f}"
            )

            return result

        except InsufficientDataError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate indicators: {e}")
            raise TechnicalAnalyzerError(f"Failed to calculate indicators: {e}")

    def _calculate_ma(self, df: pd.DataFrame) -> Dict:
        """
        移動平均（MA）を計算

        Args:
            df: OHLCVデータフレーム

        Returns:
            {
                "ma20": 157.5,
                "ma50": 156.8,
                "ma20_above_ma50": True
            }
        """
        # SMA（単純移動平均）を計算
        ma20 = df["close"].rolling(window=20).mean().iloc[-1]
        ma50 = df["close"].rolling(window=50).mean().iloc[-1]

        return {
            "ma20": round(float(ma20), 3),
            "ma50": round(float(ma50), 3),
            "ma20_above_ma50": ma20 > ma50,
        }

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """
        RSI（相対力指数）を計算

        Args:
            df: OHLCVデータフレーム
            period: 期間（デフォルト: 14）

        Returns:
            {
                "rsi": 65.5,
                "overbought": False,  # 70以上
                "oversold": False,    # 30以下
            }
        """
        # 価格差分を計算
        delta = df["close"].diff()

        # 上昇・下降を分離
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 平均上昇・下降を計算
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # RS（相対力）を計算
        rs = avg_gain / avg_loss

        # RSIを計算
        rsi = 100 - (100 / (1 + rs))

        rsi_value = float(rsi.iloc[-1])

        return {
            "rsi": round(rsi_value, 2),
            "overbought": rsi_value >= 70,
            "oversold": rsi_value <= 30,
        }

    def _calculate_macd(
        self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Dict:
        """
        MACD（移動平均収束拡散法）を計算

        Args:
            df: OHLCVデータフレーム
            fast: 短期EMA期間（デフォルト: 12）
            slow: 長期EMA期間（デフォルト: 26）
            signal: シグナル線期間（デフォルト: 9）

        Returns:
            {
                "macd": 0.15,
                "macd_signal": 0.12,
                "macd_histogram": 0.03,
                "bullish_crossover": True
            }
        """
        # EMA（指数移動平均）を計算
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

        # MACD線を計算
        macd_line = ema_fast - ema_slow

        # シグナル線を計算
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()

        # ヒストグラムを計算
        histogram = macd_line - signal_line

        # 最新値を取得
        macd = float(macd_line.iloc[-1])
        macd_signal = float(signal_line.iloc[-1])
        macd_histogram = float(histogram.iloc[-1])

        # クロスオーバー判定（前の値と比較）
        prev_histogram = float(histogram.iloc[-2])
        bullish_crossover = prev_histogram < 0 and macd_histogram > 0
        bearish_crossover = prev_histogram > 0 and macd_histogram < 0

        return {
            "macd": round(macd, 4),
            "macd_signal": round(macd_signal, 4),
            "macd_histogram": round(macd_histogram, 4),
            "bullish_crossover": bullish_crossover,
            "bearish_crossover": bearish_crossover,
        }

    def _determine_trend(self, ma_data: Dict) -> str:
        """
        トレンドを判定

        Args:
            ma_data: 移動平均データ

        Returns:
            "up" or "down"
        """
        if ma_data["ma20_above_ma50"]:
            return "up"
        else:
            return "down"

    def _determine_momentum(self, rsi_data: Dict, macd_data: Dict) -> str:
        """
        モメンタムを判定

        Args:
            rsi_data: RSIデータ
            macd_data: MACDデータ

        Returns:
            "bullish" or "bearish" or "neutral"
        """
        # 強気シグナル
        if macd_data["bullish_crossover"] or (
            rsi_data["oversold"] and macd_data["macd_histogram"] > 0
        ):
            return "bullish"

        # 弱気シグナル
        if macd_data["bearish_crossover"] or (
            rsi_data["overbought"] and macd_data["macd_histogram"] < 0
        ):
            return "bearish"

        # 中立
        return "neutral"

    def get_multiple_indicators(
        self, symbols: List[str], interval: str = "1hour", days: int = 7
    ) -> Dict[str, Dict]:
        """
        複数通貨ペアのテクニカル指標を取得

        Args:
            symbols: 通貨ペアのリスト
            interval: 時間足
            days: 取得日数

        Returns:
            {
                "USD_JPY": {...},
                "EUR_JPY": {...}
            }
        """
        results = {}

        for symbol in symbols:
            try:
                indicators = self.get_indicators(symbol, interval, days)
                results[symbol] = indicators
            except Exception as e:
                logger.error(f"Failed to get indicators for {symbol}: {e}")
                results[symbol] = {"error": str(e)}

        return results
