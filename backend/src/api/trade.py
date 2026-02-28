"""
Trade API Router

自動売買関連のFastAPIエンドポイント
Phase 4: 自動売買機能
"""

import logging
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.gmo_client import (
    GMOCoinClient,
    APIError,
    AuthenticationError,
    OrderError,
)
from src.config import settings
from src.services.trade_executor import TradeExecutor, TradeConfig, TradeResult
from src.services.risk_manager import RiskManager, RiskConfig
from src.services.technical_analyzer import TechnicalAnalyzer
from src.services.rule_engine import RuleEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trade", tags=["Trade"])


# ============================================================
# Request/Response Models
# ============================================================


class AccountAssetsResponse(BaseModel):
    """口座資産レスポンス"""

    status: str
    data: dict


class PositionItem(BaseModel):
    """ポジション項目"""

    position_id: str = Field(alias="positionId")
    symbol: str
    side: str
    size: str
    price: str
    loss_gain: Optional[str] = Field(default=None, alias="lossGain")
    timestamp: Optional[str] = None

    class Config:
        populate_by_name = True


class PositionsResponse(BaseModel):
    """ポジション一覧レスポンス"""

    status: str
    count: int
    positions: List[dict]


class OrderItem(BaseModel):
    """注文項目"""

    order_id: str = Field(alias="orderId")
    symbol: str
    side: str
    size: str
    price: Optional[str] = None
    execution_type: str = Field(alias="executionType")
    status: str
    timestamp: Optional[str] = None

    class Config:
        populate_by_name = True


class OrdersResponse(BaseModel):
    """有効注文一覧レスポンス"""

    status: str
    count: int
    orders: List[dict]


class PlaceOrderRequest(BaseModel):
    """注文発注リクエスト"""

    symbol: str = Field(..., description="通貨ペア（例: USD_JPY）")
    side: Literal["BUY", "SELL"] = Field(..., description="売買区分")
    size: int = Field(..., ge=1, description="注文数量（1=1通貨。USD_JPYの最小: 100）")
    execution_type: Literal["MARKET", "LIMIT", "STOP"] = Field(
        default="MARKET", description="注文タイプ"
    )
    price: Optional[str] = Field(default=None, description="指値価格（LIMIT時）")
    stop_price: Optional[str] = Field(default=None, description="逆指値価格（STOP時）")
    dry_run: bool = Field(default=True, description="DRY-RUNモード（デフォルト: True）")


class PlaceOrderResponse(BaseModel):
    """注文発注レスポンス"""

    status: str
    message: str
    order: dict
    dry_run: bool


class PlaceIFDOCORequest(BaseModel):
    """IFDOCO注文リクエスト"""

    symbol: str = Field(..., description="通貨ペア")
    first_side: Literal["BUY", "SELL"] = Field(..., description="1次注文の売買区分")
    first_execution_type: Literal["LIMIT", "STOP"] = Field(
        default="LIMIT", description="1次注文タイプ"
    )
    first_size: int = Field(..., ge=1, description="1次注文数量")
    first_price: str = Field(..., description="1次注文価格")
    second_size: int = Field(..., ge=1, description="2次注文数量")
    second_limit_price: str = Field(..., description="利確価格")
    second_stop_price: str = Field(..., description="損切り価格")
    dry_run: bool = Field(default=True, description="DRY-RUNモード")


class PlaceIFDOCOResponse(BaseModel):
    """IFDOCO注文レスポンス"""

    status: str
    message: str
    orders: List[dict]
    dry_run: bool


class ExecuteSignalsRequest(BaseModel):
    """シグナル実行リクエスト（v2.0）"""

    dry_run: bool = Field(default=True, description="DRY-RUNモード")


class ExecuteSignalsResponse(BaseModel):
    """シグナル実行レスポンス（v2.0）"""

    status: str
    message: str
    results: List[dict]
    dry_run: bool


class RiskSummaryResponse(BaseModel):
    """リスクサマリーレスポンス"""

    status: str
    data: dict


class MonthlySummaryResponse(BaseModel):
    """月間損益サマリーレスポンス（v2.0 研究用）"""

    status: str
    period: str
    data: dict


class TradeHistoryItem(BaseModel):
    """取引履歴1件（BUY/SELL/HOLD/SKIP 共通）"""

    trade_id: str
    symbol: str
    side: str
    used_lot: int = 0
    reason: str = ""
    created_at: str
    dry_run: bool = False
    # BUY/SELL のみ
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    order_id: Optional[str] = None
    status: Optional[str] = None
    actual_pnl: Optional[float] = None
    baseline_pnl: Optional[float] = None
    # AI判断（BUY/SELL/SKIP のみ）
    ai_sentiment: Optional[float] = None
    ai_impact: Optional[float] = None
    ai_news_count: Optional[int] = None
    lot_reason: Optional[str] = None
    # テクニカルスコア（全アクション）
    buy_score: Optional[int] = None
    sell_score: Optional[int] = None
    confidence: Optional[float] = None
    skip_reason: Optional[str] = None


class TradeHistoryResponse(BaseModel):
    """取引履歴レスポンス"""

    status: str
    count: int
    items: List[TradeHistoryItem]


class CancelOrderRequest(BaseModel):
    """注文キャンセルリクエスト"""

    order_id: str = Field(..., description="注文ID")
    dry_run: bool = Field(default=True, description="DRY-RUNモード")


class CancelOrderResponse(BaseModel):
    """注文キャンセルレスポンス"""

    status: str
    message: str
    result: dict
    dry_run: bool


# ============================================================
# Endpoints
# ============================================================


@router.get("/account", response_model=AccountAssetsResponse)
async def get_account_assets():
    """
    口座資産情報を取得

    Returns:
        口座残高、取引余力、必要証拠金などの情報
    """
    try:
        client = GMOCoinClient()
        assets = client.get_account_assets()

        return AccountAssetsResponse(
            status="success",
            data=assets,
        )

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except APIError as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions", response_model=PositionsResponse)
async def get_positions(symbol: Optional[str] = None):
    """
    ポジション一覧を取得

    Args:
        symbol: 通貨ペア（省略時は全通貨ペア）

    Returns:
        ポジション一覧
    """
    try:
        client = GMOCoinClient()
        positions = client.get_positions(symbol=symbol)

        return PositionsResponse(
            status="success",
            count=len(positions),
            positions=positions,
        )

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except APIError as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=OrdersResponse)
async def get_orders(symbol: Optional[str] = None):
    """
    有効注文一覧を取得

    Args:
        symbol: 通貨ペア（省略時は全通貨ペア）

    Returns:
        有効注文一覧
    """
    try:
        client = GMOCoinClient()
        orders = client.get_orders(symbol=symbol)

        return OrdersResponse(
            status="success",
            count=len(orders),
            orders=orders,
        )

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except APIError as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order", response_model=PlaceOrderResponse)
async def place_order(request: PlaceOrderRequest):
    """
    新規注文を発注

    Args:
        request: 注文パラメータ

    Returns:
        注文結果

    Note:
        デフォルトでDRY-RUNモード（実際の注文は行わない）
        本番注文を行う場合は dry_run=False を指定
    """
    try:
        client = GMOCoinClient(dry_run=request.dry_run)

        result = client.place_order(
            symbol=request.symbol,
            side=request.side,
            size=request.size,
            execution_type=request.execution_type,
            price=request.price,
            stop_price=request.stop_price,
        )

        mode = "DRY-RUN" if request.dry_run else "LIVE"
        return PlaceOrderResponse(
            status="success",
            message=f"[{mode}] Order placed: {request.side} {request.size} {request.symbol}",
            order=result,
            dry_run=request.dry_run,
        )

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except OrderError as e:
        logger.error(f"Order error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order/ifdoco", response_model=PlaceIFDOCOResponse)
async def place_ifdoco_order(request: PlaceIFDOCORequest):
    """
    IFDOCO注文を発注

    新規注文＋利確＋損切りを同時に設定

    Args:
        request: IFDOCO注文パラメータ

    Returns:
        注文結果（3件: 新規＋利確＋損切り）
    """
    try:
        client = GMOCoinClient(dry_run=request.dry_run)

        result = client.place_ifdoco_order(
            symbol=request.symbol,
            first_side=request.first_side,
            first_execution_type=request.first_execution_type,
            first_size=request.first_size,
            first_price=request.first_price,
            second_size=request.second_size,
            second_limit_price=request.second_limit_price,
            second_stop_price=request.second_stop_price,
        )

        mode = "DRY-RUN" if request.dry_run else "LIVE"
        return PlaceIFDOCOResponse(
            status="success",
            message=f"[{mode}] IFDOCO order placed: {request.first_side} {request.first_size} {request.symbol}",
            orders=result,
            dry_run=request.dry_run,
        )

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except OrderError as e:
        logger.error(f"Order error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except APIError as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order/cancel", response_model=CancelOrderResponse)
async def cancel_order(request: CancelOrderRequest):
    """
    注文をキャンセル

    Args:
        request: キャンセルパラメータ

    Returns:
        キャンセル結果
    """
    try:
        client = GMOCoinClient(dry_run=request.dry_run)

        result = client.cancel_order(order_id=request.order_id)

        mode = "DRY-RUN" if request.dry_run else "LIVE"
        return CancelOrderResponse(
            status="success",
            message=f"[{mode}] Order canceled: {request.order_id}",
            result=result,
            dry_run=request.dry_run,
        )

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except APIError as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=ExecuteSignalsResponse)
async def execute_signals(request: ExecuteSignalsRequest):
    """
    v2.0 シグナルに基づいて自動売買を実行

    テクニカル → AIロット決定 → リスクチェック → IFDOCO注文
    対象: USD_JPY のみ

    Args:
        request: 実行パラメータ

    Returns:
        実行結果（BUY/SELL/HOLD/SKIP）
    """
    try:
        # GMOクライアント初期化
        gmo_client = GMOCoinClient(dry_run=request.dry_run)

        # コンポーネント初期化
        technical_analyzer = TechnicalAnalyzer(gmo_client)
        rule_engine = RuleEngine(technical_analyzer=technical_analyzer)

        # リスクマネージャー初期化
        risk_config = RiskConfig()
        risk_manager = RiskManager(
            config=risk_config,
            database_id=settings.firestore_database_id,
        )

        # トレード設定（v2.0: USD_JPY固定）
        trade_config = TradeConfig(
            symbols=["USD_JPY"],
        )

        # TradeExecutor（RiskManager統合）
        executor = TradeExecutor(
            gmo_client=gmo_client,
            rule_engine=rule_engine,
            config=trade_config,
            risk_manager=risk_manager,
            database_id=settings.firestore_database_id,
        )

        # シグナル実行
        results = executor.execute_signals()

        # 結果を辞書に変換
        results_dict = [r.to_dict() for r in results]

        mode = "DRY-RUN" if request.dry_run else "LIVE"
        actions = [r.action for r in results]
        traded = sum(1 for a in actions if a in ("BUY", "SELL"))
        skipped = sum(1 for a in actions if a == "SKIP")

        return ExecuteSignalsResponse(
            status="success",
            message=f"[{mode}] traded={traded} skipped={skipped} hold={len(actions)-traded-skipped}",
            results=results_dict,
            dry_run=request.dry_run,
        )

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/summary", response_model=RiskSummaryResponse)
async def get_risk_summary():
    """
    リスク状況のサマリーを取得

    Returns:
        日次損失、取引回数、リスクレベルなど
    """
    try:
        risk_config = RiskConfig()
        risk_manager = RiskManager(config=risk_config)

        summary = risk_manager.get_risk_summary()

        return RiskSummaryResponse(
            status="success",
            data=summary,
        )

    except Exception as e:
        logger.error(f"Risk summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary():
    """
    v2.0 月間損益サマリーを取得（研究用）

    当月のトレード結果を集計し、AI運用 vs Baseline の比較データを返す。

    Returns:
        月間損益、勝率、ロット別成績、AI見送り統計
    """
    try:
        from datetime import datetime
        from google.cloud import firestore as fs
        from google.cloud.firestore_v1.base_query import FieldFilter

        db = fs.Client(database=settings.firestore_database_id)
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period = now.strftime("%Y-%m")

        # 当月のトレードを取得
        trades_ref = db.collection("trades")
        query = trades_ref.where(filter=FieldFilter("created_at", ">=", month_start))

        total_actual_pnl = 0.0
        total_baseline_pnl = 0.0
        win_count = 0
        loss_count = 0
        skip_count = 0
        lot_stats: dict = {}  # ロット別集計

        for doc in query.stream():
            trade = doc.to_dict()

            # AI見送りログ
            if trade.get("skip_reason"):
                skip_count += 1
                continue

            actual_pnl = trade.get("actual_pnl")
            baseline_pnl = trade.get("baseline_pnl")
            used_lot = trade.get("used_lot", 0)
            status = trade.get("status", "")

            # 決済済みのみ集計
            if actual_pnl is not None:
                total_actual_pnl += actual_pnl
                if status == "WIN":
                    win_count += 1
                elif status == "LOSS":
                    loss_count += 1

            if baseline_pnl is not None:
                total_baseline_pnl += baseline_pnl

            # ロット別集計
            lot_key = str(used_lot)
            if lot_key not in lot_stats:
                lot_stats[lot_key] = {"count": 0, "win": 0, "loss": 0, "pnl": 0.0}
            lot_stats[lot_key]["count"] += 1
            if status == "WIN":
                lot_stats[lot_key]["win"] += 1
            elif status == "LOSS":
                lot_stats[lot_key]["loss"] += 1
            if actual_pnl is not None:
                lot_stats[lot_key]["pnl"] += actual_pnl

        total_trades = win_count + loss_count
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
        ai_advantage = total_actual_pnl - total_baseline_pnl

        return MonthlySummaryResponse(
            status="success",
            period=period,
            data={
                "total_trades": total_trades,
                "win_count": win_count,
                "loss_count": loss_count,
                "win_rate": round(win_rate, 1),
                "skip_count": skip_count,
                "actual_pnl": round(total_actual_pnl, 0),
                "baseline_pnl": round(total_baseline_pnl, 0),
                "ai_advantage": round(ai_advantage, 0),
                "lot_stats": lot_stats,
            },
        )

    except Exception as e:
        logger.error(f"Monthly summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=TradeHistoryResponse)
async def get_trade_history(
    limit: int = Query(default=50, ge=1, le=200, description="取得件数"),
    symbol: Optional[str] = Query(default=None, description="通貨ペアフィルタ（例: USD_JPY）"),
    action: Optional[str] = Query(default=None, description="アクションフィルタ（BUY/SELL/HOLD/SKIP）"),
):
    """
    取引履歴を取得

    Firestoreの trades コレクションから最新N件を返す。
    BUY/SELL/HOLD/SKIP 全てのレコードを含む。

    Args:
        limit: 取得件数（デフォルト50、最大200）
        symbol: 通貨ペアフィルタ（省略時は全通貨ペア）
        action: アクションフィルタ（省略時は全アクション）

    Returns:
        取引履歴一覧
    """
    try:
        from google.cloud import firestore as fs
        from google.cloud.firestore_v1.base_query import FieldFilter

        db = fs.Client(database=settings.firestore_database_id)
        trades_ref = db.collection("trades")

        # symbol フィルタ（Firestore側）
        if symbol:
            query = trades_ref.where(filter=FieldFilter("symbol", "==", symbol))
        else:
            query = trades_ref

        # created_at 降順
        query = query.order_by("created_at", direction=fs.Query.DESCENDING)

        # action フィルタがある場合は多めに取得してPython側でフィルタ
        fetch_limit = limit if not action else min(limit * 4, 500)
        query = query.limit(fetch_limit)

        items = []
        for doc in query.stream():
            trade = doc.to_dict()

            side = trade.get("side", "")
            skip_reason = trade.get("skip_reason")

            # action フィルタ（Python側）
            if action:
                action_upper = action.upper()
                if action_upper == "BUY":
                    if side != "BUY" or skip_reason:
                        continue
                elif action_upper == "SELL":
                    if side != "SELL" or skip_reason:
                        continue
                elif action_upper == "HOLD":
                    if side != "HOLD":
                        continue
                elif action_upper == "SKIP":
                    if not skip_reason:
                        continue

            # created_at を ISO 文字列に変換
            created_at = trade.get("created_at")
            if hasattr(created_at, "isoformat"):
                created_at_str = created_at.isoformat()
            else:
                created_at_str = str(created_at) if created_at else ""

            ai_decision = trade.get("ai_decision") or {}
            tech_score = trade.get("technical_score") or {}

            items.append(TradeHistoryItem(
                trade_id=trade.get("trade_id", doc.id),
                symbol=trade.get("symbol", ""),
                side=side,
                used_lot=trade.get("used_lot", 0),
                reason=trade.get("reason", ""),
                created_at=created_at_str,
                dry_run=trade.get("dry_run", False),
                entry_price=trade.get("entry_price"),
                stop_loss=trade.get("stop_loss"),
                take_profit=trade.get("take_profit"),
                order_id=trade.get("order_id"),
                status=trade.get("status"),
                actual_pnl=trade.get("actual_pnl"),
                baseline_pnl=trade.get("baseline_pnl"),
                ai_sentiment=ai_decision.get("avg_sentiment"),
                ai_impact=ai_decision.get("avg_impact"),
                ai_news_count=ai_decision.get("news_count"),
                lot_reason=ai_decision.get("lot_reason"),
                buy_score=tech_score.get("buy_score"),
                sell_score=tech_score.get("sell_score"),
                confidence=tech_score.get("confidence"),
                skip_reason=skip_reason,
            ))

            if len(items) >= limit:
                break

        return TradeHistoryResponse(
            status="success",
            count=len(items),
            items=items,
        )

    except Exception as e:
        logger.error(f"Trade history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
