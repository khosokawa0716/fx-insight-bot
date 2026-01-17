"""
Trade API Router

自動売買関連のFastAPIエンドポイント
Phase 4: 自動売買機能
"""

import logging
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.gmo_client import (
    GMOCoinClient,
    APIError,
    AuthenticationError,
    OrderError,
)
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
    size: int = Field(..., ge=1, description="注文数量（1=1万通貨）")
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
    """シグナル実行リクエスト"""

    symbols: List[str] = Field(
        default=["USD_JPY"], description="対象通貨ペア"
    )
    default_size: int = Field(default=1, ge=1, description="注文サイズ")
    min_confidence: float = Field(
        default=0.7, ge=0.0, le=1.0, description="最低信頼度"
    )
    dry_run: bool = Field(default=True, description="DRY-RUNモード")


class ExecuteSignalsResponse(BaseModel):
    """シグナル実行レスポンス"""

    status: str
    message: str
    results: List[dict]
    dry_run: bool


class RiskSummaryResponse(BaseModel):
    """リスクサマリーレスポンス"""

    status: str
    data: dict


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
    シグナルに基づいて自動売買を実行

    ルールエンジンでシグナルを評価し、条件を満たす場合に注文を発注

    Args:
        request: 実行パラメータ

    Returns:
        実行結果
    """
    try:
        # GMOクライアント初期化
        gmo_client = GMOCoinClient(dry_run=request.dry_run)

        # コンポーネント初期化
        technical_analyzer = TechnicalAnalyzer(gmo_client)
        rule_engine = RuleEngine(technical_analyzer=technical_analyzer)

        # トレード設定
        trade_config = TradeConfig(
            symbols=request.symbols,
            default_size=request.default_size,
            min_confidence=request.min_confidence,
        )

        # TradeExecutor
        executor = TradeExecutor(
            gmo_client=gmo_client,
            rule_engine=rule_engine,
            config=trade_config,
        )

        # シグナル実行
        results = executor.execute_signals()

        # 結果を辞書に変換
        results_dict = [r.to_dict() for r in results]

        mode = "DRY-RUN" if request.dry_run else "LIVE"
        executed = sum(1 for r in results if r.success)

        return ExecuteSignalsResponse(
            status="success",
            message=f"[{mode}] Executed {executed}/{len(results)} signals",
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
