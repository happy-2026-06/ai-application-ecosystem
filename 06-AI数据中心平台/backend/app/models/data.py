"""Data pipeline ORM models — DataSet, DataVersion, DataAnnotation."""
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, Float, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class DataSet(Base, UUIDMixin, TimestampMixin):
    """A dataset — a collection of data items with versions and annotations."""
    __tablename__ = "datasets"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="upload",
        comment="upload/api/crawl/manual — where the data came from"
    )
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="raw",
        comment="raw/cleaning/annotating/ready/archived"
    )
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user = relationship("User", backref="datasets")
    versions = relationship("DataVersion", back_populates="dataset",
        order_by="DataVersion.version_number.desc()", cascade="all, delete-orphan")
    annotations = relationship("DataAnnotation", back_populates="dataset",
        cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DataSet(id={self.id}, name={self.name}, items={self.item_count})>"


class DataVersion(Base, UUIDMixin):
    """A snapshot/version of a dataset."""
    __tablename__ = "data_versions"

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    change_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapshot_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    dataset = relationship("DataSet", back_populates="versions")

    def __repr__(self) -> str:
        return f"<DataVersion(dataset={self.dataset_id}, v{self.version_number})>"


class DataAnnotation(Base, UUIDMixin):
    """AI annotation record for a data item."""
    __tablename__ = "data_annotations"

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data_item: Mapped[str] = mapped_column(Text, nullable=False, comment="The raw data item text")
    label: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="AI-generated label")
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="positive/negative/neutral")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True, comment="LLM confidence score")
    is_verified: Mapped[bool] = mapped_column(default=False, comment="Human verified flag")
    annotation_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    annotated_by: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ai", comment="ai/manual"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    dataset = relationship("DataSet", back_populates="annotations")

    def __repr__(self) -> str:
        return f"<DataAnnotation(id={self.id}, label={self.label}, verified={self.is_verified})>"
