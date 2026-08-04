"""Pydantic schemas for knowledge base management."""
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Document information."""
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    chunk_count: int
    char_count: int
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Paginated document list."""
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class KBStatsResponse(BaseModel):
    """Knowledge base statistics."""
    doc_count: int
    chunk_count: int
    total_chars: int
    total_size_bytes: int
    last_updated: datetime | None = None


class JobStatusResponse(BaseModel):
    """Document processing job status."""
    job_id: str
    status: str  # pending | processing | completed | failed
    progress_pct: float = 0.0
    processed: int = 0
    total: int = 0
    errors: list[str] = []
