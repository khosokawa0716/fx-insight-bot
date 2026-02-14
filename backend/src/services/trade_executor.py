"""
Trade Executor

シグナルに基づいて自動売買を実行するクラス
Phase 4: 自動売買機能
v2.0: AIロット決定 + IFDOCO注文
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from google.cloud import firestore

from .gmo_client import (
    AuthenticationError,
    GMOCoinClient,
    OrderError,
)
from .risk_manager import RiskManager
from .rule_engine import RuleEngine

logger = logging.getLogger(__name__)


@dataclass
class TradeConfig:
    """トレード設定（v2.0）"""

    # 取引対象
    symbols: List[str]

    # AIロット選択肢（通貨単位）
    lot_options: List[int] = field(default_factory=lambda: [0, 500, 1000, 1500])

    # リスク管理
    max_positions_per_symbol: int = 1
    max_total_positions: int = 1

    # 注文方式
    execution_type: str = "IFDOCO"

    # エントリーバッファ（pips）- IFDOCO 1次注文の指値バッファ
    entry_buffer_pips: float = 1.0


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
    トレード実行クラス（v2.0）

    テクニカル → AIロット決定 → リスクチェック → IFDOCO注文
    """

    def __init__(
        self,
        gmo_client: GMOCoinClient,
        rule_engine: RuleEngine,
        config: TradeConfig,
        risk_manager: Optional[RiskManager] = None,
        db: Optional[firestore.Client] = None,
        database_id: str = "(default)",
    ):
        """
        初期化

        Args:
            gmo_client: GMOコインクライアント
            rule_engine: ルールエンジン
            config: トレード設定
            risk_manager: リスクマネージャー（オプション）
            db: Firestoreクライアント（オプション）
            database_id: FirestoreデータベースID
        """
        self.gmo_client = gmo_client
        self.rule_engine = rule_engine
        self.config = config
        self.risk_manager = risk_manager
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

                # 実行された取引のみFirestoreに保存（SKIP/HOLDは個別に保存済み）
                if self.db and result.action in ("BUY", "SELL"):
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
        v2.0 取引実行フロー

        1. テクニカル判定 → buy/sell/hold
        2. hold → 終了
        3. AIロット決定 → 0なら終了（スキップログ記録）
        4. リスクチェック
        5. IFDOCO注文発注

        Args:
            symbol: 通貨ペア

        Returns:
            トレード結果
        """
        logger.info(f"Evaluating signal for {symbol}")

        # 1. シグナル生成（テクニカル + ニュースサマリー）
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
        news_summary = signal_data.get("news_summary", {})

        logger.info(
            f"Signal for {symbol}: {signal} (confidence: {confidence:.2%})"
        )

        # 2. hold → 終了
        if signal == "hold":
            return TradeResult(
                success=True,
                action="HOLD",
                symbol=symbol,
                size=0,
                reason=reason,
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

        # 3. AIロット決定
        lot, lot_reason = self.rule_engine.determine_lot(signal, news_summary)

        # AI決定をFirestoreに保存
        self.rule_engine.save_daily_ai_decision(
            symbol=symbol,
            signal=signal,
            lot=lot,
            lot_reason=lot_reason,
            news_summary=news_summary,
        )

        logger.info(f"AI lot decision: {lot} ({lot_reason})")

        # lot = 0 → スキップ（ログ記録）
        if lot == 0:
            self._save_skip_log(
                symbol=symbol,
                side=signal.upper(),
                signal_data=signal_data,
                lot_reason=lot_reason,
                news_summary=news_summary,
            )
            return TradeResult(
                success=True,
                action="SKIP",
                symbol=symbol,
                size=0,
                reason=f"AI skip: {lot_reason}",
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

        # 4. リスクチェック
        if self.risk_manager:
            risk_result = self.risk_manager.check_trade_allowed(
                symbol=symbol,
                side=signal.upper(),
                size=lot,
            )
            if not risk_result.can_trade:
                logger.info(f"Risk check failed: {risk_result.reason}")
                return TradeResult(
                    success=True,
                    action="SKIP",
                    symbol=symbol,
                    size=0,
                    reason=f"Risk check: {risk_result.reason}",
                    timestamp=datetime.now(),
                    dry_run=self.gmo_client.dry_run,
                )

        # ポジション数チェック
        can_trade, check_reason = self._can_open_position(symbol, signal.upper())
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

        # 5. IFDOCO注文発注
        return self._execute_ifdoco_order(
            symbol=symbol,
            side=signal.upper(),
            lot=lot,
            signal_data=signal_data,
            lot_reason=lot_reason,
        )

    def _execute_ifdoco_order(
        self,
        symbol: str,
        side: Literal["BUY", "SELL"],
        lot: int,
        signal_data: Dict,
        lot_reason: str,
    ) -> TradeResult:
        """
        IFDOCO注文を実行

        エントリー価格 = 現在価格 ± buffer（即約定を狙うLIMIT）
        SL = entry ∓ 40pips
        TP = entry ± 40pips

        Args:
            symbol: 通貨ペア
            side: 売買区分
            lot: ロット（通貨単位）
            signal_data: シグナルデータ
            lot_reason: ロット決定理由

        Returns:
            トレード結果
        """
        current_price = signal_data["technical"]["latest_price"]

        # エントリー・SL・TP価格を計算
        pip_value = 0.01 if symbol.endswith("_JPY") else 0.0001
        buffer = self.config.entry_buffer_pips * pip_value

        if side == "BUY":
            entry_price = current_price + buffer
        else:
            entry_price = current_price - buffer

        # SL/TP計算
        if self.risk_manager:
            sl_price = self.risk_manager.calculate_stop_loss_price(entry_price, side, symbol)
            tp_price = self.risk_manager.calculate_take_profit_price(entry_price, side, symbol)
        else:
            sl_distance = 40.0 * pip_value
            tp_distance = 40.0 * pip_value
            if side == "BUY":
                sl_price = entry_price - sl_distance
                tp_price = entry_price + tp_distance
            else:
                sl_price = entry_price + sl_distance
                tp_price = entry_price - tp_distance

        logger.info(
            f"IFDOCO order: {side} {lot} {symbol} "
            f"entry={entry_price:.3f} SL={sl_price:.3f} TP={tp_price:.3f}"
        )

        try:
            order_result = self.gmo_client.place_ifdoco_order(
                symbol=symbol,
                first_side=side,
                first_execution_type="LIMIT",
                first_size=lot,
                first_price=str(entry_price),
                second_size=lot,
                second_limit_price=str(tp_price),
                second_stop_price=str(sl_price),
            )

            # 注文IDの抽出（IFDOCO responseはdata配列）
            order_id = None
            if isinstance(order_result, dict):
                data = order_result.get("data", [])
                if data and isinstance(data, list):
                    order_id = data[0].get("orderId")
                if not order_id:
                    order_id = order_result.get("orderId")

            trade_reason = (
                f"{signal_data.get('reason', '')} | "
                f"lot={lot} ({lot_reason})"
            )

            return TradeResult(
                success=True,
                action=side,
                symbol=symbol,
                size=lot,
                order_id=order_id,
                reason=trade_reason,
                timestamp=datetime.now(),
                dry_run=order_result.get("_dry_run", False),
            )

        except (AuthenticationError, OrderError) as e:
            logger.error(f"IFDOCO order failed for {symbol}: {e}")
            return TradeResult(
                success=False,
                action=side,
                symbol=symbol,
                size=lot,
                reason=f"IFDOCO order failed: {str(e)}",
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

    def _save_skip_log(
        self,
        symbol: str,
        side: str,
        signal_data: Dict,
        lot_reason: str,
        news_summary: Dict,
    ) -> Optional[str]:
        """
        AI見送りログをFirestoreに保存

        Args:
            symbol: 通貨ペア
            side: テクニカルが出した方向
            signal_data: シグナルデータ
            lot_reason: スキップ理由
            news_summary: ニュースサマリー

        Returns:
            ドキュメントID
        """
        if not self.db:
            return None

        try:
            now = datetime.now()
            doc_id = f"skipped_{now.strftime('%Y%m%d_%H%M%S')}_{symbol}"

            doc_data = {
                "trade_id": doc_id,
                "symbol": symbol,
                "side": side,
                "used_lot": 0,
                "skip_reason": "AI_FUNDAMENTAL_OPPOSE",
                "lot_reason": lot_reason,
                "ai_decision": {
                    "avg_sentiment": news_summary.get("avg_sentiment", 0.0),
                    "avg_impact": news_summary.get("avg_impact", 0.0),
                    "news_count": news_summary.get("count", 0),
                    "lot_reason": lot_reason,
                },
                "technical_score": {
                    "confidence": signal_data.get("confidence", 0.0),
                },
                "baseline_pnl": None,
                "created_at": now,
                "dry_run": self.gmo_client.dry_run,
            }

            self.db.collection("trades").document(doc_id).set(doc_data)
            logger.info(f"Skip log saved: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to save skip log: {e}")
            return None

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
