"""FastAPI application entry point."""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api import api_router

logger = logging.getLogger(__name__)

# ── Rate limiter ──────────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


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

    # Re-index completed documents into in-memory retriever (survives container restart)
    # Runs on EVERY startup, not just DEBUG mode
    try:
        from app.rag.simple_retriever import add_document_chunks
        from app.rag.simple_retriever import get_doc_count as inmem_count
        from app.rag.simple_retriever import _split_text
        from app.services.kb_service import _read_file, process_document_async
        from sqlalchemy import select
        from app.models.document import Document

        async with AsyncSessionLocal() as db:
            # ── Step 1: Recover stuck documents (pending/processing → retry) ──
            stuck_result = await db.execute(
                select(Document).where(
                    Document.status.in_(["pending", "processing"])
                )
            )
            stuck_docs = stuck_result.scalars().all()
            if stuck_docs:
                print(f"[STARTUP] Found {len(stuck_docs)} stuck documents, re-processing...")
                for doc in stuck_docs:
                    print(f"[STARTUP] Re-processing: {doc.original_name}")
                    try:
                        await process_document_async(doc.id, db)
                        print(f"[STARTUP] Recovered: {doc.original_name}")
                    except Exception as proc_err:
                        print(f"[STARTUP] Failed to recover {doc.original_name}: {proc_err}")

            # ── Step 2: Re-index all completed documents into in-memory retriever ──
            completed_result = await db.execute(
                select(Document).where(Document.status == "completed")
            )
            completed_docs = completed_result.scalars().all()
            print(f"[STARTUP] Found {len(completed_docs)} completed documents in DB")
            for doc in completed_docs:
                if doc.file_path and os.path.isfile(doc.file_path):
                    try:
                        content = await _read_file(doc.file_path, doc.file_type)
                        if content and content.strip():
                            chunks = _split_text(content)
                            add_document_chunks(chunks, doc_id=doc.id, doc_name=doc.original_name)
                            print(f"[STARTUP] Re-indexed {doc.original_name}: {len(chunks)} chunks")
                    except Exception as read_err:
                        print(f"[STARTUP] Failed to read {doc.original_name}: {read_err}")
            print(f"[STARTUP] In-memory retriever: {inmem_count()} total chunks")
    except Exception as e:
        import traceback
        print(f"[STARTUP] Could not re-index documents: {e}")
        traceback.print_exc()

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
    description="电商智能客服助手 — 商品咨询自动应答 · 知识溯源 · 无缝转人工",
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

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
