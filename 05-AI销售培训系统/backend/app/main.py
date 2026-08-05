"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.api import api_router


# API docs are enabled by default in dev; set ENABLE_DOCS=false to disable in prod
_ENABLE_DOCS = os.environ.get("ENABLE_DOCS", "true").lower() != "false"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    from app.db.session import init_db
    await init_db()
    # Seed admin user
    from app.services.auth_service import seed_admin_user
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await seed_admin_user(db)
        await db.commit()

    # Load sample documents into simple in-memory retriever (dev mode)
    if settings.DEBUG:
        try:
            from app.rag.simple_retriever import load_documents_from_dir, get_doc_count
            sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample-data")
            if os.path.isdir(sample_dir):
                count = load_documents_from_dir(sample_dir)
                print(f"[OK] Loaded {count} chunks from sample documents")
        except Exception as e:
            print(f"[WARN] Could not load sample data: {e}")

    # Security warning on startup if dev defaults are in use
    if "change-me" in settings.SECRET_KEY or "change-me" in settings.JWT_SECRET_KEY:
        print("[WARN] ⚠️  使用了开发环境密钥默认值！生产环境请设置环境变量。")
    if settings.ADMIN_PASSWORD == "admin123":
        print("[WARN] ⚠️  管理员密码为默认值，请登录后立即修改！")

    print(f"[OK] {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    # Shutdown
    from app.db.session import engine
    await engine.dispose()
    print("[OK] Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI销售培训系统 — AI角色扮演 · 多维度实时评分 · 话术训练 · 企业销售培训平台",
    lifespan=lifespan,
    docs_url="/api/docs" if _ENABLE_DOCS else None,
    redoc_url="/api/redoc" if _ENABLE_DOCS else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
