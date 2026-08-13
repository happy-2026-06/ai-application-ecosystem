"""LangChain chain assembly for RAG generation.

LLM and chain singletons are cached for performance. Call reset_rag_chain()
after changing runtime configuration (e.g., API key) to invalidate the cache.
"""
import logging
import httpx
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.language_models.llms import LLM
from langchain_deepseek import ChatDeepSeek

from app.config import settings
from app.rag.prompts import RAG_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_llm = None
_chain = None


class _CustomLLMProxy(LLM):
    """LLM wrapper that proxies to ⑧模型工厂's fine-tuned model.

    Parses RAG context from the assembled prompt and passes it as structured
    rag_context so ⑧'s Smart Proxy can combine training data + RAG knowledge.
    """
    proxy_url: str = ""

    @property
    def _llm_type(self) -> str:
        return "custom-finetuned-proxy"

    def _call(self, prompt: str, stop=None, **kwargs) -> str:
        # Parse RAG context from the prompt's [来源:N] markers
        rag_context = _parse_rag_context(prompt)
        # Extract the actual question (everything after "## 用户问题")
        question = _extract_question(prompt)

        payload: dict = {
            "message": question or prompt,
        }
        if rag_context:
            payload["rag_context"] = rag_context

        try:
            resp = httpx.post(self.proxy_url, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            return f"[模型代理错误: HTTP {resp.status_code}]"
        except Exception as e:
            return f"[模型代理连接失败: {e}]"


def _parse_rag_context(prompt: str) -> list[str]:
    """Parse RAG context chunks from LangChain's assembled prompt."""
    import re
    chunks = re.findall(r'\[来源:\d+\]\s*文档:\s*\S+.*?(?=\[来源:\d+\]|## 用户问题|\Z)', prompt, re.DOTALL)
    return [chunk.strip()[:400] for chunk in chunks[:5]]


def _extract_question(prompt: str) -> str:
    """Extract the user's question from the assembled RAG prompt."""
    import re
    match = re.search(r'## 用户问题\s*\n(.*?)(?:\n## AI客服回答|\Z)', prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    return prompt[-500:].strip()


def get_llm():
    """Get or create the LLM singleton.

    If CUSTOM_LLM_URL is set, uses the fine-tuned model from ⑧.
    Otherwise uses the default DeepSeek API.
    """
    global _llm
    if _llm is not None:
        return _llm

    if settings.CUSTOM_LLM_URL:
        logger.info("Using custom fine-tuned model proxy: %s", settings.CUSTOM_LLM_URL)
        _llm = _CustomLLMProxy(proxy_url=settings.CUSTOM_LLM_URL)
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
