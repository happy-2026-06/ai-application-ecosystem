"""Message ORM model."""
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin


class Message(Base, UUIDMixin):
    __tablename__ = "messages"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False  # 'user' | 'assistant' | 'system'
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    citations: Mapped[list | None] = mapped_column(
        JSON, nullable=True  # stores list[dict]: [{index, doc_name, content_snippet, score}]
    )
    token_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    feedback: Mapped[str | None] = mapped_column(
        String(20), nullable=True  # 'positive' | 'negative' | None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, session={self.session_id})>"
