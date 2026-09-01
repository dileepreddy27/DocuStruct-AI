from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DocuStruct AI"
    database_url: str = "sqlite:///./data/docustruct.db"
    storage_root: Path = Path("./data/uploads")
    max_upload_bytes: int = 10 * 1024 * 1024
    extraction_provider: str = "heuristic"
    review_confidence_threshold: float = 0.80
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
