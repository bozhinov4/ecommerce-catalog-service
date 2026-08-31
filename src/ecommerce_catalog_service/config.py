"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CATALOG_",
        extra="ignore",
    )

    app_name: str = "E-commerce Catalog Service"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = Field(
        default="postgresql+psycopg://catalog:catalog@localhost:5432/catalog",
        repr=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
