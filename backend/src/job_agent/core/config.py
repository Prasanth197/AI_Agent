"""Environment-backed application settings."""

from functools import lru_cache

from pydantic import Field, model_validator
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
    auth_secret: str = Field(
        default="replace-this-local-secret-with-a-random-value-at-least-32-chars",
        min_length=32,
        repr=False,
    )
    access_token_minutes: int = Field(default=30, ge=5, le=1440)
    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-4.1-mini"
    max_resume_bytes: int = Field(default=8 * 1024 * 1024, ge=1024, le=25 * 1024 * 1024)

    @model_validator(mode="after")
    def require_production_secret(self) -> "Settings":
        if self.app_env.lower() in {"production", "prod"} and self.auth_secret.startswith("replace-this-"):
            raise ValueError("AUTH_SECRET must be set to a unique random value in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so the app has one consistent configuration."""

    return Settings()
