"""Smart Proxy — combines intent routing + Few-shot retrieval + response caching.

This is the core of the "micro-tuning hit" mechanism. Instead of just
forwarding requests to DeepSeek with a generic "you are a fine-tuned model"
prompt, we actually inject the training data knowledge into each inference.
"""
import hashlib
import time
import logging
from typing import Any

from app.services.intent_router import match_intent, build_domain_prompt
from app.services.training_retriever import (
    retrieve_relevant_samples,
    format_few_shot_prompt,
)

logger = logging.getLogger(__name__)

# ── Response Cache ─────────────────────────────────────────────────
# In-memory LRU-like cache with TTL.
# Keys are MD5 hashes of the question text.
# For production, this would be Redis.

_response_cache: dict[str, tuple[float, str, str]] = {}
# {cache_key: (timestamp, answer, intent_domain)}

CACHE_TTL_SECONDS = 3600       # 1 hour
MAX_CACHE_SIZE = 256


def _get_cache_key(message: str) -> str:
    """Generate a normalized cache key for a message."""
    # Normalize: lowercase, strip extra whitespace
    normalized = message.lower().strip()
    normalized = " ".join(normalized.split())  # collapse whitespace
    return hashlib.md5(normalized.encode()).hexdigest()


def _check_cache(cache_key: str) -> dict | None:
    """Check if a cached response exists and is not expired."""
    if cache_key in _response_cache:
        ts, answer, intent = _response_cache[cache_key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            logger.info("Cache HIT for key %s (intent: %s)", cache_key[:8], intent)
            return {"response": answer, "cached": True, "intent": intent}
        else:
            # Expired — remove
            del _response_cache[cache_key]
    return None


def _set_cache(cache_key: str, answer: str, intent: str) -> None:
    """Store a response in cache with TTL."""
    # Evict if full
    if len(_response_cache) >= MAX_CACHE_SIZE:
        # Remove oldest 10% of entries
        now = time.time()
        expired = [k for k, v in _response_cache.items() if now - v[0] >= CACHE_TTL_SECONDS]
        for k in expired:
            del _response_cache[k]
        # If still full, remove oldest 20 entries
        if len(_response_cache) >= MAX_CACHE_SIZE:
            sorted_keys = sorted(_response_cache, key=lambda k: _response_cache[k][0])
            for k in sorted_keys[:20]:
                del _response_cache[k]

    _response_cache[cache_key] = (time.time(), answer, intent)
    logger.debug("Cache SET for key %s (size: %d)", cache_key[:8], len(_response_cache))


def get_cache_stats() -> dict:
    """Return cache statistics for monitoring."""
    now = time.time()
    active = sum(1 for ts, _, _ in _response_cache.values() if now - ts < CACHE_TTL_SECONDS)
    return {
        "total_entries": len(_response_cache),
        "active_entries": active,
        "max_size": MAX_CACHE_SIZE,
        "ttl_seconds": CACHE_TTL_SECONDS,
    }


def clear_cache() -> int:
    """Clear all cached responses. Returns count of cleared entries."""
    count = len(_response_cache)
    _response_cache.clear()
    logger.info("Cache cleared: %d entries removed", count)
    return count


# ── Smart Prompt Builder ───────────────────────────────────────────


def build_smart_prompt(
    message: str,
    model_name: str,
    training_domains: list[str] | None = None,
    training_samples_cache: list[dict] | None = None,
    rag_context: list[str] | None = None,
) -> tuple[str, dict]:
    """Build an enhanced prompt with few-shot training data and domain routing.

    This is the main entry point for the Smart Proxy.

    Args:
        message: The user's question/message.
        model_name: Name of the fine-tuned model being used.
        training_domains: Domains this model was trained on.
        training_samples_cache: Cached training data samples.
        rag_context: Optional RAG-retrieved knowledge from the calling system.

    Returns:
        Tuple of (full_prompt, metadata_dict).
    """
    # Layer 1: Intent routing
    intent = match_intent(message, training_domains)
    domain_prompt = build_domain_prompt(intent, model_name)

    # Layer 2: Few-shot retrieval from training data
    few_shots = retrieve_relevant_samples(message, training_samples_cache)
    few_shot_text = format_few_shot_prompt(few_shots)

    # Layer 3: RAG context integration (from calling system)
    rag_text = ""
    if rag_context:
        rag_parts = []
        for i, ctx in enumerate(rag_context[:5], 1):  # max 5 RAG chunks
            if isinstance(ctx, str):
                rag_parts.append(f"[知识库片段 {i}]\n{ctx[:400]}")
            elif isinstance(ctx, dict):
                rag_parts.append(
                    f"[{ctx.get('doc_name', '文档' + str(i))}]\n"
                    f"{ctx.get('content', '')[:400]}"
                )
        if rag_parts:
            rag_text = "## 实时知识库参考\n" + "\n\n".join(rag_parts)

    # Assemble the full prompt
    prompt_parts = [domain_prompt]

    if few_shot_text and few_shot_text != "（无相关训练数据参考）":
        prompt_parts.append(f"\n## 训练数据参考（你已学习过的知识）\n以下是与当前问题相关的训练样本，请参考这些知识来回答问题：\n\n{few_shot_text}")

    if rag_text:
        prompt_parts.append(f"\n{rag_text}")

    prompt_parts.append(f"\n## 当前问题\n{message}")
    prompt_parts.append("\n请基于以上训练数据中学习的知识，给出专业、准确的回答。如果训练数据中有相关答案，优先使用训练数据中的信息。")

    full_prompt = "\n".join(prompt_parts)

    # Build metadata
    metadata = {
        "intent_domain": intent["domain"],
        "intent_confidence": intent["confidence"],
        "few_shot_count": len(few_shots),
        "has_rag_context": bool(rag_context),
        "training_domains": training_domains or [],
    }

    logger.info(
        "Smart prompt built: domain=%s, few_shots=%d, rag=%s, prompt_len=%d",
        intent["domain"], len(few_shots), bool(rag_context), len(full_prompt),
    )

    return full_prompt, metadata
