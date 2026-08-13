"""Model fine-tuning ORM models — FineTuneTask, ModelVersion, ABTest."""
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, Float, JSON, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class FineTuneTask(Base, UUIDMixin, TimestampMixin):
    """A model fine-tuning task."""
    __tablename__ = "finetune_tasks"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_model: Mapped[str] = mapped_column(String(100), nullable=False, default="deepseek-chat", comment="Base model name")
    dataset_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="Reference to dataset")
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="qlora", comment="qlora/lora/full")
    hyperparams: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="{lr, epochs, batch_size, rank}")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created", comment="created/running/stopped/completed/failed")
    loss_history: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="Training loss per step")
    lr_history: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="Learning rate per step (warmup + cosine decay schedule)")
    eval_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="{bleu, rouge_l, human_score}")
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user = relationship("User")
    model_versions = relationship("ModelVersion", back_populates="task", cascade="all, delete-orphan")
    ab_tests = relationship("ABTest", back_populates="task", cascade="all, delete-orphan")


class ModelVersion(Base, UUIDMixin):
    """A version of a fine-tuned model."""
    __tablename__ = "model_versions"

    task_id: Mapped[str] = mapped_column(ForeignKey("finetune_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    size_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    api_endpoint: Mapped[str | None] = mapped_column(String(300), nullable=True)
    eval_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="{bleu, rouge_l, human_score, final_loss} snapshot at training time")
    # Smart Proxy: training data cache for inference-time Few-shot retrieval
    training_samples_cache: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="Samples from training data for Few-shot injection")
    training_domains: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="Business domains this model was trained on")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("FineTuneTask", back_populates="model_versions")


class ABTest(Base, UUIDMixin):
    """A/B comparison between base and fine-tuned model."""
    __tablename__ = "ab_tests"

    task_id: Mapped[str] = mapped_column(ForeignKey("finetune_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    base_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    finetuned_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    winner: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="base/finetuned/tie")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("FineTuneTask", back_populates="ab_tests")
