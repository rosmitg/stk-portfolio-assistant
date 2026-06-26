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

    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "stk-portfolio-assistant"

    voyage_api_key: Optional[str] = None

    news_api_key: Optional[str] = None

    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None

    database_url: Optional[str] = None

    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None

    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "portfolio_data"

    # Watchman backend service (generates portfolio briefs).
    watchman_backend_url: str = "http://localhost:8001"


settings = Settings()
