from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_env: str = "development"
    debug: bool = False

    anthropic_api_key: str

    langchain_api_key: Optional[str] = None
    langchain_project: str = "stk-portfolio-assistant"

    voyage_api_key: Optional[str] = None

    news_api_key: Optional[str] = None

    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None

    database_url: Optional[str] = None

    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "portfolio_data"


settings = Settings()
