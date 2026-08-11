"""Asset ORM model for 图库资产管家."""
from sqlalchemy import ForeignKey, Integer, String, Text, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Asset(Base, UUIDMixin, TimestampMixin):
    """Digital asset — image, video, or document stored in the platform."""
    __tablename__ = "assets"

    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    original_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # 'image/png', 'video/mp4', 'document/pdf'
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=True
    )
    thumbnail_path: Mapped[str] = mapped_column(
        String(500), nullable=True
    )

    # AI-generated tags and description
    tags: Mapped[list | None] = mapped_column(
        JSON, nullable=True  # customer manual tags: ["夕阳", "城市"]
    )
    ai_tags: Mapped[list | None] = mapped_column(
        JSON, nullable=True  # AI auto-generated: ["sunset", "cityscape", "silhouette"]
    )
    ai_description: Mapped[str | None] = mapped_column(
        Text, nullable=True  # AI-generated description of the asset
    )

    # Metadata
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True  # for video
    )

    # Version management
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="processing"
        # processing -> ready -> archived
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_by: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    uploader = relationship("User", backref="assets")

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name={self.original_name}, status={self.status})>"
