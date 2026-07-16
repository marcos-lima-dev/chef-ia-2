from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Geral
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    secret_key: str = Field("dev-secret", env="SECRET_KEY")

    # Banco de Dados (futuro)
    database_url: str = Field("sqlite+aiosqlite:///./chefe_ia.db", env="DATABASE_URL")

    # LLM
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    llm_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
