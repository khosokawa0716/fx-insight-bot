"""
FX Insight Bot - Configuration Management
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # GCP Configuration
    gcp_project_id: str = "fx-insight-bot-prod"
    gcp_location: str = "asia-northeast1"
    firestore_database_id: str = "fx-insight-bot-db"

    # Service Account (for local development)
    google_application_credentials: str = "../credentials/service-account.json"

    # Vertex AI Configuration
    vertex_ai_model: str = "gemini-1.5-flash"

    # News Collection
    news_collection_interval_hours: int = 12

    # Application
    environment: str = "development"
    log_level: str = "INFO"

    # GMO Coin API (optional - for trading functionality)
    gmo_api_key: str = ""
    gmo_api_secret: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()


def get_credentials_path() -> Path:
    """Get absolute path to service account credentials"""
    backend_dir = Path(__file__).parent.parent
    credentials_path = (backend_dir / settings.google_application_credentials).resolve()

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Service account credentials not found at: {credentials_path}\n"
            f"Please ensure the JSON key file is in the credentials/ directory."
        )

    return credentials_path
