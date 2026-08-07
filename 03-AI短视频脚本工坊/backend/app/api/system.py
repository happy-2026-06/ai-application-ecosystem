"""System API routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.auth import admin_required, get_current_user
from app.config import settings

router = APIRouter()


class ConfigUpdateRequest(BaseModel):
    """Request body for updating system configuration."""
    chunk_size: int | None = Field(default=None, ge=100, le=5000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=1000)
    retrieval_top_k: int | None = Field(default=None, ge=1, le=50)
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


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
    body: ConfigUpdateRequest,
    current_user: User = Depends(admin_required),
):
    """Update system configuration (admin only).

    Note: In production, this would persist to the system_config table.
    For now, we validate and respond.
    """
    updates = {}
    if body.chunk_size is not None:
        updates["chunk_size"] = body.chunk_size
    if body.chunk_overlap is not None:
        updates["chunk_overlap"] = body.chunk_overlap
    if body.retrieval_top_k is not None:
        updates["retrieval_top_k"] = body.retrieval_top_k
    if body.similarity_threshold is not None:
        updates["similarity_threshold"] = body.similarity_threshold

    return {"message": "配置已更新", "updates": updates}
