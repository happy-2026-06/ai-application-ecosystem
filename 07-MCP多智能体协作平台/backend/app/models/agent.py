"""Agent platform ORM models — Agent, Task, Execution."""
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, Float, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class Agent(Base, UUIDMixin, TimestampMixin):
    """A registered AI Agent with capabilities and a unique system prompt."""
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False, comment="Agent role/description")
    capability: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general",
        comment="analysis/content/decision/execution/general"
    )
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Agent's unique system prompt for LLM")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="offline",
        comment="online/offline/busy/error"
    )
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    executions = relationship("Execution", back_populates="agent", cascade="all, delete-orphan")


class Task(Base, UUIDMixin, TimestampMixin):
    """A task to be executed by one or more agents."""
    __tablename__ = "tasks"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pipeline",
        comment="pipeline/parallel/vote/debate"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="pending/running/completed/failed"
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User")
    executions = relationship("Execution", back_populates="task", order_by="Execution.step_order", cascade="all, delete-orphan")


class Execution(Base, UUIDMixin):
    """A single agent execution step within a task."""
    __tablename__ = "executions"

    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[str] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued",
        comment="queued/running/completed/failed"
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    task = relationship("Task", back_populates="executions")
    agent = relationship("Agent", back_populates="executions")
