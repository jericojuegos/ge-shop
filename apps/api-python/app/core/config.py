from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="ge-shop-api-python")
    environment: str = Field(default="development")
    database_url: str = Field(default="sqlite:///./ge_shop.db")
    jwt_secret_key: str = Field(default="dev-only-change-in-production-secret-key-32b")
    jwt_algorithm: str = Field(default="HS256")
    ai_provider: str = Field(default="google")
    rust_engine_url: str = Field(default="http://127.0.0.1:8081")


settings = Settings()
