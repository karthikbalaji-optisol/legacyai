import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "LegacyLens AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # Storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "backend" / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    REPOSITORIES_DIR: Path = STORAGE_DIR / "repositories"
    EXPORTS_DIR: Path = STORAGE_DIR / "exports"

    # Database: Supports SQLite (aiosqlite) or PostgreSQL (asyncpg)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{STORAGE_DIR}/legacylens.db"

    # Security Limits
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB
    MAX_FILE_COUNT: int = int(os.getenv("MAX_FILE_COUNT", "25000"))  # Enterprise repos up to 25,000 files
    MAX_SINGLE_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    MAX_UNCOMPRESSED_SIZE_BYTES: int = 500 * 1024 * 1024  # 500 MB
    MAX_ANALYSIS_SECONDS: int = 300

    # Amazon Bedrock Settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_SESSION_TOKEN: str = os.getenv("AWS_SESSION_TOKEN", "")
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    BEDROCK_MAX_TOKENS: int = 16384
    BEDROCK_TEMPERATURE: float = 0.1
    BEDROCK_TIMEOUT_SECONDS: int = 180

    # Observability
    ENABLE_OTEL: bool = True
    ENABLE_PROMETHEUS: bool = True
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")

    def ensure_directories(self) -> None:
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
        self.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()

