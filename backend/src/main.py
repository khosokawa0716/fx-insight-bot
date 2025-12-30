"""
FX Insight Bot - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
