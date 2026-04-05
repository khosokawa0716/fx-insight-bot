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

                # BUY/SELLの保存は_execute_ifdoco_order内で実施済み

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

        # 2. hold → ログ記録して終了
        if signal == "hold":
            now = datetime.now()
            self._save_hold_log(
                symbol=symbol,
                signal_data=signal_data,
                reason=reason,
                timestamp=now,
            )
            return TradeResult(
                success=True,
                action="HOLD",
                symbol=symbol,
                size=0,
                reason=reason,
                timestamp=now,
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

        # lot = 0 → スキップログ記録して終了
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
                reason=f"AI lot=0: {lot_reason}",
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

        # 価格の小数点桁数を調整（GMO API仕様に合わせる）
        if symbol.endswith("_JPY"):
            # JPYペアはtickSize=0.001 → 小数点第3位まで
            entry_price = round(entry_price, 3)
            sl_price = round(sl_price, 3)
            tp_price = round(tp_price, 3)
        else:
            # USDペアはtickSize=0.00001 → 小数点第5位まで
            entry_price = round(entry_price, 5)
            sl_price = round(sl_price, 5)
            tp_price = round(tp_price, 5)

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
                first_price=f"{entry_price:.3f}" if symbol.endswith("_JPY") else f"{entry_price:.5f}",
                second_size=lot,
                second_limit_price=f"{tp_price:.3f}" if symbol.endswith("_JPY") else f"{tp_price:.5f}",
                second_stop_price=f"{sl_price:.3f}" if symbol.endswith("_JPY") else f"{sl_price:.5f}",
            )

            # 注文IDの抽出（IFDOCO responseはリスト）
            order_id = None
            if isinstance(order_result, list) and order_result:
                order_id = order_result[0].get("orderId") or order_result[0].get("rootOrderId")
            elif isinstance(order_result, dict):
                order_id = order_result.get("orderId")

            trade_reason = (
                f"{signal_data.get('reason', '')} | "
                f"lot={lot} ({lot_reason})"
            )

            result = TradeResult(
                success=True,
                action=side,
                symbol=symbol,
                size=lot,
                order_id=order_id,
                reason=trade_reason,
                timestamp=datetime.now(),
                dry_run=self.gmo_client.dry_run,
            )

            # v2.0 研究ログ付きで保存
            self._save_v2_trade_record(
                result=result,
                signal_data=signal_data,
                lot=lot,
                lot_reason=lot_reason,
                entry_price=entry_price,
                sl_price=sl_price,
                tp_price=tp_price,
            )

            return result

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

    def _save_hold_log(
        self,
        symbol: str,
        signal_data: Dict,
        reason: str,
        timestamp: datetime,
    ) -> Optional[str]:
        """
        HOLD判定をFirestoreに保存

        Args:
            symbol: 通貨ペア
            signal_data: シグナルデータ（テクニカルスコア含む）
            reason: HOLD理由
            timestamp: 判定時刻

        Returns:
            ドキュメントID
        """
        if not self.db:
            return None

        try:
            doc_id = f"hold_{timestamp.strftime('%Y%m%d_%H%M%S')}_{symbol}"

            doc_data = {
                "trade_id": doc_id,
                "symbol": symbol,
                "side": "HOLD",
                "used_lot": 0,
                "skip_reason": "TECHNICAL_HOLD",
                "technical_score": {
                    "buy_score": signal_data.get("buy_score", 0),
                    "sell_score": signal_data.get("sell_score", 0),
                    "confidence": signal_data.get("confidence", 0.0),
                },
                "reason": reason,
                "rule_version": signal_data.get("rule_version", "v2.0"),
                "created_at": timestamp,
                "dry_run": self.gmo_client.dry_run,
            }

            self.db.collection("trades").document(doc_id).set(doc_data)
            logger.info(f"Hold log saved: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to save hold log: {e}")
            return None

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
                    "buy_score": signal_data.get("buy_score", 0),
                    "sell_score": signal_data.get("sell_score", 0),
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

    def _save_v2_trade_record(
        self,
        result: TradeResult,
        signal_data: Dict,
        lot: int,
        lot_reason: str,
        entry_price: float,
        sl_price: float,
        tp_price: float,
    ) -> Optional[str]:
        """
        v2.0 研究ログ付きでトレード結果をFirestoreに保存

        Args:
            result: トレード結果
            signal_data: シグナルデータ（buy_score, sell_score含む）
            lot: 使用ロット
            lot_reason: ロット決定理由
            entry_price: エントリー価格
            sl_price: ストップロス価格
            tp_price: テイクプロフィット価格

        Returns:
            ドキュメントID
        """
        if not self.db:
            return None

        try:
            timestamp = result.timestamp or datetime.now()
            doc_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{result.symbol}"

            news_summary = signal_data.get("news_summary", {})

            doc_data = {
                # 基本フィールド
                "trade_id": doc_id,
                "symbol": result.symbol,
                "side": result.action,
                "entry_price": entry_price,
                "exit_price": None,
                "status": "open",
                "order_id": result.order_id,
                "order_type": "IFDOCO",
                "stop_loss": sl_price,
                "take_profit": tp_price,
                # v2.0 研究ログフィールド
                "used_lot": lot,
                "actual_pnl": None,
                "baseline_pnl": None,
                "ai_decision": {
                    "avg_sentiment": news_summary.get("avg_sentiment", 0.0),
                    "avg_impact": news_summary.get("avg_impact", 0.0),
                    "news_count": news_summary.get("count", 0),
                    "lot_reason": lot_reason,
                },
                "technical_score": {
                    "buy_score": signal_data.get("buy_score", 0),
                    "sell_score": signal_data.get("sell_score", 0),
                    "confidence": signal_data.get("confidence", 0.0),
                },
                "reason": result.reason,
                "rule_version": signal_data.get("rule_version", "v2.0"),
                "created_at": timestamp,
                "dry_run": result.dry_run,
            }

            self.db.collection("trades").document(doc_id).set(doc_data)
            logger.info(f"V2 trade record saved: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to save v2 trade record: {e}")
            return None

    @staticmethod
    def calculate_baseline_pnl(
        entry_price: float,
        exit_price: float,
        side: str,
    ) -> float:
        """
        Baseline損益を計算（1000通貨固定での仮想損益）

        Args:
            entry_price: エントリー価格
            exit_price: 決済価格
            side: 売買区分（"BUY" or "SELL"）

        Returns:
            baseline_pnl（円）
        """
        direction = 1 if side == "BUY" else -1
        return (exit_price - entry_price) * 1000 * direction

    def update_trade_settlement(
        self,
        trade_id: str,
        exit_price: float,
        actual_pnl: float,
        side: str,
        entry_price: float,
    ) -> bool:
        """
        決済時にactual_pnl/baseline_pnlを更新

        Args:
            trade_id: トレードID（Firestoreドキュメント）
            exit_price: 決済価格
            actual_pnl: 実損益（円）
            side: 売買区分
            entry_price: エントリー価格

        Returns:
            更新成功か
        """
        if not self.db:
            return False

        try:
            baseline_pnl = self.calculate_baseline_pnl(entry_price, exit_price, side)
            status = "WIN" if actual_pnl >= 0 else "LOSS"

            self.db.collection("trades").document(trade_id).update({
                "exit_price": exit_price,
                "actual_pnl": actual_pnl,
                "baseline_pnl": baseline_pnl,
                "status": status,
                "closed_at": datetime.now(),
            })

            logger.info(
                f"Trade settled: {trade_id} "
                f"actual_pnl={actual_pnl:.0f} baseline_pnl={baseline_pnl:.0f} ({status})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update trade settlement: {e}")
            return False

    def settle_open_trades(self) -> List[Dict]:
        """
        Firestore の open トレードを確認し、決済済みのものを更新する

        フロー:
          1. Firestore から status="open" の BUY/SELL トレードを取得
          2. 各トレードの order_id で /v1/executions を呼び OPEN execution の positionId を取得
          3. /v1/latestExecutions から settleType="CLOSE" の約定を取得
          4. positionId が一致する CLOSE execution があれば update_trade_settlement() を呼ぶ

        Returns:
            更新結果のリスト [{"trade_id": ..., "status": "settled"|"still_open"|"error", ...}]
        """
        if not self.db:
            logger.warning("settle_open_trades: Firestore not available")
            return []

        results = []

        # 1. Firestore から open トレードを取得
        try:
            query = (
                self.db.collection("trades")
                .where("status", "==", "open")
            )
            open_docs = list(query.stream())
        except Exception as e:
            logger.error(f"settle_open_trades: Firestore query failed: {e}")
            return [{"status": "error", "reason": str(e)}]

        if not open_docs:
            logger.info("settle_open_trades: no open trades found")
            return []

        # 2. シンボルごとに latestExecutions を1回だけ取得してキャッシュ
        latest_by_symbol: Dict[str, List[Dict]] = {}

        for doc in open_docs:
            trade = doc.to_dict()
            trade_id = trade.get("trade_id", doc.id)
            symbol = trade.get("symbol", "USD_JPY")
            order_id = trade.get("order_id")
            side = trade.get("side", "")

            if side not in ("BUY", "SELL"):
                continue

            if not order_id:
                logger.warning(f"settle_open_trades: no order_id for {trade_id}, skipping")
                results.append({"trade_id": trade_id, "status": "skipped", "reason": "no order_id"})
                continue

            try:
                # STEP A: order_id → positionId（OPEN execution から取得）
                entry_executions = self.gmo_client.get_executions(int(order_id))
                open_exec = next(
                    (e for e in entry_executions if e.get("settleType") == "OPEN"),
                    None,
                )
                if not open_exec:
                    logger.info(f"settle_open_trades: {trade_id} not yet filled (no OPEN execution)")
                    results.append({"trade_id": trade_id, "status": "still_open", "reason": "entry not filled"})
                    continue

                position_id = open_exec.get("positionId")
                if not position_id:
                    logger.warning(f"settle_open_trades: {trade_id} has no positionId in OPEN execution")
                    results.append({"trade_id": trade_id, "status": "error", "reason": "no positionId"})
                    continue

                # STEP B: latestExecutions（シンボル単位でキャッシュ）
                if symbol not in latest_by_symbol:
                    latest_by_symbol[symbol] = self.gmo_client.get_latest_executions(symbol)

                close_exec = next(
                    (
                        e for e in latest_by_symbol[symbol]
                        if e.get("settleType") == "CLOSE"
                        and e.get("positionId") == position_id
                    ),
                    None,
                )

                if not close_exec:
                    logger.info(f"settle_open_trades: {trade_id} (positionId={position_id}) still open or closed >24h ago")
                    results.append({"trade_id": trade_id, "status": "still_open", "reason": "no CLOSE execution in last 24h"})
                    continue

                # STEP C: 決済情報を取得して Firestore 更新
                exit_price = float(close_exec["price"])
                actual_pnl = float(close_exec["lossGain"])
                entry_price = trade.get("entry_price", 0.0)

                success = self.update_trade_settlement(
                    trade_id=trade_id,
                    exit_price=exit_price,
                    actual_pnl=actual_pnl,
                    side=side,
                    entry_price=entry_price,
                )

                if success:
                    status_str = "WIN" if actual_pnl >= 0 else "LOSS"
                    logger.info(f"settle_open_trades: {trade_id} settled → {status_str} actual_pnl={actual_pnl:.0f}")
                    results.append({
                        "trade_id": trade_id,
                        "status": "settled",
                        "result": status_str,
                        "actual_pnl": actual_pnl,
                        "exit_price": exit_price,
                    })
                else:
                    results.append({"trade_id": trade_id, "status": "error", "reason": "Firestore update failed"})

            except Exception as e:
                logger.error(f"settle_open_trades: error processing {trade_id}: {e}")
                results.append({"trade_id": trade_id, "status": "error", "reason": str(e)})

        return results

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
