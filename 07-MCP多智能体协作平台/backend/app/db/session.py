"""Async SQLAlchemy database engine and session management."""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings

# Use different engine args for SQLite vs PostgreSQL
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_engine_kwargs = {
    "echo": settings.DEBUG,
}
if not _is_sqlite:
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 40,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# SQLite 性能优化：WAL 模式 + 并发参数
# WAL (Write-Ahead Logging): 允许读写并发，大幅提升多用户场景性能
if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")       # 写前日志：读不阻塞写
        cursor.execute("PRAGMA synchronous=NORMAL")      # 减少 fsync 次数
        cursor.execute("PRAGMA cache_size=-8000")        # 缓存 8MB
        cursor.execute("PRAGMA busy_timeout=5000")       # 锁等待 5 秒（默认 0=立即失败）
        cursor.execute("PRAGMA foreign_keys=ON")         # 外键约束
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Dedicated session factory for concurrent agent execution — uses
# pool_pre_ping=False to avoid the "transaction in progress" race
# when multiple agents commit from asyncio.gather() callbacks.
AgentSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (for development use; use Alembic in production)."""
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
