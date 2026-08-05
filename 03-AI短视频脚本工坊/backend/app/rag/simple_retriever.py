"""Simple in-memory retriever for dev mode (no ChromaDB/Ollama needed).

Loads text files from a directory and performs keyword-based retrieval.
Used as fallback when ChromaDB is unavailable.
"""
import os
import re
from pathlib import Path

# In-memory document store
_docs: list[dict] = []


def load_documents_from_dir(directory: str) -> int:
    """Load all text files from a directory into the in-memory store.

    Supports: .csv, .txt, .md files.
    Returns the number of chunks loaded.
    """
    global _docs
    _docs = []
    directory = os.path.abspath(directory)

    if not os.path.isdir(directory):
        return 0

    for filepath in Path(directory).rglob("*"):
        if filepath.suffix.lower() not in (".csv", ".txt", ".md"):
            continue
        if filepath.name.startswith("."):
            continue

        try:
            content = filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = filepath.read_text(encoding="gbk")
            except Exception:
                continue

        if not content.strip():
            continue

        doc_name = filepath.name

        # Split into chunks by double newline or sections
        chunks = _split_text(content)

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            _docs.append({
                "content": chunk.strip(),
                "doc_name": doc_name,
                "chunk_index": i,
                "score": None,
            })

    return len(_docs)


def _split_text(text: str, chunk_size: int = 500) -> list[str]:
    """Split text into overlapping chunks."""
    # Try to split by sections first (Markdown headers, double newlines)
    sections = re.split(r'\n(?:#{1,4}\s|={3,}|-{3,})', text)
    if len(sections) <= 1:
        sections = text.split('\n\n')

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            # Further split long sections by sentences (Chinese + English punctuation)
            sentences = re.split(r'(?<=[。！？；…\n])', section)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) <= chunk_size:
                    current += sent
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    current = sent
            if current.strip():
                chunks.append(current.strip())

    return chunks


async def simple_search(query: str, top_k: int = 5) -> list[dict]:
    """Keyword-based search: score documents by word overlap with query.

    Returns list of {content, doc_name, score, ...}
    """
    if not _docs:
        return []

    # Extract keywords from query (Chinese: each character group is a word)
    query_chars = set(query.replace(" ", ""))
    query_words = set(query.lower().split())

    scored = []
    for doc in _docs:
        content = doc["content"]
        # Score by character overlap (for Chinese) + word overlap (for English)
        content_chars = set(content.replace(" ", ""))
        char_overlap = len(query_chars & content_chars) / max(len(query_chars), 1)

        content_lower = content.lower()
        word_hits = sum(1 for w in query_words if w in content_lower)
        word_score = word_hits / max(len(query_words), 1)

        # Combined score (weight: 70% char overlap, 30% keyword)
        score = 0.7 * char_overlap + 0.3 * word_score

        if score > 0.05:  # Minimum threshold
            scored.append({**doc, "score": round(score, 4)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def add_document_chunks(chunks: list[str], doc_id: str, doc_name: str) -> int:
    """Add chunks from a new document to the in-memory store."""
    global _docs
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        _docs.append({
            "content": chunk.strip(),
            "doc_name": doc_name,
            "doc_id": doc_id,
            "chunk_index": i,
            "score": None,
        })
    return len(chunks)


def remove_document(doc_id: str) -> int:
    """Remove all chunks for a document from the in-memory store."""
    global _docs
    before = len(_docs)
    _docs = [d for d in _docs if d.get("doc_id") != doc_id]
    return before - len(_docs)


def get_doc_count() -> int:
    """Return the number of chunks in the in-memory store."""
    return len(_docs)
