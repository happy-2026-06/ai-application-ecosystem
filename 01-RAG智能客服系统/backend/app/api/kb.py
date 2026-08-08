"""Knowledge Base management API routes (Admin only)."""
import asyncio
import hashlib
import logging
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.core.auth import admin_required
from app.schemas.kb import DocumentResponse, DocumentListResponse, KBStatsResponse, JobStatusResponse
from app.config import settings

router = APIRouter()

# ── Filename encoding fix ──────────────────────────────────────────

def _fix_filename(name: str) -> str:
    """Fix garbled filenames from Windows browsers (GBK→Latin-1→UTF-8).

    Some Windows browsers send multipart filenames in system locale (GBK)
    instead of UTF-8 as RFC 5987 requires. This detects garbled names
    and re-encodes them correctly.
    """
    if not name:
        return "untitled"

    # If the name is already valid UTF-8 Chinese, return as-is
    # Try to detect garbled: contains high-byte Latin-1 chars that
    # look like mis-decoded GBK
    try:
        # Encode as Latin-1, then decode as GBK — this fixes "ÃÂ¡ÃÂºÃ..."
        # which is GBK bytes incorrectly interpreted as Latin-1
        latin1_bytes = name.encode("latin-1")
        # Check if the bytes look like valid GBK
        decoded = latin1_bytes.decode("gbk")
        # If successful AND different, use the fixed version
        if decoded != name:
            return decoded
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    # Try UTF-8 fallback
    try:
        name.encode("utf-8")
        return name
    except UnicodeEncodeError:
        pass

    # Last resort: replace invalid chars
    return name.encode("utf-8", errors="replace").decode("utf-8")


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
    # Sanitize filename + fix encoding (Windows browsers send GBK filenames)
    raw_name = str(file.filename) if file.filename else "untitled"
    safe_filename = _fix_filename(os.path.basename(raw_name))
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

    # ── Process document synchronously: user sees "done" when it's really done ──
    # Using asyncio.wait_for as a safety net, but process completes in-process
    from app.services.kb_service import process_document_async

    try:
        await asyncio.wait_for(
            process_document_async(document.id, db),
            timeout=600,  # 10 minutes max
        )
    except asyncio.TimeoutError:
        logger = logging.getLogger(__name__)
        logger.error("Document processing timed out: %s", document.id)
        document.status = "failed"
        document.error_message = "处理超时，请重试"
        await db.flush()
    except Exception as proc_err:
        logger = logging.getLogger(__name__)
        logger.exception("Document processing failed: %s", document.id)

    # Refresh to get the updated status from process_document_async
    await db.refresh(document)
    return document


@router.patch("/documents/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: str,
    original_name: str | None = None,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Update document fields (rename, etc). Supports Form data."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if original_name is not None and original_name.strip():
        new_name = original_name.strip()
        # Ensure file name matches if stored in the same base directory
        if document.file_path and os.path.isfile(document.file_path):
            old_path = document.file_path
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                document.file_path = new_path
            except OSError:
                pass  # If rename fails, still update the DB name
        document.original_name = new_name
        document.filename = new_name

    await db.flush()
    await db.refresh(document)
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


# ── Document Content Preview ──────────────────────────────────────

@router.get("/documents/{doc_id}/content")
async def get_document_content(
    doc_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Get document text content for preview (txt/md/csv + docx/pdf via loader)."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not document.file_path or not os.path.isfile(document.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        content = None

        # Text-based files: direct read with encoding fallback
        if document.file_type in ("txt", "md", "csv"):
            for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]:
                try:
                    with open(document.file_path, "r", encoding=enc) as f:
                        content = f.read()
                    if content.strip():
                        break
                except (UnicodeDecodeError, UnicodeError):
                    continue

        # DOCX: extract text via Docx2txtLoader
        elif document.file_type == "docx":
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(document.file_path)
                docs = loader.load()
                if docs:
                    content = "\n\n".join(d.page_content for d in docs if d.page_content)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning("Docx2txtLoader failed for preview: %s", e)

        # PDF: extract text via PyPDFLoader
        elif document.file_type == "pdf":
            try:
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(document.file_path)
                docs = loader.load()
                if docs:
                    content = "\n\n".join(d.page_content for d in docs if d.page_content)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning("PyPDFLoader failed for preview: %s", e)

        if content:
            return {
                "content": content,
                "file_type": document.file_type,
                "original_name": document.original_name,
            }
        else:
            return {
                "content": None,
                "message": f"无法提取 {document.file_type} 文件的文本内容，请下载后查看",
            }
    except Exception:
        raise HTTPException(status_code=500, detail="读取文件失败")


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
