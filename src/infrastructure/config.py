"""
Application settings — equivalent to appsettings.json + IConfiguration in C#.
Pydantic-settings reads from environment variables / .env file automatically.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/clean_architecture_db"

    # App
    APP_NAME: str = "Clean Architecture Python"
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

