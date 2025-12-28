from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
   # Database
   DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/appsbuilder"
   DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@db:5432/appsbuilder"

   # OpenRouter
   OPENROUTER_API_KEY: str = ""
   OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
   LLM_MODEL: str = "openai/gpt-4o-mini"

   # Auth
   SECRET_KEY: str = "your-secret-key-change-in-production"
   ALGORITHM: str = "HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

   # App
   APP_NAME: str = "Blueprint Apps Builder"
   DEBUG: bool = True

   class Config:
      env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
   return Settings()


settings = get_settings()

