"""Training session and round ORM models."""
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, Float, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class TrainingSession(Base, UUIDMixin, TimestampMixin):
    """A sales training role-play session."""
    __tablename__ = "training_sessions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="picky/price/hesitant/expert"
    )
    product_context: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Product background info provided by user"
    )
    overall_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Average score across all rounds"
    )
    total_rounds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", comment="active/completed"
    )

    # Relationships
    user = relationship("User", backref="training_sessions")
    rounds = relationship(
        "TrainingRound", back_populates="training_session",
        order_by="TrainingRound.round_number", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TrainingSession(id={self.id}, type={self.customer_type}, rounds={self.total_rounds})>"


class TrainingRound(Base, UUIDMixin):
    """A single round in a training session."""
    __tablename__ = "training_rounds"

    training_session_id: Mapped[str] = mapped_column(
        ForeignKey("training_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    round_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    user_response: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Salesperson's response"
    )
    customer_response: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AI customer's response"
    )
    coach_hint: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Coach improvement hint"
    )
    scores: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="{fluency, persuasiveness, knowledge, objection, emotion}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    training_session = relationship("TrainingSession", back_populates="rounds")

    def __repr__(self) -> str:
        return f"<TrainingRound(round={self.round_number}, session={self.training_session_id})>"
