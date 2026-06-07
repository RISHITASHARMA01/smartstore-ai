from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve .env from the project root regardless of working directory
_ENV_FILE = Path(__file__).parents[2] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/smartstore"
    secret_key: str = "changeme-in-production-generate-with-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
