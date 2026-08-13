"""Cross-project data push client — sends data to 数据中枢(⑥)."""
import logging
import re
import httpx

logger = logging.getLogger(__name__)

DATAHUB_URL = "http://p6-backend:8000/api/data/external/ingest"
# Fallback for local dev
DATAHUB_URL_LOCAL = "http://localhost:8606/api/data/external/ingest"


def _clean_text(text: str, max_len: int = 300) -> str:
    """Clean pushed text: strip markdown/emoji, collapse whitespace, truncate.

    Data pushed to ⑥ will be displayed and annotated there — raw LLM output
    contains markdown symbols (**bold**, - lists) and emoji that look like
    garbled noise in the dataset list.
    """
    text = re.sub(r'\*\*|__|~~|`', '', text)          # markdown bold/italic/strike/code
    text = re.sub(r'[\U0001F300-\U0001FAFF☀-➿️‍]', '', text)  # emoji
    text = re.sub(r'^\s*[-*+]\s+', '· ', text, flags=re.MULTILINE)  # list bullets at line start
    text = re.sub(r'([。！？：；])\s*[-*]\s+', r'\1 ', text)  # inline list markers after punctuation
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len] + '…'
    return text


async def push_chat_to_datahub(
    username: str,
    question: str,
    answer: str,
    sources: list[dict] | None = None,
) -> bool:
    """Push a chat Q&A pair to the data hub as training data."""
    q = _clean_text(question, 100)
    a = _clean_text(answer, 300)
    text = f"Q: {q}\nA: {a}"
    if sources:
        src_text = " | ".join(s.get("doc_name", "") for s in sources[:3])
        text += f"\n[来源: {src_text}]"

    return await _push("客服助手", "chat_qa", [text], f"来自客服的对话数据")


async def push_training_to_datahub(
    username: str,
    customer_type: str,
    rounds_data: list[dict],
) -> bool:
    """Push training session data to the data hub."""
    texts = []
    for r in rounds_data:
        scores = r.get("scores", {})
        score_str = ", ".join(f"{k}={v}" for k, v in scores.items()) if scores else "no scores"
        text = (
            f"[{customer_type}客户] 销售: {r.get('user_response', '')[:300]} | "
            f"客户回应: {r.get('customer_response', '')[:300]} | "
            f"评分: {score_str}"
        )
        texts.append(text)

    return await _push("话术教练", "training_data", texts, f"话术训练-{customer_type}客户")


async def push_asset_tags_to_datahub(
    filename: str,
    ai_description: str,
    ai_tags: list[str],
) -> bool:
    """Push an asset's AI-generated tags/description to the data hub.

    The hub uses these as annotation reference material (④ → ⑥ 数据飞轮).
    """
    tags_str = ", ".join(ai_tags) if ai_tags else ""
    desc = _clean_text(ai_description or "", 200)
    text = f"素材: {filename} | 描述: {desc} | 标签: {tags_str}"
    return await _push("图库管家", "asset_tags", [text], "素材标签参考")


async def _push(
    source_project: str,
    data_type: str,
    texts: list[str],
    dataset_name: str,
) -> bool:
    """Push data to the data hub via HTTP POST."""
    payload = {
        "source_project": source_project,
        "data_type": data_type,
        "texts": texts,
        "dataset_name": dataset_name,
        "description": f"从 {source_project} 自动汇入的{data_type}数据",
    }

    admin_auth = _get_admin_auth_header()

    for url in [DATAHUB_URL, DATAHUB_URL_LOCAL]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=admin_auth)
                if resp.status_code in (200, 201):
                    logger.info(
                        "DataHub push OK: %s -> %s (%d items)",
                        source_project, dataset_name, len(texts),
                    )
                    return True
                logger.warning(
                    "DataHub push failed (%s): status=%d %s",
                    url, resp.status_code, resp.text[:200],
                )
        except Exception as e:
            logger.debug("DataHub push attempt failed (%s): %s", url, e)

    return False


def _get_admin_auth_header() -> dict:
    """Get auth header for data hub API calls.

    Cross-project internal calls authenticate via the X-Internal-Call header
    carrying the shared secret (configured as INTERNAL_CALL_SECRET in ⑥'s
    config.py). The data hub accepts this instead of a JWT for machine-to-
    machine pushes from other projects in the ecosystem.
    """
    return {"X-Internal-Call": "ai-ecosystem-internal-2026"}


async def push_generated_content_to_datahub(
    source_project: str,
    title: str,
    content: str,
    platform: str = "",
) -> bool:
    """Push generated content (文案/脚本) to data hub."""
    text = f"[{platform}] {title}\n{content[:500]}"
    return await _push(source_project, "generated_content", [text], f"来自{source_project}的内容")
