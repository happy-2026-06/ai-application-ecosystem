"""System API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.auth import admin_required, get_current_user
from app.config import settings

router = APIRouter()


@router.get("/config")
async def get_config(current_user: User = Depends(get_current_user)):
    """Get system configuration (public settings only)."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.DEEPSEEK_MODEL,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "retrieval_top_k": settings.RETRIEVAL_TOP_K,
    }


@router.put("/config")
async def update_config(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    retrieval_top_k: int | None = None,
    similarity_threshold: float | None = None,
    current_user: User = Depends(admin_required),
):
    """Update system configuration (admin only).

    Note: In production, this would persist to the system_config table.
    For now, we validate and respond.
    """
    updates = {}
    if chunk_size is not None:
        if not (100 <= chunk_size <= 5000):
            return {"error": "chunk_size must be between 100 and 5000"}
        updates["chunk_size"] = chunk_size
    if chunk_overlap is not None:
        if not (0 <= chunk_overlap <= 1000):
            return {"error": "chunk_overlap must be between 0 and 1000"}
        updates["chunk_overlap"] = chunk_overlap
    if retrieval_top_k is not None:
        if not (1 <= retrieval_top_k <= 50):
            return {"error": "retrieval_top_k must be between 1 and 50"}
        updates["retrieval_top_k"] = retrieval_top_k
    if similarity_threshold is not None:
        if not (0.0 <= similarity_threshold <= 1.0):
            return {"error": "similarity_threshold must be between 0 and 1"}
        updates["similarity_threshold"] = similarity_threshold

    return {"message": "配置已更新", "updates": updates}
