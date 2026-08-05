"""Knowledge graph builder: extract entities and relations from documents.

Uses LLMGraphTransformer to build a Neo4j knowledge graph from document chunks.
The graph captures:
  - Entities: Brand, Product, Category, Spec, Feature
  - Relations: PRODUCES, BELONGS_TO, HAS_SPEC, HAS_FEATURE, COMPATIBLE_WITH
"""
import asyncio
from langchain_core.documents import Document

from app.rag.graph.neo4j_client import execute_cypher


async def build_knowledge_graph(documents: list[Document]) -> dict:
    """Build or update the knowledge graph from document chunks.

    In production, this uses LLMGraphTransformer to extract entities and
    relations automatically. For the initial implementation, we seed the
    graph with structured product data from CSV or formatted documents.

    Args:
        documents: List of LangChain Document objects

    Returns:
        Stats dict with counts of nodes and relationships created
    """
    # Ensure graph schema exists
    await _ensure_schema()

    stats = {"nodes_created": 0, "relations_created": 0}

    # This is a placeholder for the full LLMGraphTransformer implementation
    # which will be implemented in Phase 4 (GraphRAG)

    return stats


async def _ensure_schema():
    """Create indexes and constraints if they don't exist."""
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
    ]
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (s:Spec) ON (s.key, s.value)",
        "CREATE INDEX IF NOT EXISTS FOR (f:Feature) ON (f.name)",
    ]

    for c in constraints:
        try:
            await execute_cypher(c)
        except Exception:
            pass

    for idx in indexes:
        try:
            await execute_cypher(idx)
        except Exception:
            pass
