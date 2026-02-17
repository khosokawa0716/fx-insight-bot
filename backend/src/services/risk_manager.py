"""
Risk Manager

リスク管理機能を提供するクラス
Phase 4: 自動売買機能
v2.0: 月間損失管理、取引間隔チェック追加
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    """リスク管理設定（v2.0）"""

    # 損切り設定（pips）
    stop_loss_pips: float = 40.0

    # 利確設定（pips）
    take_profit_pips: float = 40.0

    # 月間最大損失額（円）
    max_monthly_loss: float = 5000.0

    # 1日あたりの最大取引回数
    max_daily_trades: int = 2

    # 取引間隔の最小値（時間）
    min_trade_interval_hours: int = 6

    # 連続損失での取引停止回数
    max_consecutive_losses: int = 7

    # 必要証拠金率（%）- この割合を下回ると新規取引停止
    min_margin_ratio: float = 100.0


@dataclass
class RiskCheckResult:
    """リスクチェック結果"""

    can_trade: bool
    reason: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "can_trade": self.can_trade,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "details": self.details,
        }


class RiskManager:
    """
    リスク管理クラス

    取引前のリスクチェック、ポジション監視を担当
    """

    def __init__(
        self,
        config: RiskConfig,
        db: Optional[firestore.Client] = None,
        database_id: str = "(default)",
    ):
        """
        初期化

        Args:
            config: リスク管理設定
            db: Firestoreクライアント（オプション）
            database_id: FirestoreデータベースID
        """
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

        # メモリ内の取引追跡（日次リセット）
        self._daily_trades = 0
        self._consecutive_losses = 0
        self._last_reset_date: Optional[datetime] = None

        logger.info(f"RiskManager initialized: stop_loss={config.stop_loss_pips}pips")

    def check_trade_allowed(
        self,
        symbol: str,
        side: Literal["BUY", "SELL"],
        size: int,
        account_assets: Optional[Dict] = None,
    ) -> RiskCheckResult:
        """
        取引が許可されるかチェック（v2.0）

        チェック項目:
        1. 連続損失
        2. 月間損失上限
        3. 日次取引回数
        4. 取引間隔（6時間以上）
        5. 証拠金率

        Args:
            symbol: 通貨ペア
            side: 売買区分
            size: 取引数量
            account_assets: 口座資産情報（オプション）

        Returns:
            リスクチェック結果
        """
        self._reset_daily_stats_if_needed()

        details: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "size": size,
            "daily_trades": self._daily_trades,
            "consecutive_losses": self._consecutive_losses,
        }

        # 1. 連続損失チェック
        if self._consecutive_losses >= self.config.max_consecutive_losses:
            return RiskCheckResult(
                can_trade=False,
                reason=f"Consecutive losses limit reached: {self._consecutive_losses}/{self.config.max_consecutive_losses}",
                risk_level="CRITICAL",
                details=details,
            )

        # 2. 月間損失チェック
        can_trade_monthly, monthly_loss = self.check_monthly_loss()
        details["monthly_loss"] = monthly_loss
        details["max_monthly_loss"] = self.config.max_monthly_loss
        if not can_trade_monthly:
            return RiskCheckResult(
                can_trade=False,
                reason=f"Monthly loss limit reached: {monthly_loss:.0f}/{self.config.max_monthly_loss:.0f} JPY",
                risk_level="CRITICAL",
                details=details,
            )

        # 3. 日次取引回数チェック
        if self._daily_trades >= self.config.max_daily_trades:
            return RiskCheckResult(
                can_trade=False,
                reason=f"Daily trade limit reached: {self._daily_trades}/{self.config.max_daily_trades}",
                risk_level="HIGH",
                details=details,
            )

        # 4. 取引間隔チェック
        can_trade_interval, last_trade_time = self.check_trade_interval()
        if not can_trade_interval:
            return RiskCheckResult(
                can_trade=False,
                reason=f"Trade interval too short: min {self.config.min_trade_interval_hours}h required",
                risk_level="HIGH",
                details={**details, "last_trade_time": str(last_trade_time)},
            )

        # 5. 証拠金率チェック（口座情報がある場合）
        if account_assets:
            margin_check = self._check_margin_ratio(account_assets)
            if not margin_check.can_trade:
                return margin_check

        # リスクレベルの判定
        risk_level = self._calculate_risk_level(monthly_loss)

        return RiskCheckResult(
            can_trade=True,
            reason="Trade allowed",
            risk_level=risk_level,
            details=details,
        )

    def check_monthly_loss(self) -> tuple[bool, float]:
        """
        月間累計損失をチェック

        Firestoreのtradesコレクションから当月の決済済み取引を集計し、
        累計損失がmax_monthly_lossを超えていないか確認する。

        Returns:
            (取引可能か, 当月累計損失額)
        """
        if not self.db:
            logger.warning("Firestore not available, skipping monthly loss check")
            return True, 0.0

        try:
            now = datetime.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            trades_ref = self.db.collection("trades")
            query = trades_ref.where(filter=FieldFilter("created_at", ">=", month_start))

            monthly_loss = 0.0
            for doc in query.stream():
                trade = doc.to_dict()
                pnl = trade.get("actual_pnl", 0.0)
                if pnl < 0:
                    monthly_loss += abs(pnl)

            can_trade = monthly_loss < self.config.max_monthly_loss
            if not can_trade:
                logger.warning(
                    f"Monthly loss limit reached: {monthly_loss:.0f}/{self.config.max_monthly_loss:.0f} JPY"
                )

            return can_trade, monthly_loss

        except Exception as e:
            logger.warning(f"Monthly loss check failed: {e}")
            return True, 0.0

    def check_trade_interval(self) -> tuple[bool, Optional[datetime]]:
        """
        前回取引からの間隔をチェック

        Firestoreから直近の取引を取得し、min_trade_interval_hours以上
        経過しているか確認する。

        Returns:
            (取引可能か, 前回取引時刻)
        """
        if not self.db:
            return True, None

        try:
            trades_ref = self.db.collection("trades")
            query = (
                trades_ref
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(1)
            )

            docs = list(query.stream())
            if not docs:
                return True, None

            last_trade = docs[0].to_dict()
            last_trade_time = last_trade.get("created_at")

            if not last_trade_time:
                return True, None

            # Firestore TimestampをnaiveなPython datetimeに変換して比較
            if hasattr(last_trade_time, "replace"):
                last_trade_naive = last_trade_time.replace(tzinfo=None)
            else:
                last_trade_naive = last_trade_time

            elapsed = datetime.now() - last_trade_naive
            elapsed_hours = elapsed.total_seconds() / 3600

            can_trade = elapsed_hours >= self.config.min_trade_interval_hours
            if not can_trade:
                logger.info(
                    f"Trade interval check: {elapsed_hours:.1f}h elapsed, "
                    f"min {self.config.min_trade_interval_hours}h required"
                )

            return can_trade, last_trade_time

        except Exception as e:
            logger.warning(f"Trade interval check failed: {e}")
            return True, None

    def _check_margin_ratio(self, account_assets: Dict) -> RiskCheckResult:
        """証拠金率をチェック"""
        try:
            balance = float(account_assets.get("balance", 0))
            margin = float(account_assets.get("margin", 0))

            if margin == 0:
                margin_ratio = 100.0  # ポジションなしは100%
            else:
                margin_ratio = (balance / margin) * 100

            details = {
                "balance": balance,
                "margin": margin,
                "margin_ratio": margin_ratio,
            }

            if margin_ratio < self.config.min_margin_ratio:
                return RiskCheckResult(
                    can_trade=False,
                    reason=f"Margin ratio too low: {margin_ratio:.1f}% < {self.config.min_margin_ratio}%",
                    risk_level="CRITICAL",
                    details=details,
                )

            return RiskCheckResult(
                can_trade=True,
                reason="Margin ratio OK",
                risk_level="LOW",
                details=details,
            )

        except Exception as e:
            logger.warning(f"Margin ratio check failed: {e}")
            return RiskCheckResult(
                can_trade=True,
                reason=f"Margin check skipped: {str(e)}",
                risk_level="MEDIUM",
                details={},
            )

    def _calculate_risk_level(
        self, monthly_loss: float = 0.0
    ) -> Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        """現在のリスクレベルを計算"""
        # 月間損失率
        loss_ratio = monthly_loss / self.config.max_monthly_loss if self.config.max_monthly_loss > 0 else 0

        # 取引回数率
        trade_ratio = self._daily_trades / self.config.max_daily_trades if self.config.max_daily_trades > 0 else 0

        # 連続損失率
        loss_streak_ratio = self._consecutive_losses / self.config.max_consecutive_losses if self.config.max_consecutive_losses > 0 else 0

        max_ratio = max(loss_ratio, trade_ratio, loss_streak_ratio)

        if max_ratio >= 0.8:
            return "HIGH"
        elif max_ratio >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"

    def _reset_daily_stats_if_needed(self) -> None:
        """日次統計を必要に応じてリセット"""
        today = datetime.now().date()

        if self._last_reset_date is None or self._last_reset_date != today:
            logger.info("Resetting daily stats")
            self._daily_trades = 0
            self._last_reset_date = today

    def record_trade_result(self, profit_loss: float, success: bool) -> None:
        """
        取引結果を記録

        Args:
            profit_loss: 損益（円）
            success: 取引成功か
        """
        self._daily_trades += 1

        if profit_loss < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0  # 利益が出たらリセット

        logger.info(
            f"Trade recorded: P/L={profit_loss:.0f}, "
            f"daily_trades={self._daily_trades}, "
            f"consecutive_losses={self._consecutive_losses}"
        )

    def calculate_stop_loss_price(
        self,
        entry_price: float,
        side: Literal["BUY", "SELL"],
        symbol: str,
    ) -> float:
        """
        ストップロス価格を計算

        Args:
            entry_price: エントリー価格
            side: 売買区分
            symbol: 通貨ペア

        Returns:
            ストップロス価格
        """
        # pipsを価格に変換（USD_JPYなら1pip = 0.01）
        pip_value = self._get_pip_value(symbol)
        stop_distance = self.config.stop_loss_pips * pip_value

        if side == "BUY":
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance

    def calculate_take_profit_price(
        self,
        entry_price: float,
        side: Literal["BUY", "SELL"],
        symbol: str,
    ) -> float:
        """
        利確価格を計算

        Args:
            entry_price: エントリー価格
            side: 売買区分
            symbol: 通貨ペア

        Returns:
            利確価格
        """
        pip_value = self._get_pip_value(symbol)
        profit_distance = self.config.take_profit_pips * pip_value

        if side == "BUY":
            return entry_price + profit_distance
        else:
            return entry_price - profit_distance

    def _get_pip_value(self, symbol: str) -> float:
        """
        通貨ペアのpip値を取得

        Args:
            symbol: 通貨ペア

        Returns:
            1pipの価格
        """
        # 円クロスは0.01、それ以外は0.0001
        if symbol.endswith("_JPY"):
            return 0.01
        else:
            return 0.0001

    def get_risk_summary(self) -> Dict[str, Any]:
        """リスク状況のサマリーを取得"""
        self._reset_daily_stats_if_needed()

        _, monthly_loss = self.check_monthly_loss()

        return {
            "monthly_loss": monthly_loss,
            "max_monthly_loss": self.config.max_monthly_loss,
            "monthly_loss_ratio": monthly_loss / self.config.max_monthly_loss if self.config.max_monthly_loss > 0 else 0,
            "daily_trades": self._daily_trades,
            "max_daily_trades": self.config.max_daily_trades,
            "consecutive_losses": self._consecutive_losses,
            "max_consecutive_losses": self.config.max_consecutive_losses,
            "risk_level": self._calculate_risk_level(monthly_loss),
            "stop_loss_pips": self.config.stop_loss_pips,
            "take_profit_pips": self.config.take_profit_pips,
            "min_trade_interval_hours": self.config.min_trade_interval_hours,
            "last_reset_date": self._last_reset_date.isoformat() if self._last_reset_date else None,
        }

    def should_close_position(
        self,
        position: Dict,
        current_price: float,
    ) -> tuple[bool, str]:
        """
        ポジションを決済すべきかチェック

        v2.0ではIFDOCO注文でSL/TPを証券会社側が管理するため、
        このメソッドはモニタリング用途のみ。

        Args:
            position: ポジション情報
            current_price: 現在価格

        Returns:
            (決済すべきか, 理由)
        """
        entry_price = float(position.get("price", 0))
        side = position.get("side", "")
        symbol = position.get("symbol", "")

        if not entry_price or not side:
            return False, "Invalid position data"

        # ストップロス・利確価格を計算
        stop_loss = self.calculate_stop_loss_price(entry_price, side, symbol)
        take_profit = self.calculate_take_profit_price(entry_price, side, symbol)

        # ストップロスチェック
        if side == "BUY" and current_price <= stop_loss:
            return True, f"Stop loss triggered: {current_price} <= {stop_loss}"
        elif side == "SELL" and current_price >= stop_loss:
            return True, f"Stop loss triggered: {current_price} >= {stop_loss}"

        # 利確チェック
        if side == "BUY" and current_price >= take_profit:
            return True, f"Take profit triggered: {current_price} >= {take_profit}"
        elif side == "SELL" and current_price <= take_profit:
            return True, f"Take profit triggered: {current_price} <= {take_profit}"

        return False, "Position OK"
