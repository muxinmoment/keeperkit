from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="KeeperKit Rules", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")

    raw_docs_dir: Path = Field(default=BACKEND_DIR / "data" / "raw", alias="RAW_DOCS_DIR")
    processed_docs_dir: Path = Field(
        default=BACKEND_DIR / "data" / "processed",
        alias="PROCESSED_DOCS_DIR",
    )
    index_dir: Path = Field(default=BACKEND_DIR / "data" / "index", alias="INDEX_DIR")

    retrieval_top_k: int = Field(default=8, alias="RETRIEVAL_TOP_K")
    rerank_top_k: int = Field(default=3, alias="RERANK_TOP_K")

    llm_base_url: str = Field(default="https://api.deepseek.com", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="replace-me", alias="LLM_API_KEY")
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")


settings = Settings()
