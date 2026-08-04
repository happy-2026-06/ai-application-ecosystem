"""Knowledge Base service: document processing pipeline.

Tries ChromaDB first, falls back to in-memory simple retriever.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document

logger = logging.getLogger(__name__)


async def process_document_async(doc_id: str, db: AsyncSession) -> None:
    """Process a document: load → chunk → store (ChromaDB or in-memory)."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        return

    try:
        document.status = "processing"
        await db.flush()

        # Step 1: Read file content
        content = await _read_file(document.file_path, document.file_type)

        if not content.strip():
            raise ValueError("文档解析结果为空")

        # Step 2: Split into chunks
        from app.rag.simple_retriever import _split_text
        chunks = _split_text(content)
        if not chunks:
            raise ValueError("文档分割结果为空")

        # Step 3: Try ChromaDB first, fall back to in-memory
        stored = False
        try:
            from app.rag.vectorstore import add_chunks_to_vectorstore
            from langchain_core.documents import Document as LCDoc
            lc_docs = [LCDoc(page_content=c, metadata={}) for c in chunks]
            await add_chunks_to_vectorstore(lc_docs, doc_id=doc_id, doc_name=document.original_name)
            stored = True
            logger.info("Stored in ChromaDB: %s", document.original_name)
        except Exception as e:
            logger.warning("ChromaDB unavailable, using in-memory store: %s", e)

        if not stored:
            from app.rag.simple_retriever import add_document_chunks
            add_document_chunks(chunks, doc_id=doc_id, doc_name=document.original_name)
            logger.info("Stored in-memory: %s", document.original_name)

        # Step 4: Update document
        document.chunk_count = len(chunks)
        document.char_count = len(content)
        document.status = "completed"
        document.error_message = None
        await db.flush()

        logger.info("Document '%s': %d chunks, %d chars", document.original_name, len(chunks), len(content))

    except Exception as e:
        document.status = "failed"
        document.error_message = str(e)
        await db.flush()
        logger.exception("Document processing failed: %s", e)
        raise


async def _read_file(file_path: str, file_type: str) -> str:
    """Read file content with automatic encoding detection."""
    if not file_path or not isinstance(file_path, str):
        raise ValueError("Invalid file path")

    # Try langchain loader first
    try:
        from app.rag.loader import load_document
        docs = await asyncio.to_thread(load_document, file_path, file_type)
        if docs:
            return "\n\n".join(d.page_content for d in docs if d.page_content)
    except Exception as e:
        logger.warning("LangChain loader failed, trying raw read: %s", e)

    # Fallback: raw file reading
    content = await asyncio.to_thread(_raw_read, file_path)
    if not content:
        raise ValueError(f"Could not read file: {file_path}")
    return content


def _raw_read(file_path: str) -> str:
    """Raw file reading with encoding fallback."""
    for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Last resort
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


async def delete_document_vectors(doc_id: str) -> None:
    """Delete document from all storage backends."""
    # Try ChromaDB
    try:
        from app.rag.vectorstore import get_vectorstore
        vs = get_vectorstore()
        vs.delete(where={"doc_id": doc_id})
    except Exception:
        pass
    # Try in-memory
    try:
        from app.rag.simple_retriever import remove_document
        remove_document(doc_id)
    except Exception:
        pass
