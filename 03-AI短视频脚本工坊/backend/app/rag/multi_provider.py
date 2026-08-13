"""Multi-provider LLM with automatic failover: DeepSeek → Zhipu GLM → DashScope Qwen.

All three providers expose OpenAI-compatible chat-completions endpoints, so a
single httpx call format covers every provider. When one provider fails
(network / key / rate-limit), the request is retried on the next one.
"""
import logging

import httpx
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk

logger = logging.getLogger(__name__)

# Fallback provider specs: (name, chat-completions URL, model)
PROVIDER_SPECS: list[tuple[str, str, str]] = [
    ("Zhipu GLM", "https://open.bigmodel.cn/api/paas/v4/chat/completions", "glm-4-flash"),
    ("DashScope Qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", "qwen-turbo"),
]


def build_providers_from_keys(zhipu_key: str, dashscope_key: str) -> list[dict]:
    """Build the fallback provider list from configured API keys.

    Empty or placeholder keys (e.g. copied from .env.example) are treated as
    unset and skipped.
    """
    providers = []
    for (name, url, model), key in zip(PROVIDER_SPECS, (zhipu_key, dashscope_key)):
        if key and "your-" not in key.strip().lower():
            providers.append({"name": name, "url": url, "key": key, "model": model})
    return providers


class MultiProviderLLM(LLM):
    """LangChain-compatible LLM that tries multiple OpenAI-compatible providers."""

    providers: list[dict]  # [{name, url, key, model}]

    @property
    def _llm_type(self) -> str:
        return "multi-provider-failover"

    def _call(self, prompt, stop=None, **kwargs) -> str:
        import asyncio
        return asyncio.run(self._acall(prompt, stop, **kwargs))

    async def _acall(self, prompt, stop=None, **kwargs) -> str:
        for p in self.providers:
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(p["url"], headers={
                        "Authorization": f"Bearer {p['key']}",
                        "Content-Type": "application/json",
                    }, json={
                        "model": p["model"],
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 2048,
                    })
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    if p["name"] != "DeepSeek":
                        logger.warning("LLM failover: %s served the request", p["name"])
                    return content
                logger.warning("Provider %s failed: HTTP %s", p["name"], resp.status_code)
            except Exception as e:
                logger.warning("Provider %s error: %s", p["name"], e)
        raise RuntimeError("All AI providers failed")

    def _stream(self, prompt, stop=None, run_manager=None, **kwargs):
        """Yield the complete answer as a single chunk (providers are non-streaming)."""
        yield GenerationChunk(text=self._call(prompt, stop=stop, **kwargs))

    async def _astream(self, prompt, stop=None, run_manager=None, **kwargs):
        """Async single-chunk stream — awaits _acall directly.

        Overriding this avoids the BaseLLM default (which would call _call →
        asyncio.run() from inside a running event loop and raise RuntimeError
        when the chain is streamed from FastAPI).
        """
        yield GenerationChunk(text=await self._acall(prompt, stop=stop, **kwargs))
