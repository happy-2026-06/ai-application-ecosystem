"""Application configuration via Pydantic Settings.

All secrets MUST be set via environment variables or .env file in production.
The defaults below are for local development only and will trigger warnings.
"""
import os
import warnings
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    # ── Application ──────────────────────────────────────────────────
    APP_NAME: str = "图库资产管家"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(
        default="dev-secret-change-me-in-production",
        description="Used by FastAPI/Starlette for session signing. Override in production!",
    )

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/assetmgmt.db",
        description="Async database URL. For PostgreSQL, set postgresql+asyncpg://user:pass@host/db",
    )
    DATABASE_URL_SYNC: str = Field(
        default="sqlite:///./data/assetmgmt.db",
        description="Synchronous database URL (for Alembic migrations)",
    )

    # ── Redis ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── ChromaDB ─────────────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # ── Neo4j ────────────────────────────────────────────────────────
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = Field(
        default="neo4j-dev-password",
        description="Neo4j password. Override in production!",
    )

    # ── Embedding Model (Ollama) ─────────────────────────────────────
    OLLAMA_HOST: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "bge-m3"
    EMBEDDING_DIM: int = 1024

    # ── DeepSeek API ─────────────────────────────────────────────────
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ── LLM Fallback (Ollama) ─────────────────────────────────────────
    OLLAMA_LLM_MODEL: str = "qwen2.5:7b"

    # ── JWT ──────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        default="jwt-dev-secret-change-me-in-production",
        description="JWT signing key. MUST be a long random string in production!",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── File Upload ──────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./data/uploads"

    # ── RAG Parameters ───────────────────────────────────────────────
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    RETRIEVAL_TOP_K: int = 20
    RERANK_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.5

    # ── Rate Limiting ────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:80", "http://localhost"],
    )

    # ── Pre-seeded admin account ─────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = Field(
        default="admin123",
        description="Initial admin password. CHANGE IT after first login!",
    )
    ADMIN_EMAIL: str = "admin@assetmgmt.local"

    # ── Pydantic Config ──────────────────────────────────────────────
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    # ── Derived Properties ───────────────────────────────────────────
    @property
    def max_upload_size_bytes(self) -> int:
        """Max upload file size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def chroma_http_url(self) -> str:
        """Full HTTP URL for ChromaDB server."""
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"

    # ── Security Warnings (development defaults) ─────────────────────
    _warned: bool = False

    @field_validator("SECRET_KEY", "JWT_SECRET_KEY", "ADMIN_PASSWORD",
                     "NEO4J_PASSWORD", mode="after")
    @classmethod
    def _warn_dev_defaults(cls, v: str, info) -> str:
        """Warn once if any secret uses its development default."""
        if Settings._warned:
            return v
        dev_markers = ("change-me", "dev-secret", "dev-password", "admin123",
                       "neo4j-dev", "jwt-dev")
        if any(marker in v for marker in dev_markers):
            Settings._warned = True
            warnings.warn(
                f"⚠️  [{info.field_name}] 使用了开发环境默认值！"
                f"生产环境请务必通过环境变量或 .env 文件覆盖。",
                RuntimeWarning,
                stacklevel=2,
            )
        return v


settings = Settings()
