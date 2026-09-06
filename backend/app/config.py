from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root:
# BugTracking_project/
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()