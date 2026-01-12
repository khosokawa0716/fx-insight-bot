"""
Rule Engine Service

ニュース分析結果とテクニカル指標を統合してトレードシグナルを生成します。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal

from src.models.firestore import NewsEvent
from src.services.technical_analyzer import TechnicalAnalyzer
from src.utils.firestore_client import get_db

logger = logging.getLogger(__name__)

# Type Aliases
TradeSignal = Literal["buy", "sell", "hold"]


class RuleEngineError(Exception):
    """RuleEngine基底例外"""

    pass


class RuleEngine:
    """
    ルールエンジン

    ニュース分析とテクニカル指標を統合してトレードシグナルを生成します。
    """

    def __init__(
        self,
        technical_analyzer: Optional[TechnicalAnalyzer] = None,
        rule_version: str = "v1.0",
    ):
        """
        初期化

        Args:
            technical_analyzer: テクニカルアナライザー（省略時は自動生成）
            rule_version: ルールバージョン
        """
        self.technical_analyzer = technical_analyzer or TechnicalAnalyzer()
        self.rule_version = rule_version
        self.db = get_db()
        logger.info(f"RuleEngine initialized (version: {rule_version})")

    def generate_signal(
        self,
        symbol: str,
        interval: str = "1hour",
        days: int = 7,
        lookback_hours: int = 24,
    ) -> Dict:
        """
        トレードシグナルを生成

        Args:
            symbol: 通貨ペア（例: USD_JPY）
            interval: 時間足（デフォルト: 1hour）
            days: テクニカル指標計算用の日数（デフォルト: 7日）
            lookback_hours: ニュース取得時間（デフォルト: 24時間）

        Returns:
            トレードシグナルの辞書
            {
                "symbol": "USD_JPY",
                "signal": "buy" or "sell" or "hold",
                "confidence": 0.0-1.0,
                "timestamp": datetime,
                "technical": {...},
                "news_summary": {...},
                "reason": "...",
                "rule_version": "v1.0"
            }

        Raises:
            RuleEngineError: シグナル生成エラー
        """
        try:
            logger.info(f"Generating signal: {symbol} (lookback: {lookback_hours}h)")

            # 1. テクニカル指標を取得
            technical = self.technical_analyzer.get_indicators(
                symbol=symbol, interval=interval, days=days
            )

            # 2. 最近のニュースを取得
            news_list = self._fetch_recent_news(
                symbol=symbol, lookback_hours=lookback_hours
            )

            # 3. ニュース分析サマリーを作成
            news_summary = self._summarize_news(news_list, symbol)

            # 4. 統合判定
            signal, confidence, reason = self._integrate_signals(
                technical=technical, news_summary=news_summary, symbol=symbol
            )

            result = {
                "symbol": symbol,
                "signal": signal,
                "confidence": round(confidence, 3),
                "timestamp": datetime.utcnow(),
                "technical": technical,
                "news_summary": news_summary,
                "reason": reason,
                "rule_version": self.rule_version,
            }

            logger.info(
                f"Signal generated: {signal.upper()} (confidence: {confidence:.2f}) - {reason}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to generate signal: {e}")
            raise RuleEngineError(f"Failed to generate signal: {e}")

    def _fetch_recent_news(self, symbol: str, lookback_hours: int) -> List[NewsEvent]:
        """
        最近のニュースをFirestoreから取得

        Args:
            symbol: 通貨ペア（USD_JPY or EUR_JPY）
            lookback_hours: 取得時間（時間）

        Returns:
            NewsEventのリスト
        """
        try:
            # 通貨ペアに応じてimpactフィールドを選択
            impact_field = (
                "impact_usdjpy" if symbol == "USD_JPY" else "impact_eurjpy"
            )

            # 過去N時間のニュースを取得
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)

            # Firestoreクエリ
            news_ref = self.db.collection("news")
            query = (
                news_ref.where("collected_at", ">=", cutoff_time)
                .where(impact_field, ">=", 3)  # インパクト3以上
                .order_by("collected_at", direction=firestore.Query.DESCENDING)
                .limit(10)
            )

            docs = query.stream()
            news_list = []

            for doc in docs:
                data = doc.to_dict()
                # NewsEventに変換
                news_event = NewsEvent(**data)
                news_list.append(news_event)

            logger.info(
                f"Fetched {len(news_list)} news items for {symbol} (last {lookback_hours}h)"
            )

            return news_list

        except Exception as e:
            logger.warning(f"Failed to fetch news from Firestore: {e}")
            return []

    def _summarize_news(self, news_list: List[NewsEvent], symbol: str) -> Dict:
        """
        ニュースリストを分析してサマリーを作成

        Args:
            news_list: ニュースイベントのリスト
            symbol: 通貨ペア

        Returns:
            ニュースサマリー
            {
                "count": 5,
                "avg_sentiment": 0.4,
                "avg_impact": 3.8,
                "bullish_count": 3,
                "bearish_count": 1,
                "neutral_count": 1,
                "signals": {"BUY_CANDIDATE": 2, "SELL_CANDIDATE": 1, ...}
            }
        """
        if not news_list:
            return {
                "count": 0,
                "avg_sentiment": 0.0,
                "avg_impact": 0.0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "signals": {},
            }

        # 通貨ペアに応じてimpactを選択
        impact_field = "impact_usdjpy" if symbol == "USD_JPY" else "impact_eurjpy"

        # 集計
        total_sentiment = sum(news.sentiment for news in news_list)
        total_impact = sum(getattr(news, impact_field) for news in news_list)

        bullish_count = sum(1 for news in news_list if news.sentiment > 0)
        bearish_count = sum(1 for news in news_list if news.sentiment < 0)
        neutral_count = sum(1 for news in news_list if news.sentiment == 0)

        # シグナル集計
        signals = {}
        for news in news_list:
            signal = news.signal
            signals[signal] = signals.get(signal, 0) + 1

        return {
            "count": len(news_list),
            "avg_sentiment": round(total_sentiment / len(news_list), 2),
            "avg_impact": round(total_impact / len(news_list), 2),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "signals": signals,
        }

    def _integrate_signals(
        self, technical: Dict, news_summary: Dict, symbol: str
    ) -> tuple[TradeSignal, float, str]:
        """
        テクニカル指標とニュース分析を統合してシグナルを判定

        Args:
            technical: テクニカル指標
            news_summary: ニュースサマリー
            symbol: 通貨ペア

        Returns:
            (signal, confidence, reason)
            signal: "buy" or "sell" or "hold"
            confidence: 0.0-1.0
            reason: 判定理由
        """
        # テクニカル分析から判定
        tech_trend = technical["trend"]  # "up" or "down"
        tech_momentum = technical["momentum"]  # "bullish" or "bearish" or "neutral"
        rsi = technical["rsi"]["rsi"]
        rsi_overbought = technical["rsi"]["overbought"]
        rsi_oversold = technical["rsi"]["oversold"]

        # ニュース分析から判定
        news_sentiment = news_summary["avg_sentiment"]
        news_impact = news_summary["avg_impact"]
        news_count = news_summary["count"]
        bullish_news = news_summary["bullish_count"]
        bearish_news = news_summary["bearish_count"]

        # 信頼度計算の基礎
        confidence = 0.0
        reasons = []

        # === 買いシグナル判定 ===
        buy_score = 0
        sell_score = 0

        # テクニカル: 上昇トレンド + 強気モメンタム
        if tech_trend == "up" and tech_momentum == "bullish":
            buy_score += 3
            reasons.append("テクニカル: 上昇トレンド + 強気モメンタム")
        elif tech_trend == "up":
            buy_score += 1
            reasons.append("テクニカル: 上昇トレンド")

        # テクニカル: RSI売られすぎ（買いチャンス）
        if rsi_oversold:
            buy_score += 2
            reasons.append(f"RSI売られすぎ ({rsi:.1f})")

        # ニュース: 強気センチメント
        if news_count > 0:
            if news_sentiment > 0.5 and news_impact >= 3:
                buy_score += 3
                reasons.append(
                    f"ニュース強気 (sentiment: {news_sentiment:.1f}, impact: {news_impact:.1f})"
                )
            elif news_sentiment > 0:
                buy_score += 1
                reasons.append(f"ニュース小幅ポジティブ (sentiment: {news_sentiment:.1f})")

        # === 売りシグナル判定 ===

        # テクニカル: 下降トレンド + 弱気モメンタム
        if tech_trend == "down" and tech_momentum == "bearish":
            sell_score += 3
            reasons.append("テクニカル: 下降トレンド + 弱気モメンタム")
        elif tech_trend == "down":
            sell_score += 1
            reasons.append("テクニカル: 下降トレンド")

        # テクニカル: RSI買われすぎ（売りチャンス）
        if rsi_overbought:
            sell_score += 2
            reasons.append(f"RSI買われすぎ ({rsi:.1f})")

        # ニュース: 弱気センチメント
        if news_count > 0:
            if news_sentiment < -0.5 and news_impact >= 3:
                sell_score += 3
                reasons.append(
                    f"ニュース弱気 (sentiment: {news_sentiment:.1f}, impact: {news_impact:.1f})"
                )
            elif news_sentiment < 0:
                sell_score += 1
                reasons.append(f"ニュース小幅ネガティブ (sentiment: {news_sentiment:.1f})")

        # === 最終判定 ===

        # 買いシグナル
        if buy_score >= 4 and sell_score <= 1:
            signal = "buy"
            confidence = min(0.3 + (buy_score * 0.15), 1.0)
            reason = " | ".join(reasons)

        # 売りシグナル
        elif sell_score >= 4 and buy_score <= 1:
            signal = "sell"
            confidence = min(0.3 + (sell_score * 0.15), 1.0)
            reason = " | ".join(reasons)

        # 様子見（中立）
        else:
            signal = "hold"
            confidence = 0.5
            reason = f"買い要因 ({buy_score}pt) vs 売り要因 ({sell_score}pt) - 判断保留"

            # 中立の場合も理由を追加
            if reasons:
                reason += " | " + " | ".join(reasons[:2])  # 最初の2つの理由を追加

        return signal, confidence, reason

    def generate_multiple_signals(
        self, symbols: List[str], interval: str = "1hour", lookback_hours: int = 24
    ) -> Dict[str, Dict]:
        """
        複数通貨ペアのシグナルを生成

        Args:
            symbols: 通貨ペアのリスト
            interval: 時間足
            lookback_hours: ニュース取得時間

        Returns:
            {
                "USD_JPY": {...},
                "EUR_JPY": {...}
            }
        """
        results = {}

        for symbol in symbols:
            try:
                signal = self.generate_signal(
                    symbol=symbol, interval=interval, lookback_hours=lookback_hours
                )
                results[symbol] = signal
            except Exception as e:
                logger.error(f"Failed to generate signal for {symbol}: {e}")
                results[symbol] = {"error": str(e)}

        return results

    def save_signal_to_firestore(self, signal: Dict) -> str:
        """
        シグナルをFirestoreに保存

        Args:
            signal: generate_signal()の戻り値

        Returns:
            保存したドキュメントID
        """
        try:
            # シグナルコレクションに保存
            signals_ref = self.db.collection("signals")

            # ドキュメントID生成（タイムスタンプ + 通貨ペア）
            timestamp_str = signal["timestamp"].strftime("%Y%m%d_%H%M%S")
            doc_id = f"{timestamp_str}_{signal['symbol']}"

            # numpy型をPython native型に変換（Firestore互換性のため）
            signal_clean = self._convert_to_native_types(signal)

            # Firestoreに保存
            signals_ref.document(doc_id).set(signal_clean)

            logger.info(f"Signal saved to Firestore: {doc_id}")

            return doc_id

        except Exception as e:
            logger.error(f"Failed to save signal to Firestore: {e}")
            raise RuleEngineError(f"Failed to save signal: {e}")

    def _convert_to_native_types(self, data):
        """
        numpy型をPython native型に再帰的に変換

        Args:
            data: 変換対象のデータ（dict, list, or primitive）

        Returns:
            Python native型に変換されたデータ
        """
        import numpy as np

        if isinstance(data, dict):
            return {key: self._convert_to_native_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_native_types(item) for item in data]
        elif isinstance(data, np.bool_):
            return bool(data)
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        else:
            return data


# Firestoreモジュールのインポート（_fetch_recent_newsで使用）
from google.cloud import firestore
