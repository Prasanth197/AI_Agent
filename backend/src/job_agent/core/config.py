"""Environment-backed application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Job Application Agent"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = Field(
        default="postgresql+psycopg://job_agent:local_dev_only_change_me@localhost:5432/job_agent",
        repr=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so the app has one consistent configuration."""

    return Settings()
