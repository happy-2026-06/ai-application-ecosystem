"""ChromaDB vector store management."""
import asyncio
import logging
import chromadb
from chromadb.errors import InvalidCollectionException
from langchain_chroma import Chroma
from langchain_core.documents import Document as LCDocument

from app.config import settings
from app.rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "kb_chunks"

_chroma_client: chromadb.HttpClient | None = None
_vectorstore: Chroma | None = None


def _get_chroma_client() -> chromadb.HttpClient:
    """Get or create ChromaDB HTTP client singleton."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
    return _chroma_client


def get_vectorstore() -> Chroma:
    """Get or create the Chroma vector store singleton."""
    global _vectorstore
    if _vectorstore is None:
        client = _get_chroma_client()
        embeddings = get_embeddings()

        # Get or create collection with specific error handling
        try:
            collection = client.get_collection(COLLECTION_NAME)
            logger.info(f"Connected to existing ChromaDB collection: {COLLECTION_NAME}")
        except (InvalidCollectionException, ValueError):
            collection = client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Created new ChromaDB collection: {COLLECTION_NAME}")

        _vectorstore = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )
    return _vectorstore


async def _run_sync_in_executor(func, *args, **kwargs):
    """Run a synchronous function in a thread pool executor to avoid blocking."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


async def add_chunks_to_vectorstore(
    chunks: list[LCDocument],
    doc_id: str,
    doc_name: str,
) -> None:
    """Add document chunks to the ChromaDB vector store (async-safe)."""
    vectorstore = get_vectorstore()

    # Enrich metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            "doc_id": doc_id,
            "doc_name": doc_name,
            "chunk_index": i,
        })

    # Add in batches via executor to avoid blocking event loop
    batch_size = 32
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        await _run_sync_in_executor(vectorstore.add_documents, batch)

    logger.info(f"Added {len(chunks)} chunks for document '{doc_name}' ({doc_id})")


async def delete_document_vectors(doc_id: str) -> None:
    """Delete all vectors for a document from ChromaDB (async-safe)."""
    vectorstore = get_vectorstore()
    try:
        await _run_sync_in_executor(vectorstore.delete, where={"doc_id": doc_id})
        logger.info(f"Deleted vectors for document {doc_id}")
    except Exception as e:
        logger.warning(f"Failed to delete vectors for {doc_id}: {e}")


async def similarity_search(
    query: str,
    top_k: int = 5,
    score_threshold: float | None = None,
) -> list[dict]:
    """Perform semantic similarity search (async-safe).

    Uses similarity_search_with_score which returns (doc, distance_score).
    Lower distance = more similar. We convert to a relevance-like score
    and filter by threshold.

    Returns list of dicts with keys: content, doc_name, doc_id, score
    """
    vectorstore = get_vectorstore()

    if score_threshold is None:
        score_threshold = settings.SIMILARITY_THRESHOLD

    # Use similarity_search_with_score for compatibility across LangChain versions
    # Returns List[Tuple[Document, float]] where float is cosine distance (lower = better)
    docs_with_scores = await _run_sync_in_executor(
        vectorstore.similarity_search_with_score,
        query,
        k=top_k,
    )

    results = []
    for doc, distance in docs_with_scores:
        # Convert cosine distance to similarity score (0-1 range)
        # Cosine distance range depends on embedding space, normalize heuristically
        relevance = max(0.0, min(1.0, 1.0 - distance))

        if relevance < score_threshold:
            continue

        results.append({
            "content": doc.page_content,
            "doc_name": doc.metadata.get("doc_name", "未知"),
            "doc_id": doc.metadata.get("doc_id"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "score": round(relevance, 4),
        })

    return results
