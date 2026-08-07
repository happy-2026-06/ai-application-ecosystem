"""Pydantic schemas for chat and sessions."""
from datetime import datetime
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Create a new chat session."""
    title: str | None = Field(None, max_length=200, description="会话标题，为空则自动生成")


class SessionUpdate(BaseModel):
    """Update session (rename)."""
    title: str = Field(..., min_length=1, max_length=200)


class SessionResponse(BaseModel):
    """Session list item."""
    id: str
    title: str | None
    session_type: str
    status: str
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """Send a chat message."""
    question: str = Field(..., min_length=1, max_length=5000, description="用户问题")


class CitationSchema(BaseModel):
    """A single citation/reference."""
    doc_name: str
    doc_id: str | None = None
    chunk_id: str | None = None
    content_snippet: str
    score: float | None = None
    page: int | None = None
    section: str | None = None


class MessageResponse(BaseModel):
    """A single message in a session."""
    id: str
    session_id: str
    role: str
    content: str
    citations: list[dict] | None = None
    token_count: int | None = None
    feedback: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    """Submit feedback on an answer."""
    message_id: str
    rating: str = Field(..., pattern="^(positive|negative)$")
    comment: str | None = Field(None, max_length=500)


class EscalateRequest(BaseModel):
    """转人工客服请求（支持 JSON body 和 query string 两种方式）"""
    session_id: str | None = Field(None, description="会话ID（可在 query string 或 body 中提供）")
    reason: str = ""


class EscalateResponse(BaseModel):
    """转人工客服响应"""
    message: str
    ticket_id: int
    queue_length: int
    estimated_wait: str
