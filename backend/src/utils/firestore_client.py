"""
Firestore Client - Database connection management
"""

import os
from typing import Optional
from google.cloud import firestore
from google.oauth2 import service_account

from src.config import settings, get_credentials_path


class FirestoreClient:
    """Singleton Firestore client for database operations"""

    _instance: Optional[firestore.Client] = None

    @classmethod
    def get_client(cls) -> firestore.Client:
        """Get or create Firestore client instance"""
        if cls._instance is None:
            cls._instance = cls._create_client()
        return cls._instance

    @classmethod
    def _create_client(cls) -> firestore.Client:
        """Create Firestore client with service account credentials"""
        credentials_path = get_credentials_path()

        # Set environment variable for Google Cloud SDK
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)

        # Create credentials from service account file
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path)
        )

        # Initialize Firestore client
        client = firestore.Client(
            project=settings.gcp_project_id,
            database=settings.firestore_database_id,
            credentials=credentials,
        )

        return client

    @classmethod
    def test_connection(cls) -> dict:
        """Test Firestore connection and return status"""
        try:
            client = cls.get_client()

            # Try to list collections (this will fail if not authenticated)
            collections = list(client.collections())

            return {
                "status": "success",
                "message": "Successfully connected to Firestore",
                "project_id": settings.gcp_project_id,
                "database_id": settings.firestore_database_id,
                "collections_count": len(collections),
                "collections": [col.id for col in collections],
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to Firestore: {str(e)}",
                "project_id": settings.gcp_project_id,
                "database_id": settings.firestore_database_id,
            }


# Convenience function
def get_db() -> firestore.Client:
    """Get Firestore database client"""
    return FirestoreClient.get_client()
