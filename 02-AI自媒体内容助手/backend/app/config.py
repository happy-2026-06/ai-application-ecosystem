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
    APP_NAME: str = "灵笔内容引擎"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(
        default="sm-creator-dev-secret-must-override-in-prod-7b2e",
        description="Used by FastAPI/Starlette for session signing. Override in production!",
    )

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/selfmedia.db",
        description="Async database URL. For PostgreSQL, set postgresql+asyncpg://user:pass@host/db",
    )
    DATABASE_URL_SYNC: str = Field(
        default="sqlite:///./data/selfmedia.db",
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

    # ── Fallback AI Providers (DeepSeek 失败时自动回退) ───────────────
    ZHIPU_API_KEY: str = ""
    DASHSCOPE_API_KEY: str = ""

    # ── Custom Model (微调模型代理) ───────────────────────────────────
    CUSTOM_LLM_URL: str = Field(
        default="",
        description="如果设置，将使用⑧模型工厂的微调模型代理替代默认DeepSeek"
    )

    # ── LLM Fallback (Ollama) ─────────────────────────────────────────
    OLLAMA_LLM_MODEL: str = "qwen2.5:7b"

    # ── JWT ──────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        default="sm-creator-jwt-dev-key-must-override-in-prod-9e1a",
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
        default=["http://localhost:3002", "http://localhost:80", "http://localhost"],
    )

    # ── Pre-seeded admin account ─────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = Field(
        default="SM-creator-admin-2024!",
        description="Initial admin password. CHANGE IT after first login!",
    )
    ADMIN_EMAIL: str = "admin@selfmedia.local"

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

    @field_validator("SECRET_KEY", "JWT_SECRET_KEY", "ADMIN_PASSWORD",
                     "NEO4J_PASSWORD", mode="after")
    @classmethod
    def _warn_dev_defaults(cls, v: str, info) -> str:
        """Warn once per field if it uses its development default."""
        if not hasattr(cls, '__warned_fields'):
            cls.__warned_fields = set()
        field_name = info.field_name
        if field_name in cls.__warned_fields:
            return v
        dev_markers = ("change-me", "dev-secret", "dev-password", "admin123",
                       "neo4j-dev", "jwt-dev", "must-override", "SM-creator")
        if any(marker in v for marker in dev_markers):
            cls.__warned_fields.add(field_name)
            warnings.warn(
                f"⚠️  [{field_name}] 使用了开发环境默认值！"
                f"生产环境请务必通过环境变量或 .env 文件覆盖。",
                RuntimeWarning,
                stacklevel=2,
            )
        return v


settings = Settings()
