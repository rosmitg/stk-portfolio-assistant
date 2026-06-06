from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    debug: bool = False

    # Claude (Anthropic)
    anthropic_api_key: str

    # LangSmith
    langchain_api_key: str
    langchain_project: str = "stk-portfolio-assistant"

    # NewsAPI
    news_api_key: str

    # Pinecone
    pinecone_api_key: str
    pinecone_environment: str

    # Database
    database_url: str


settings = Settings()
