"""
Trade Executor

シグナルに基づいて自動売買を実行するクラス
Phase 4: 自動売買機能
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from google.cloud import firestore

from .gmo_client import (
    AuthenticationError,
    GMOCoinClient,
    OrderError,
)
from .rule_engine import RuleEngine

logger = logging.getLogger(__name__)


@dataclass
class TradeConfig:
    """トレード設定"""

    # 取引対象
    symbols: List[str]

    # ポジションサイズ（1 = 1万通貨）
    default_size: int = 1

    # リスク管理
    max_positions_per_symbol: int = 3  # 1通貨ペアあたりの最大ポジション数
    max_total_positions: int = 5  # 全体の最大ポジション数

    # シグナル閾値
    min_confidence: float = 0.7  # 最低信頼度（これ以上でのみ取引）

    # 取引タイプ
    execution_type: Literal["MARKET", "LIMIT"] = "MARKET"


@dataclass
class TradeResult:
    """トレード結果"""

    success: bool
    action: Literal["BUY", "SELL", "HOLD", "CLOSE", "SKIP"]
    symbol: str
    size: int
    order_id: Optional[str] = None
    reason: str = ""
    timestamp: Optional[datetime] = None
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "success": self.success,
            "action": self.action,
            "symbol": self.symbol,
            "size": self.size,
            "order_id": self.order_id,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "dry_run": self.dry_run,
        }


class TradeExecutor:
    """
    トレード実行クラス

    ルールエンジンからのシグナルに基づいて自動売買を実行
    """

    def __init__(
        self,
        gmo_client: GMOCoinClient,
        rule_engine: RuleEngine,
        config: TradeConfig,
        db: Optional[firestore.Client] = None,
        database_id: str = "(default)",
    ):
        """
        初期化

        Args:
            gmo_client: GMOコインクライアント
            rule_engine: ルールエンジン
            config: トレード設定
            db: Firestoreクライアント（オプション）
            database_id: FirestoreデータベースID
        """
        self.gmo_client = gmo_client
        self.rule_engine = rule_engine
        self.config = config
        self.database_id = database_id

        # Firestore
        if db:
            self.db = db
        else:
            try:
                self.db = firestore.Client(database=database_id)
            except Exception as e:
                logger.warning(f"Firestore initialization failed: {e}")
                self.db = None

        logger.info(
            f"TradeExecutor initialized: symbols={config.symbols}, "
            f"dry_run={gmo_client.dry_run}"
        )

    def execute_signals(self) -> List[TradeResult]:
        """
        全シンボルのシグナルを評価し、トレードを実行

        Returns:
            トレード結果のリスト
        """
        results = []

        for symbol in self.config.symbols:
            try:
                result = self.execute_signal_for_symbol(symbol)
                results.append(result)

                # 結果をFirestoreに保存
                if self.db:
                    self._save_trade_result(result)

            except Exception as e:
                logger.error(f"Error executing signal for {symbol}: {e}")
                results.append(
                    TradeResult(
                        success=False,
                        action="SKIP",
                        symbol=symbol,
                        size=0,
                        reason=f"Error: {str(e)}",
                        timestamp=datetime.now(),
                        dry_run=self.gmo_client.dry_run,
                    )
                )

        return results

    def execute_signal_for_symbol(self, symbol: str) -> TradeResult:
        """
        特定シンボルのシグナルを評価し、トレードを実行

        Args:
            symbol: 通貨ペア

        Returns:
            トレード結果
        """
        logger.info(f"Evaluating signal for {symbol}")

        # シグナル生成
        signal_data = self.rule_engine.generate_signal(symbol)

        if not signal_data:
            return TradeResult(
                success=False,
                action="SKIP",
                symbol=symbol,
                size=0,
                reason="Failed to generate signal",
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

        signal = signal_data.get("signal", "hold")
        confidence = signal_data.get("confidence", 0.0)
        reason = signal_data.get("reason", "")

        logger.info(
            f"Signal for {symbol}: {signal} (confidence: {confidence:.2%})"
        )

        # 信頼度チェック
        if confidence < self.config.min_confidence:
            return TradeResult(
                success=True,
                action="HOLD",
                symbol=symbol,
                size=0,
                reason=f"Confidence too low: {confidence:.2%} < {self.config.min_confidence:.2%}",
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

        # シグナルに応じたアクション
        if signal == "buy":
            return self._execute_buy(symbol, confidence, reason)
        elif signal == "sell":
            return self._execute_sell(symbol, confidence, reason)
        else:
            return TradeResult(
                success=True,
                action="HOLD",
                symbol=symbol,
                size=0,
                reason=reason,
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

    def _execute_buy(
        self, symbol: str, confidence: float, signal_reason: str
    ) -> TradeResult:
        """
        買い注文を実行

        Args:
            symbol: 通貨ペア
            confidence: シグナル信頼度
            signal_reason: シグナル理由

        Returns:
            トレード結果
        """
        # ポジション数チェック
        can_trade, check_reason = self._can_open_position(symbol, "BUY")
        if not can_trade:
            return TradeResult(
                success=True,
                action="SKIP",
                symbol=symbol,
                size=0,
                reason=check_reason,
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

        # 注文実行
        try:
            order_result = self.gmo_client.place_order(
                symbol=symbol,
                side="BUY",
                size=self.config.default_size,
                execution_type=self.config.execution_type,
            )

            return TradeResult(
                success=True,
                action="BUY",
                symbol=symbol,
                size=self.config.default_size,
                order_id=order_result.get("orderId"),
                reason=signal_reason,
                timestamp=datetime.now(),
                dry_run=order_result.get("_dry_run", False),
            )

        except (AuthenticationError, OrderError) as e:
            logger.error(f"Buy order failed for {symbol}: {e}")
            return TradeResult(
                success=False,
                action="BUY",
                symbol=symbol,
                size=self.config.default_size,
                reason=f"Order failed: {str(e)}",
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

    def _execute_sell(
        self, symbol: str, confidence: float, signal_reason: str
    ) -> TradeResult:
        """
        売り注文を実行

        Args:
            symbol: 通貨ペア
            confidence: シグナル信頼度
            signal_reason: シグナル理由

        Returns:
            トレード結果
        """
        # ポジション数チェック
        can_trade, check_reason = self._can_open_position(symbol, "SELL")
        if not can_trade:
            return TradeResult(
                success=True,
                action="SKIP",
                symbol=symbol,
                size=0,
                reason=check_reason,
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

        # 注文実行
        try:
            order_result = self.gmo_client.place_order(
                symbol=symbol,
                side="SELL",
                size=self.config.default_size,
                execution_type=self.config.execution_type,
            )

            return TradeResult(
                success=True,
                action="SELL",
                symbol=symbol,
                size=self.config.default_size,
                order_id=order_result.get("orderId"),
                reason=signal_reason,
                timestamp=datetime.now(),
                dry_run=order_result.get("_dry_run", False),
            )

        except (AuthenticationError, OrderError) as e:
            logger.error(f"Sell order failed for {symbol}: {e}")
            return TradeResult(
                success=False,
                action="SELL",
                symbol=symbol,
                size=self.config.default_size,
                reason=f"Order failed: {str(e)}",
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

    def _can_open_position(
        self, symbol: str, side: Literal["BUY", "SELL"]
    ) -> tuple[bool, str]:
        """
        新規ポジションを開けるかチェック

        Args:
            symbol: 通貨ペア
            side: 売買区分

        Returns:
            (取引可能か, 理由)
        """
        # DRY-RUNモードではスキップ
        if self.gmo_client.dry_run:
            return True, "DRY-RUN mode"

        try:
            # 現在のポジション取得
            positions = self.gmo_client.get_positions(symbol)
            total_positions = self.gmo_client.get_positions()

            # 1通貨ペアあたりの制限
            symbol_positions = len(positions)
            if symbol_positions >= self.config.max_positions_per_symbol:
                return (
                    False,
                    f"Max positions per symbol reached: {symbol_positions}/{self.config.max_positions_per_symbol}",
                )

            # 全体の制限
            if len(total_positions) >= self.config.max_total_positions:
                return (
                    False,
                    f"Max total positions reached: {len(total_positions)}/{self.config.max_total_positions}",
                )

            return True, "OK"

        except AuthenticationError:
            # 認証エラーの場合は取引不可
            return False, "Authentication required"
        except Exception as e:
            logger.warning(f"Position check failed: {e}")
            # エラーの場合は安全のため取引不可
            return False, f"Position check failed: {str(e)}"

    def close_positions_for_symbol(
        self, symbol: str, side: Optional[Literal["BUY", "SELL"]] = None
    ) -> List[TradeResult]:
        """
        指定シンボルのポジションを決済

        Args:
            symbol: 通貨ペア
            side: 決済対象のサイド（省略時は全ポジション）

        Returns:
            決済結果のリスト
        """
        results = []

        try:
            positions = self.gmo_client.get_positions(symbol)

            for position in positions:
                pos_side = position.get("side")
                if side and pos_side != side:
                    continue

                # 反対売買で決済
                close_side = "SELL" if pos_side == "BUY" else "BUY"
                pos_size = int(position.get("size", 1))
                pos_id = position.get("positionId")

                try:
                    close_result = self.gmo_client.close_position(
                        position_id=pos_id,
                        symbol=symbol,
                        side=close_side,
                        size=pos_size,
                    )

                    result = TradeResult(
                        success=True,
                        action="CLOSE",
                        symbol=symbol,
                        size=pos_size,
                        order_id=close_result.get("orderId"),
                        reason=f"Closed position {pos_id}",
                        timestamp=datetime.now(),
                        dry_run=close_result.get("_dry_run", False),
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Failed to close position {pos_id}: {e}")
                    results.append(
                        TradeResult(
                            success=False,
                            action="CLOSE",
                            symbol=symbol,
                            size=pos_size,
                            reason=f"Failed to close: {str(e)}",
                            timestamp=datetime.now(),
                            dry_run=self.gmo_client.dry_run,
                        )
                    )

        except Exception as e:
            logger.error(f"Failed to get positions for {symbol}: {e}")
            results.append(
                TradeResult(
                    success=False,
                    action="CLOSE",
                    symbol=symbol,
                    size=0,
                    reason=f"Failed to get positions: {str(e)}",
                    timestamp=datetime.now(),
                    dry_run=self.gmo_client.dry_run,
                )
            )

        return results

    def _save_trade_result(self, result: TradeResult) -> Optional[str]:
        """
        トレード結果をFirestoreに保存

        Args:
            result: トレード結果

        Returns:
            ドキュメントID
        """
        if not self.db:
            return None

        try:
            trades_ref = self.db.collection("trades")
            timestamp = result.timestamp or datetime.now()
            doc_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{result.symbol}"

            doc_data = result.to_dict()
            doc_data["created_at"] = timestamp

            trades_ref.document(doc_id).set(doc_data)
            logger.info(f"Trade result saved: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to save trade result: {e}")
            return None

    def get_current_positions(self) -> Dict[str, List[Dict]]:
        """
        現在のポジション状況を取得

        Returns:
            シンボルごとのポジションリスト
        """
        positions_by_symbol: Dict[str, List[Dict]] = {}

        for symbol in self.config.symbols:
            try:
                positions = self.gmo_client.get_positions(symbol)
                positions_by_symbol[symbol] = positions
            except Exception as e:
                logger.warning(f"Failed to get positions for {symbol}: {e}")
                positions_by_symbol[symbol] = []

        return positions_by_symbol

    def get_account_summary(self) -> Dict[str, Any]:
        """
        口座サマリーを取得

        Returns:
            口座情報と現在のポジション状況
        """
        try:
            assets = self.gmo_client.get_account_assets()
        except AuthenticationError:
            assets = {"error": "Authentication required"}
        except Exception as e:
            assets = {"error": str(e)}

        positions = self.get_current_positions()

        total_positions = sum(len(p) for p in positions.values())

        return {
            "account": assets,
            "positions": positions,
            "total_positions": total_positions,
            "max_positions": self.config.max_total_positions,
            "dry_run": self.gmo_client.dry_run,
        }
