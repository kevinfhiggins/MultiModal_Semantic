from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # MongoDB
    mongodb_uri: str
    mongodb_database: str
    mongodb_collection: str = "MoD_Data"

    # Voyage AI
    voyage_api_key: str
    voyage_model: str = "voyage-3"

    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Vector Search
    vector_index_name: str = "vector_index"
    vector_dimension: int = 1024

    # File Storage
    file_storage_path: str = "sample_data"
    file_base_url: str = "http://localhost:8000/files"

    class Config:
        # Look for .env in project root
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False
        extra = "allow"  # Allow extra fields

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


def get_settings() -> Settings:
    """Get application settings singleton"""
    return Settings()
