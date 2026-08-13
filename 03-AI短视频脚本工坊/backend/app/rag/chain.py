"""LangChain chain assembly for RAG generation.

LLM and chain singletons are cached for performance. Call reset_rag_chain()
after changing runtime configuration (e.g., API key) to invalidate the cache.
"""
import logging
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_deepseek import ChatDeepSeek

from app.config import settings
from app.rag.prompts import RAG_SYSTEM_PROMPT, select_mode_guide
from app.rag.multi_provider import MultiProviderLLM, build_providers_from_keys

logger = logging.getLogger(__name__)

_llm: ChatDeepSeek | None = None
_chain = None


def get_llm() -> ChatDeepSeek:
    """Get or create the LLM singleton (DeepSeek API).

    Raises ValueError if DEEPSEEK_API_KEY is not configured.
    On failure, the singleton is NOT cached — next call retries initialization.
    """
    global _llm
    if _llm is not None:
        return _llm

    if not settings.DEEPSEEK_API_KEY:
        raise ValueError(
            "DeepSeek API key not configured. Set DEEPSEEK_API_KEY in .env file "
            "or via environment variable."
        )

    try:
        _llm = ChatDeepSeek(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            api_base=settings.DEEPSEEK_API_BASE,
            temperature=0.7,       # slightly creative for script writing
            max_tokens=4096,       # video scripts can be lengthy
            streaming=True,
            timeout=60,            # longer timeout for full script generation
            max_retries=3,
        )
        logger.info("DeepSeek LLM initialized: model=%s", settings.DEEPSEEK_MODEL)
        return _llm
    except Exception as e:
        # Do NOT cache a failed instance — allow retry on next request
        logger.error("Failed to initialize DeepSeek LLM: %s", e)
        raise


def get_llm_with_failover():
    """Get the primary LLM or fall back to multi-provider when DeepSeek is unavailable.

    Priority:
      1. ChatDeepSeek (DEEPSEEK_API_KEY set)
      2. MultiProviderLLM (Zhipu GLM / DashScope Qwen keys)

    Raises ValueError when no AI provider key is configured at all.
    """
    try:
        return get_llm()
    except Exception as e:
        logger.warning("Primary LLM unavailable, building fallback: %s", e)

    providers = build_providers_from_keys(settings.ZHIPU_API_KEY, settings.DASHSCOPE_API_KEY)
    if not providers:
        raise ValueError(
            "No AI provider configured. Set DEEPSEEK_API_KEY, ZHIPU_API_KEY or "
            "DASHSCOPE_API_KEY in .env file."
        )
    logger.warning(
        "Using multi-provider fallback LLM: %s",
        ", ".join(p["name"] for p in providers),
    )
    return MultiProviderLLM(providers=providers)


def build_chain(question: str):
    """Build a new LCEL chain with mode-appropriate system prompt.

    The mode guide is selected based on keywords in the user's question
    (带货/测评/开箱) and injected into the system prompt template.

    Args:
        question: The user's raw question, used to detect the desired mode.

    Returns:
        A LangChain Runnable (prompt | llm) ready for streaming.
    """
    mode_guide = select_mode_guide(question)
    system_prompt = SystemMessagePromptTemplate.from_template(RAG_SYSTEM_PROMPT)
    human_prompt = HumanMessagePromptTemplate.from_template(
        "请根据以上规则和参考信息回答用户问题。"
    )
    prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

    # Partially fill the mode_guide so callers only need to pass {context, question}
    prompt_with_mode = prompt.partial(mode_guide=mode_guide)

    llm = get_llm_with_failover()
    return prompt_with_mode | llm


def get_rag_chain():
    """Get or create the RAG chain (backward-compatible singleton).

    Prefer build_chain(question) for new code — it injects the correct
    mode guide for 带货/测评/开箱. This singleton uses the default selling mode.
    """
    global _chain
    if _chain is not None:
        return _chain

    # Default to selling mode for the singleton
    _chain = build_chain("带货")
    logger.info("RAG chain built (default: selling mode)")
    return _chain


def reset_rag_chain() -> None:
    """Reset cached LLM and chain instances.

    Call this after updating settings at runtime (e.g., changing API key,
    model name, or API base URL) so the next request picks up the new config.
    """
    global _llm, _chain
    _llm = None
    _chain = None
    logger.info("RAG chain cache reset — will reinitialize on next request")
