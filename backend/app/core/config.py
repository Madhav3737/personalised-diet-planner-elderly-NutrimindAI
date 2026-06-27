import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NutriMind AI"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecretkeychangeit48920384029384"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Databases
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nutrimind"
    REDIS_URL: Optional[str] = None
    
    # Vector Search
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DB_DIR: str = "./embeddings"
    DOCUMENTS_DIR: str = "./documents"
    
    # LLM config
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o"
    
    # Fallback to local SQLite if Postgres fails or isn't desired
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_DATABASE_URL: str = "sqlite+aiosqlite:///./nutrimind.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
