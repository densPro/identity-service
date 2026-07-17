"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration.

    Values are loaded from environment variables or a ``.env`` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "Identity Service"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str = Field(..., validation_alias="DATABASE_URL")

    # --- CORS ---
    cors_origins: list[str] = ["*"]

    # --- JWT ---
    jwt_secret_key: str = Field(..., validation_alias="JWT_SECRET_KEY")
    jwt_refresh_secret_key: str = Field(..., validation_alias="JWT_REFRESH_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # --- Logging ---
    log_level: str = "INFO"
    log_format: str = "text"


settings = Settings()
