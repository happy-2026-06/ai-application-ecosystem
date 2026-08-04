"""Graph retriever: Natural Language → Cypher → Neo4j results.

Converts user questions into Cypher queries using an LLM, executes them
against Neo4j, and returns structured results for the RAG pipeline.
"""
from app.rag.graph.neo4j_client import execute_cypher


async def graph_retrieve(query: str, top_k: int = 10) -> list[dict]:
    """Retrieve information from the knowledge graph.

    Uses few-shot prompting to convert NL → Cypher, then formats
    results as document-like dicts for the RAG pipeline.

    This will be fully implemented in Phase 4 (GraphRAG).

    Returns:
        List of results with {content, doc_name, score, source_type: "graph"}
    """
    # TODO: Implement NL→Cypher with LangChain's GraphCypherQAChain
    # For now, try a simple product name lookup

    # Extract potential product names from the query
    results = []

    # Simple product lookup (to be replaced with LLM-generated Cypher)
    try:
        records = await execute_cypher(
            """
            MATCH (p:Product)
            WHERE toLower(p.name) CONTAINS toLower($query_fragment)
            OPTIONAL MATCH (p)-[:HAS_SPEC]->(s:Spec)
            RETURN p.name as product, collect({key: s.key, value: s.value}) as specs
            LIMIT $limit
            """,
            {"query_fragment": query[:50], "limit": top_k},
        )

        for record in records:
            specs_text = "; ".join(
                f"{s['key']}: {s['value']}" for s in record.get("specs", []) if s["key"]
            )
            content = f"产品: {record['product']}"
            if specs_text:
                content += f"\n规格: {specs_text}"

            results.append({
                "content": content,
                "doc_name": f"知识图谱 - {record['product']}",
                "doc_id": None,
                "score": 0.8,
                "source_type": "graph",
            })
    except Exception:
        pass

    return results
