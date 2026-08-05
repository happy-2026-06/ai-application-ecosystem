"""SQLAlchemy declarative base and common mixins."""
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Beijing timezone
_BEIJING_TZ = timezone(timedelta(hours=8))


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def gen_uuid() -> str:
    return str(uuid.uuid4())


def _now_beijing() -> datetime:
    """Return current time in Asia/Shanghai timezone.

    Stores as timezone-aware datetime so the database always knows
    these timestamps are Beijing time, regardless of DB timezone settings.
    """
    return datetime.now(_BEIJING_TZ)


class TimestampMixin:
    """Mixin adding created_at and updated_at timestamp columns (Beijing time, timezone-aware)."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_beijing,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_beijing,
        onupdate=_now_beijing,
        nullable=False,
    )


class UUIDMixin:
    """Mixin adding a UUID primary key."""
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=gen_uuid,
    )
