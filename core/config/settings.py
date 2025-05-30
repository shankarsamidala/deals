"""
Production-ready configuration management with Pydantic settings.
Centralized settings for all services in the application.
"""

from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Complete application settings - all in one class for simplicity"""

    # Application
    environment: str = Field(default="development", description="Application environment")
    app_name: str = Field(default="telegram-deal-monitor", description="Application name")
    log_level: str = Field(default="INFO", description="Logging level")

    # Telegram
    telegram_api_id: int = Field(..., description="Telegram API ID")
    telegram_api_hash: str = Field(..., description="Telegram API Hash")
    telegram_session_string: str = Field(..., description="Telegram session string")

    # MongoDB
    mongodb_uri: str = Field(..., description="MongoDB connection URI")
    mongodb_database: str = Field(..., description="Database name")
    mongodb_connection_timeout: int = Field(default=10, description="Connection timeout in seconds")

    # Discord
    discord_incidents_webhook: str = Field(..., description="Discord incidents webhook URL")
    discord_monitoring_webhook: str = Field(..., description="Discord monitoring webhook URL")

    # DataDog
    datadog_api_key: Optional[str] = Field(default=None, description="DataDog API key")
    datadog_app_key: Optional[str] = Field(default=None, description="DataDog APP key")
    datadog_enabled: bool = Field(default=False, description="Enable DataDog monitoring")

    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    sentry_enabled: bool = Field(default=False, description="Enable Sentry error tracking")

    # API Service
    api_service_port: int = Field(default=8000, description="API service port")
    api_service_host: str = Field(default="0.0.0.0", description="API service host")

    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = "utf-8"


# Function to get settings instance with proper path resolution
def get_settings() -> Settings:
    """Get settings instance with proper .env file resolution"""
    from pathlib import Path
    import os

    # Find .env file in project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # Go up to project root
    env_file_path = project_root / ".env"

    # Change working directory temporarily if needed
    original_cwd = os.getcwd()
    if not Path(".env").exists() and env_file_path.exists():
        os.chdir(project_root)

    try:
        return Settings(_env_file=str(env_file_path))
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


# Global settings instance
settings = get_settings()