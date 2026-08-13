from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    database_url: Optional[str] = None
    jira_api_key: Optional[str] = None
    slack_bot_token: Optional[str] = None
    gemini_api_key: Optional[str] = None
    port: int = 8000
    sentry_dsn: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
