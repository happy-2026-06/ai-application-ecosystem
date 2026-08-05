"""Query router: determine retrieval strategy based on question type.

Classifies user questions to decide which retrieval paths to use:
  - comparison: questions comparing multiple products → Vector + Graph
  - factual: simple attribute lookups → Vector only
  - relationship: entity-relationship queries → Graph + Vector
  - general: chitchat or out-of-scope → Direct LLM

This optimizes performance by avoiding unnecessary Neo4j calls for
simple factual queries that vector search handles well.
"""

from enum import Enum


class QueryType(str, Enum):
    COMPARISON = "comparison"     # e.g., "A 和 B 哪个好？"
    FACTUAL = "factual"           # e.g., "A 的价格是多少？"
    RELATIONSHIP = "relationship" # e.g., "哪些配件兼容 A？"
    GENERAL = "general"           # e.g., "你好"


# Keywords that signal different query types
_COMPARISON_KEYWORDS = [
    "对比", "比较", "区别", "哪个好", "哪个更", "差异",
    "vs", "VS", "versus", "相比", "比起来",
]
_RELATIONSHIP_KEYWORDS = [
    "兼容", "支持", "适用于", "配件", "搭配", "连接",
    "属于", "有哪些", "哪些产品", "什么产品",
]


async def classify_query(question: str) -> QueryType:
    """Classify the query type based on keyword matching.

    In production, this would use an LLM-based classifier for accuracy.
    For the initial implementation, keyword matching is fast and works well
    for common e-commerce query patterns.

    Args:
        question: The user's original question

    Returns:
        QueryType indicating which retrieval strategies to use
    """
    question_lower = question.lower()

    # Check comparison keywords
    if any(kw in question_lower for kw in _COMPARISON_KEYWORDS):
        return QueryType.COMPARISON

    # Check relationship keywords
    if any(kw in question for kw in _RELATIONSHIP_KEYWORDS):
        return QueryType.RELATIONSHIP

    # Check if it's a simple chitchat
    chitchat_keywords = ["你好", "谢谢", "再见", "帮助", "你是谁", "功能"]
    if any(kw in question for kw in chitchat_keywords) and len(question) < 10:
        return QueryType.GENERAL

    # Default: factual lookup
    return QueryType.FACTUAL


def get_retrieval_strategy(query_type: QueryType) -> dict:
    """Map query type to retrieval strategy configuration.

    Returns:
        Dict with flags for {use_vector, use_bm25, use_graph}
    """
    strategies = {
        QueryType.COMPARISON: {
            "use_vector": True,
            "use_bm25": True,
            "use_graph": True,
        },
        QueryType.FACTUAL: {
            "use_vector": True,
            "use_bm25": True,
            "use_graph": False,  # Vector is sufficient for factual queries
        },
        QueryType.RELATIONSHIP: {
            "use_vector": True,
            "use_bm25": False,
            "use_graph": True,   # Graph excels at relationship traversal
        },
        QueryType.GENERAL: {
            "use_vector": False,
            "use_bm25": False,
            "use_graph": False,  # Direct LLM response, no KB needed
        },
    }
    return strategies[query_type]
