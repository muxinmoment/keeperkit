from pathlib import Path
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = None if os.getenv("KEEPERKIT_DISABLE_DOTENV") == "1" else BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
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

    embedding_provider: str = Field(default="hash", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="hash-256", alias="EMBEDDING_MODEL")
    vector_store_provider: str = Field(default="json", alias="VECTOR_STORE_PROVIDER")
    chroma_collection: str = Field(default="keeperkit_rules", alias="CHROMA_COLLECTION")

    generator_provider: str = Field(default="template", alias="GENERATOR_PROVIDER")
    llm_base_url: str = Field(default="https://api.deepseek.com", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="replace-me", alias="LLM_API_KEY")
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")


settings = Settings()
