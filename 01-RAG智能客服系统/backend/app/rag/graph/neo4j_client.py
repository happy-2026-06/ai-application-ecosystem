"""Neo4j connection management for GraphRAG."""
from neo4j import AsyncGraphDatabase
from app.config import settings

_driver = None


def get_neo4j_driver():
    """Get or create Neo4j async driver singleton."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=3600,
            max_connection_pool_size=10,
        )
    return _driver


async def close_neo4j_driver():
    """Close the Neo4j driver."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


async def execute_cypher(query: str, params: dict = None) -> list[dict]:
    """Execute a Cypher query and return results as list of dicts."""
    driver = get_neo4j_driver()
    params = params or {}
    records, _, _ = await driver.execute_query(query, params)
    return [dict(record) for record in records]
