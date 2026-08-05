"""ChatSession ORM model."""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Session(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sessions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=True, default="新会话"
    )
    session_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="qa"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Relationships
    user = relationship("User", backref="sessions")
    messages = relationship(
        "Message", back_populates="session",
        order_by="Message.created_at", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title}, messages={self.message_count})>"
