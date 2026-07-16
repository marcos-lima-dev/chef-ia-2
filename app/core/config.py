from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    secret_key: str = Field("dev-secret", env="SECRET_KEY")
    database_url: str = Field("sqlite+aiosqlite:///./chefe_ia.db", env="DATABASE_URL")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
