"""Knowledge Base management API routes (Admin only)."""
import asyncio
import hashlib
import logging
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.core.auth import admin_required
from app.schemas.kb import DocumentResponse, DocumentListResponse, KBStatsResponse, JobStatusResponse
from app.config import settings

router = APIRouter()


# ── Document Management (Admin Only) ──────────────────────────────

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """List all documents (admin only, paginated)."""
    query = select(Document)
    count_query = select(func.count(Document.id))

    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to the knowledge base."""
    # Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(file.filename or "untitled")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    # Validate file type
    allowed_extensions = {".pdf", ".txt", ".md", ".csv", ".docx"}
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 '{ext}'。支持: {', '.join(allowed_extensions)}",
        )

    # Validate file size — use chunked reading to avoid OOM on large files
    chunks = []
    while True:
        chunk = await file.read(1024 * 1024)  # 1MB chunks
        if not chunk:
            break
        chunks.append(chunk)
    content = b"".join(chunks)
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE_MB}MB)",
        )

    # Check deduplication: query existing document by hash before creating
    content_hash = hashlib.sha256(content).hexdigest()
    existing = await db.execute(
        select(Document).where(
            Document.content_hash == content_hash,
            Document.status != "failed",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="相同内容的文档已存在")

    # Create document record
    doc_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.UPLOAD_DIR, doc_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, safe_filename)
    with open(file_path, "wb") as f:
        f.write(content)

    document = Document(
        id=doc_id,
        filename=safe_filename,
        original_name=safe_filename,
        file_type=ext.lstrip("."),
        file_size=len(content),
        file_path=file_path,
        content_hash=content_hash,
        status="pending",
        uploaded_by=current_user.id,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # Trigger processing in background (non-blocking, with its own DB session)
    from app.services.kb_service import process_document_async
    from app.db.session import AsyncSessionLocal
    import asyncio as _asyncio

    async def _process_with_own_session():
        async with AsyncSessionLocal() as bg_db:
            try:
                await asyncio.wait_for(
                    process_document_async(document.id, bg_db),
                    timeout=600,  # 10 minutes max
                )
            except asyncio.TimeoutError:
                logger = logging.getLogger(__name__)
                logger.error("Document processing timed out: %s", document.id)
            except Exception:
                logger = logging.getLogger(__name__)
                logger.exception("Background processing failed: %s", document.id)

    asyncio.create_task(_process_with_own_session())

    return document


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its vector data."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # Delete from vector store
    from app.services.kb_service import delete_document_vectors
    await delete_document_vectors(doc_id)

    # Delete file and its directory from disk (path traversal safe: only deletes within upload_dir)
    if document.file_path:
        real_upload_dir = os.path.realpath(settings.UPLOAD_DIR)
        real_file_path = os.path.realpath(document.file_path)
        if real_file_path.startswith(real_upload_dir + os.sep) and os.path.isfile(real_file_path):
            os.remove(real_file_path)
            # Clean up empty parent directory
            parent_dir = os.path.dirname(real_file_path)
            if parent_dir.startswith(real_upload_dir + os.sep) and os.path.isdir(parent_dir):
                try:
                    os.rmdir(parent_dir)
                except OSError:
                    pass  # Directory not empty, leave it

    await db.delete(document)
    await db.flush()
    return {"message": "文档已删除"}


@router.post("/documents/{doc_id}/reprocess")
async def reprocess_document(
    doc_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Re-process a document (re-chunk and re-embed)."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    document.status = "pending"
    document.error_message = None
    await db.flush()

    from app.services.kb_service import process_document_async
    await process_document_async(document.id, db)

    return {"message": "文档已加入处理队列", "doc_id": doc_id}


# ── Statistics ────────────────────────────────────────────────────

@router.get("/stats", response_model=KBStatsResponse)
async def get_kb_stats(
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge base statistics — consolidated single query."""
    result = await db.execute(
        select(
            func.count(Document.id).label("doc_count"),
            func.coalesce(func.sum(Document.chunk_count), 0).label("chunk_count"),
            func.coalesce(func.sum(Document.char_count), 0).label("total_chars"),
            func.coalesce(func.sum(Document.file_size), 0).label("total_size"),
        ).where(Document.status == "completed")
    )
    stats = result.one()

    return KBStatsResponse(
        doc_count=stats.doc_count,
        chunk_count=stats.chunk_count,
        total_chars=stats.total_chars,
        total_size_bytes=stats.total_size,
    )
