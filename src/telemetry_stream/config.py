from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Persistent Telemetry Stream API"
    app_version: str = "2.0.0"
    environment: str = "development"
    database_url: str = "sqlite:///telemetry.db"
    oauth_client_id: str = "telemetry-client"
    oauth_client_secret: str = "development-only-secret"
    oauth_signing_key: str = "development-only-signing-key"
    oauth_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TELEMETRY_STREAM_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
