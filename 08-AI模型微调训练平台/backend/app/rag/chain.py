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
from app.rag.prompts import RAG_SYSTEM_PROMPT

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
            temperature=0.3,
            max_tokens=2048,
            streaming=True,
            timeout=30,
            max_retries=3,
        )
        logger.info("DeepSeek LLM initialized: model=%s", settings.DEEPSEEK_MODEL)
        return _llm
    except Exception as e:
        # Do NOT cache a failed instance — allow retry on next request
        logger.error("Failed to initialize DeepSeek LLM: %s", e)
        raise


def get_rag_chain():
    """Get or create the RAG chain using LCEL (LangChain Expression Language).

    Uses SystemMessage for behavioral instructions and HumanMessage for the
    user's question + context.  Returns the cached chain, or builds a new one
    if not yet initialized.
    """
    global _chain
    if _chain is not None:
        return _chain

    llm = get_llm()
    system_prompt = SystemMessagePromptTemplate.from_template(RAG_SYSTEM_PROMPT)
    human_prompt = HumanMessagePromptTemplate.from_template(
        "请根据以上规则和参考信息回答用户问题。"
    )
    prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    _chain = prompt | llm
    logger.info("RAG chain built successfully")
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
