"""Document ORM model."""
from sqlalchemy import ForeignKey, Integer, String, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    original_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # 'pdf' | 'txt' | 'md' | 'csv' | 'docx'
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=True
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=True  # SHA256 for dedup
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    char_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        # pending | processing | completed | failed
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    uploaded_by: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    uploader = relationship("User", backref="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name={self.original_name}, status={self.status})>"
