"""Training sample retriever — searches cached training data for relevant Few-shot examples.

When a user asks a question through the fine-tuned model proxy, this service
retrieves the most relevant training samples from the model's training cache
and formats them as Few-shot examples for the LLM prompt.
"""
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Max samples to include in prompt (to control token usage)
MAX_FEW_SHOT_SAMPLES = 3
# Minimum similarity score to include a sample
MIN_SIMILARITY = 0.1


def retrieve_relevant_samples(
    question: str,
    training_cache: list[dict] | None,
    k: int = MAX_FEW_SHOT_SAMPLES,
) -> list[dict]:
    """Retrieve the most relevant training samples for a given question.

    Uses a simple but effective hybrid approach:
    1. Keyword overlap scoring (fast, domain-aware)
    2. Text similarity (fallback for fuzzy matching)

    Args:
        question: The user's question.
        training_cache: List of cached training samples, each with keys:
                        text, category, keywords, label
        k: Number of samples to retrieve.

    Returns:
        List of the top-k most relevant training samples.
    """
    if not training_cache or not question:
        return []

    scored_samples: list[tuple[float, dict]] = []
    question_lower = question.lower().strip()

    for sample in training_cache:
        score = _score_sample(question_lower, sample)
        if score > MIN_SIMILARITY:
            scored_samples.append((score, sample))

    # Sort by score descending, take top k
    scored_samples.sort(key=lambda x: x[0], reverse=True)
    top_k = scored_samples[:k]

    logger.debug(
        "Retrieved %d relevant samples from %d cached (question: '%s')",
        len(top_k), len(training_cache), question[:60],
    )

    return [s for _, s in top_k]


def _score_sample(question_lower: str, sample: dict) -> float:
    """Score a single training sample against the question.

    Uses keyword overlap + text similarity.
    """
    score = 0.0
    sample_text = sample.get("text", "").lower()

    # 1. Keyword match bonus
    keywords = sample.get("keywords", [])
    if keywords:
        matched = sum(1 for kw in keywords if kw.lower() in question_lower)
        score += (matched / max(len(keywords), 1)) * 0.5

    # 2. Category match bonus
    category = sample.get("category", "")
    if category and category.lower() in question_lower:
        score += 0.3

    # 3. Text similarity (fuzzy)
    if sample_text:
        similarity = SequenceMatcher(None, question_lower, sample_text).ratio()
        score += similarity * 0.3

    return min(1.0, score)


def format_few_shot_prompt(samples: list[dict]) -> str:
    """Format retrieved training samples into a Few-shot prompt section.

    Args:
        samples: List of relevant training samples.

    Returns:
        Formatted string ready to inject into the LLM prompt.
    """
    if not samples:
        return "（无相关训练数据参考）"

    parts = []
    for i, sample in enumerate(samples, 1):
        text = sample.get("text", "")
        category = sample.get("category", "")
        label = sample.get("label", "")

        header = f"### 示例 {i}"
        tags = []
        if category:
            tags.append(f"类别: {category}")
        if label:
            tags.append(f"标签: {label}")
        if tags:
            header += f"（{' | '.join(tags)}）"

        # Truncate very long samples
        display_text = text[:600] + ("..." if len(text) > 600 else "")
        parts.append(f"{header}\n{display_text}")

    return "\n\n".join(parts)


def extract_keywords_from_text(text: str) -> list[str]:
    """Extract potential keywords from a training sample text.

    Used when training data doesn't have explicit keyword annotations.
    Simple approach: extract 2-4 character Chinese phrases.

    Args:
        text: The training sample text.

    Returns:
        List of keyword strings.
    """
    import re

    # Extract Chinese words (2-6 chars) that might be keywords
    chinese_words = re.findall(r'[一-鿿]{2,6}', text)
    # Filter common stop words
    stop_words = {"怎么操作", "可以吗", "是什么", "有没有", "能不能",
                  "我们要", "这是", "需要", "这个", "所以", "因为",
                  "如果", "但是", "而且", "或者", "以及", "还有",
                  "我们", "他们", "你们", "什么", "怎么", "为什么"}
    keywords = [w for w in chinese_words if w not in stop_words]
    # Return unique, sorted by length (longer = more specific)
    unique = list(dict.fromkeys(keywords))  # preserve order, remove dupes
    unique.sort(key=len, reverse=True)
    return unique[:10]
