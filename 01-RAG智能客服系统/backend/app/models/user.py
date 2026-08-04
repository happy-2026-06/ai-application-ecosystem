"""User ORM model."""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(100), nullable=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
