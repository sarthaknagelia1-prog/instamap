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

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "groq").lower()
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # Instagram Graph API
    IG_ACCESS_TOKEN: str = os.getenv("IG_ACCESS_TOKEN", "")
    IG_USER_ID: str = os.getenv("IG_USER_ID", "")

    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")


settings = Settings()
