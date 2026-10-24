"""
backend/config.py

Configuration and settings for Instagram Growth Engine backend.
Loads environment variables from .env with sensible defaults.
"""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from repository root
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'growth_engine.db'}")

    # LLM Settings (optional — system works fully offline without these)
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "offline").lower()
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Security & Access Control Settings
    # In development/test default to False unless set to True; in production fails closed.
    REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "false").lower() in ("true", "1", "yes")
    DEFAULT_WORKSPACE_ID: str = os.getenv("DEFAULT_WORKSPACE_ID", "default")
    
    # Comma-separated list of allowed CORS origins
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:3000",
    )

    # Ingestion & Resource Limits
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))  # 10MB
    MAX_INGEST_RECORDS: int = int(os.getenv("MAX_INGEST_RECORDS", "5000"))
    MAX_PASTE_SIZE_BYTES: int = int(os.getenv("MAX_PASTE_SIZE_BYTES", str(5 * 1024 * 1024)))   # 5MB
    ORCHESTRATOR_TIMEOUT_SECONDS: int = int(os.getenv("ORCHESTRATOR_TIMEOUT_SECONDS", "60"))

    # Configured API keys mapping key -> user metadata JSON/dict
    API_KEYS_RAW: str = os.getenv("API_KEYS", "")

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"



settings = Settings()

