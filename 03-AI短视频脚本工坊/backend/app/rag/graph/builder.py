"""Knowledge graph builder: extract entities and relations from documents.

⚠️ DEPRECATED — Phase 4 GraphRAG stub (not yet implemented).
   The Neo4j knowledge graph pipeline is not functional in the current release.
   These stubs are kept for future development; do NOT import them in production code.

Planned entities: Brand, Product, Category, Spec, Feature
Planned relations: PRODUCES, BELONGS_TO, HAS_SPEC, HAS_FEATURE, COMPATIBLE_WITH
"""
import warnings
from langchain_core.documents import Document


async def build_knowledge_graph(documents: list[Document]) -> dict:
    """⚠️ DEPRECATED — GraphRAG not yet implemented. Always returns empty stats."""
    warnings.warn(
        "graph.builder.build_knowledge_graph() is a Phase 4 stub and does nothing.",
        FutureWarning,
        stacklevel=2,
    )
    return {"nodes_created": 0, "relations_created": 0}
