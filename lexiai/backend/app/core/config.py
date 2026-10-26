import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'lexiai.db'}"
    SECRET_KEY: str = "supersecretkey12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    FRONTEND_URL_PROD: str = "https://lexiai.com"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "minimaxai/minimax-m3.1-flash"
    NVIDIA_EMBEDDING_MODEL: str = "nvidia/nemotron-3-embed-1b"
    AI_PROVIDER: str = "nvidia"  # "gemini", "nvidia", or "auto"
    CHROMA_PERSIST_DIR: str = str(BACKEND_DIR / "chroma_db")
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_CHUNKS: int = 4

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        extra="ignore"
    )

settings = Settings()

# If DATABASE_URL was provided from .env as a relative sqlite path, resolve it relative to BACKEND_DIR
if settings.DATABASE_URL.startswith("sqlite:///./"):
    rel_name = settings.DATABASE_URL.replace("sqlite:///./", "")
    settings.DATABASE_URL = f"sqlite:///{BACKEND_DIR / rel_name}"

