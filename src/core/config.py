"""Configuration management using Pydantic settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Google Gemini API
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"

    # Ollama Fallback
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Database
    database_url: str = "sqlite:///./data/ebt_classification.db"

    # ChromaDB
    chroma_persist_directory: str = "./data/chroma_db"
    chroma_collection_name: str = "snap_regulations"

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    # External APIs
    usda_api_key: Optional[str] = None
    usda_api_base_url: str = "https://api.nal.usda.gov/fdc/v1"

    # Rate Limiting
    gemini_rpm_limit: int = 15
    gemini_daily_token_limit: int = 1000000

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def database_path(self) -> str:
        """Extract database path from URL."""
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.replace("sqlite:///", "")
        return self.database_url

    @property
    def is_gemini_configured(self) -> bool:
        """Check if Gemini API is properly configured."""
        return self.google_api_key is not None and len(self.google_api_key) > 0

    @property
    def is_usda_configured(self) -> bool:
        """Check if USDA API is properly configured."""
        return self.usda_api_key is not None and len(self.usda_api_key) > 0


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
