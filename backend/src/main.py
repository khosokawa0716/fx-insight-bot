"""
FX Insight Bot - FastAPI Application Entry Point
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.utils.firestore_client import FirestoreClient
from src.services.news_pipeline import run_news_collection
from src.api.trade import router as trade_router

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FX Insight Bot API",
    description="News collection, AI analysis, and trading signals for FX trading",
    version="0.1.0",
)

# Configure CORS (for frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trade_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "FX Insight Bot API is running",
        "environment": settings.environment,
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "gcp_project": settings.gcp_project_id,
        "firestore_db": settings.firestore_database_id,
        "location": settings.gcp_location,
    }


@app.get("/test/firestore")
async def test_firestore():
    """Test Firestore connection"""
    result = FirestoreClient.test_connection()
    return result


# ============================================================
# News Collection API
# ============================================================


class NewsCollectionRequest(BaseModel):
    """ニュース収集リクエスト"""

    query: Optional[str] = "USD/JPY EUR/JPY 為替 最新ニュース"
    news_count: Optional[int] = 5
    skip_duplicate: Optional[bool] = True


class NewsCollectionResponse(BaseModel):
    """ニュース収集レスポンス"""

    status: str
    message: str
    stats: dict


@app.post("/api/v1/news/collect", response_model=NewsCollectionResponse)
async def collect_news(request: NewsCollectionRequest = None):
    """
    ニュース収集エンドポイント

    Cloud Schedulerから定期的に呼び出されるエンドポイント。
    手動実行も可能。

    Args:
        request: 収集パラメータ（省略可）

    Returns:
        収集結果の統計情報
    """
    try:
        logger.info("News collection triggered via API")

        # デフォルトパラメータ
        if request is None:
            request = NewsCollectionRequest()

        # ニュース収集実行
        stats = run_news_collection(
            query=request.query,
            news_count=request.news_count,
            skip_duplicate=request.skip_duplicate,
        )

        logger.info(
            f"News collection completed: {stats['saved']} saved, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )

        return NewsCollectionResponse(
            status="success",
            message=f"Collected {stats['analyzed']} news items, saved {stats['saved']} items",
            stats=stats,
        )

    except Exception as e:
        logger.error(f"News collection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"News collection failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
