"""Validated application configuration."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/khaoai"
    auto_create_tables: bool = False

    jwt_secret_key: str = Field(default="development-only-change-me", min_length=24)
    jwt_expire_minutes: int = 60 * 24 * 7
    provider_token_encryption_key: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    default_location: str = "Salt Lake, Sector V"
    local_timezone: str = "Asia/Kolkata"

    swiggy_mcp_url: str = "https://mcp.swiggy.com/food"
    swiggy_oauth_base_url: str = "https://mcp.swiggy.com"
    swiggy_redirect_uri: str = "http://localhost:8000/api/providers/swiggy/callback"
    swiggy_cache_ttl_seconds: int = 120
    swiggy_request_timeout_seconds: float = 20.0
    fixture_provider_enabled: bool = False

    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    debug_endpoints_enabled: bool = True

    @field_validator("database_url")
    @classmethod
    def normalize_database_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def validate_runtime_security(self) -> None:
        if self.app_env == "production" and (
            self.jwt_secret_key == "development-only-change-me" or self.jwt_secret_key.startswith("replace-")
        ):
            raise RuntimeError("JWT_SECRET_KEY must be set in production")
        if self.app_env == "production" and not self.provider_token_encryption_key:
            raise RuntimeError("PROVIDER_TOKEN_ENCRYPTION_KEY must be set in production")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime_security()
    return settings


settings = get_settings()
