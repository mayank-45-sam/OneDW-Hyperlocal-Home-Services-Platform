"""
Application configuration loaded from environment variables.
Uses pydantic-settings for type-safe, validated env parsing.
"""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "onedw_db"

    # JWT
    jwt_secret_key: str = "development-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Gemini AI
    gemini_api_key: str = ""

    # App
    app_env: str = "development"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174,"
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — avoids re-reading .env on every import."""
    return Settings()


settings = get_settings()