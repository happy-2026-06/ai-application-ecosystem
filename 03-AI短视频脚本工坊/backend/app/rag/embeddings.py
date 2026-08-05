"""Embedding model management - BGE-M3 via Ollama."""
from langchain_ollama import OllamaEmbeddings
from app.config import settings

_embedding_model: OllamaEmbeddings | None = None


def get_embeddings() -> OllamaEmbeddings:
    """Get or create the Ollama BGE-M3 embedding model singleton."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL,
            base_url=settings.OLLAMA_HOST,
            num_ctx=4096,
        )
    return _embedding_model


def get_embedding_dim() -> int:
    """Return the embedding dimension."""
    return settings.EMBEDDING_DIM
