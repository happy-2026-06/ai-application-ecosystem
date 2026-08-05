"""Hybrid retrieval: vector similarity + optional BM25 + Graph.

This module implements multi-strategy retrieval:
1. Vector semantic search via ChromaDB
2. Keyword search via BM25 (for exact product codes/model numbers)
3. Graph search via Neo4j (for entity-relationship queries) [optional]

Results are fused using Reciprocal Rank Fusion (RRF).
"""
import asyncio
from app.rag.vectorstore import similarity_search
from app.config import settings


async def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    use_hybrid: bool = True,
    use_graph: bool = False,
) -> list[dict]:
    """Retrieve the most relevant chunks for a query.

    Args:
        query: The user's question
        top_k: Number of final results to return
        use_hybrid: Enable BM25 keyword search in addition to vector
        use_graph: Enable Neo4j graph retrieval (GraphRAG)

    Returns:
        List of dicts with {content, doc_name, doc_id, score, source_type}
    """
    # Vector semantic search (always used)
    vector_results = await similarity_search(
        query=query,
        top_k=settings.RETRIEVAL_TOP_K,
    )

    results = [{"source_type": "vector", **r} for r in vector_results]

    # BM25 keyword search (optional)
    if use_hybrid:
        try:
            bm25_results = await _bm25_search(query, top_k=settings.RETRIEVAL_TOP_K)
            results.extend([{"source_type": "bm25", **r} for r in bm25_results])
        except Exception:
            pass  # BM25 not available, fall back to vector-only

    # Graph search (optional, for GraphRAG)
    if use_graph:
        try:
            graph_results = await _graph_search(query, top_k=settings.RETRIEVAL_TOP_K)
            results.extend([{"source_type": "graph", **r} for r in graph_results])
        except Exception:
            pass  # Neo4j not available, fall back

    # Simple RRF-like fusion: deduplicate by content and sort by score
    seen = set()
    fused = []
    for r in sorted(results, key=lambda x: x.get("score", 0), reverse=True):
        key = r["content"][:100]  # Use first 100 chars as dedup key
        if key not in seen:
            seen.add(key)
            fused.append(r)

    return fused[:top_k]


async def _bm25_search(query: str, top_k: int = 20) -> list[dict]:
    """BM25 keyword-based retrieval — ⚠️ NOT YET IMPLEMENTED.

    Planned for Phase 5: exact product code / model number matching.
    Currently returns an empty list; hybrid retrieval falls back to vector-only.
    """
    return []


async def _graph_search(query: str, top_k: int = 20) -> list[dict]:
    """Neo4j graph-based retrieval — ⚠️ NOT YET IMPLEMENTED (Phase 4 stub).

    Planned: NL → Cypher via LangChain's GraphCypherQAChain.
    Currently returns an empty list; callers fall back to vector search.
    """
    return []
