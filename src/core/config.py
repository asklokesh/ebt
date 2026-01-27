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

    # LLM Configuration (OpenAI-compatible API)
    llm_provider: str = "openai"  # openai, gemini, ollama, or custom
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None  # Custom API endpoint (e.g., your wrapper)
    llm_model: str = "gpt-4o-mini"  # Model name for your provider

    # Google Gemini API (legacy, use llm_* settings instead)
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"

    # Ollama Configuration
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_cloud_enabled: bool = False
    ollama_cloud_api_key: Optional[str] = None
    ollama_cloud_base_url: str = "https://api.ollama.com/v1"

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
    def is_llm_configured(self) -> bool:
        """Check if any LLM is properly configured."""
        # Check new unified LLM config first
        if self.llm_api_key and len(self.llm_api_key) > 0:
            return True
        # Fall back to legacy Gemini config
        if self.google_api_key and len(self.google_api_key) > 0:
            return True
        # Check Ollama
        if self.ollama_enabled:
            return True
        return False

    @property
    def is_gemini_configured(self) -> bool:
        """Check if Gemini API is properly configured (legacy)."""
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
