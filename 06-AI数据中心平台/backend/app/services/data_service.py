"""Data pipeline service: collection, cleaning, annotation, versioning."""
import logging
import re
import json
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data import DataSet, DataVersion, DataAnnotation
from app.config import settings

logger = logging.getLogger(__name__)

# ── Data Collection ───────────────────────────────────────────────

async def ingest_text_data(
    db: AsyncSession,
    dataset: DataSet,
    texts: list[str],
) -> int:
    """Ingest raw text items into a dataset (as annotation records)."""
    count = 0
    for text in texts:
        text = text.strip()
        if not text:
            continue
        annotation = DataAnnotation(
            dataset_id=dataset.id,
            data_item=text,
            annotated_by="raw",
            is_verified=False,
        )
        db.add(annotation)
        count += 1

    dataset.item_count += count
    await db.flush()
    return count


# ── Data Cleaning ─────────────────────────────────────────────────

async def clean_dataset(
    db: AsyncSession,
    dataset: DataSet,
    remove_duplicates: bool = True,
    remove_empty: bool = True,
    normalize_text: bool = True,
) -> dict:
    """Clean a dataset: dedup, remove empty, normalize."""
    result = await db.execute(
        select(DataAnnotation).where(DataAnnotation.dataset_id == dataset.id)
    )
    items = result.scalars().all()

    stats = {"before": len(items), "after": 0, "duplicates_removed": 0, "empty_removed": 0}
    seen = set()
    to_keep = []

    for item in items:
        text = item.data_item.strip()

        # Remove empty
        if remove_empty and not text:
            stats["empty_removed"] += 1
            await db.delete(item)
            continue

        # Normalize
        if normalize_text:
            text = re.sub(r'\s+', ' ', text)
            item.data_item = text

        # Remove duplicates
        normalized = text.lower().strip()
        if remove_duplicates and normalized in seen:
            stats["duplicates_removed"] += 1
            await db.delete(item)
            continue

        seen.add(normalized)
        to_keep.append(item)

    stats["after"] = len(to_keep)
    dataset.item_count = stats["after"]
    dataset.status = "ready" if stats["after"] > 0 else "raw"
    await db.flush()

    return stats


# ── AI Annotation ─────────────────────────────────────────────────

ANNOTATION_PROMPT = """你是一个数据标注专家。请对以下文本进行分析，返回JSON格式结果（不要多余解释）：

{"label": "最合适的标签(2-4字中文)", "category": "分类(qa/content/review/data/other)", "sentiment": "情感(positive/negative/neutral)"}

文本: {text}"""


async def auto_annotate_items(
    db: AsyncSession,
    dataset: DataSet,
    item_ids: list[str],
) -> dict:
    """Run AI annotation on selected data items."""
    result = await db.execute(
        select(DataAnnotation).where(
            DataAnnotation.id.in_(item_ids),
            DataAnnotation.dataset_id == dataset.id,
        )
    )
    items = result.scalars().all()

    annotated = 0
    llm = None
    try:
        from app.rag.chain import get_llm
        llm = get_llm()
    except Exception:
        pass

    for item in items:
        try:
            prompt = ANNOTATION_PROMPT.format(text=item.data_item[:2000])
            if llm:
                response = await llm.ainvoke(prompt)
                raw = response.content if hasattr(response, "content") else str(response)
                parsed = _parse_annotation_response(raw)
            else:
                parsed = _fallback_annotation(item.data_item)

            item.label = parsed.get("label")
            item.category = parsed.get("category")
            item.sentiment = parsed.get("sentiment")
            item.confidence = parsed.get("confidence", 0.7)
            item.annotated_by = "ai"
            annotated += 1
        except Exception as e:
            logger.warning("Annotation failed for item %s: %s", item.id, e)
            parsed = _fallback_annotation(item.data_item)
            item.label = parsed.get("label")
            item.category = parsed.get("category")
            item.sentiment = parsed.get("sentiment")
            item.confidence = 0.3
            item.annotated_by = "ai"
            annotated += 1

    dataset.status = "annotating"
    await db.flush()
    return {"annotated": annotated, "total": len(items)}


def _parse_annotation_response(raw: str) -> dict:
    """Parse LLM annotation response, extracting JSON."""
    try:
        # Try direct JSON parse
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try to extract JSON from markdown code block
    match = re.search(r'\{[^}]+\}', raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"label": "未分类", "category": "other", "sentiment": "neutral", "confidence": 0.3}


def _fallback_annotation(text: str) -> dict:
    """Keyword-based fallback annotation when LLM unavailable."""
    text_lower = text.lower()
    # Simple keyword rules
    if any(k in text_lower for k in ["问题", "怎么", "如何", "什么", "help"]):
        label, cat = "用户问题", "qa"
    elif any(k in text_lower for k in ["价格", "便宜", "贵", "优惠", "折扣"]):
        label, cat = "价格咨询", "qa"
    elif any(k in text_lower for k in ["标题", "文案", "创作", "生成"]):
        label, cat = "内容创作", "content"
    elif any(k in text_lower for k in ["好评", "满意", "不错", "好"]):
        label, cat = "正面评价", "review"
    elif any(k in text_lower for k in ["差评", "不好", "垃圾", "烂"]):
        label, cat = "负面评价", "review"
    else:
        label, cat = "通用数据", "data"

    # Sentiment
    pos_words = ["好", "满意", "不错", "喜欢", "赞", "优秀"]
    neg_words = ["差", "不好", "垃圾", "烂", "失望", "投诉"]
    pos = sum(1 for w in pos_words if w in text_lower)
    neg = sum(1 for w in neg_words if w in text_lower)
    if pos > neg:
        sentiment = "positive"
    elif neg > pos:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {"label": label, "category": cat, "sentiment": sentiment, "confidence": 0.5}


# ── Versioning ────────────────────────────────────────────────────

async def create_version(
    db: AsyncSession,
    dataset: DataSet,
    change_log: str | None = None,
    quality_score: float | None = None,
) -> DataVersion:
    """Create a snapshot version of the current dataset state."""
    # Count current items
    count_result = await db.execute(
        select(func.count()).select_from(DataAnnotation).where(
            DataAnnotation.dataset_id == dataset.id
        )
    )
    item_count = count_result.scalar() or 0

    # Build a real snapshot of annotation state for later comparison
    ann_result = await db.execute(
        select(DataAnnotation).where(DataAnnotation.dataset_id == dataset.id)
    )
    items = ann_result.scalars().all()

    ai_annotated = sum(1 for i in items if i.annotated_by == "ai")
    human_verified = sum(1 for i in items if i.is_verified)
    categories: dict[str, int] = {}
    confidences: list[float] = []
    for item in items:
        if item.category:
            categories[item.category] = categories.get(item.category, 0) + 1
        if item.confidence is not None:
            confidences.append(item.confidence)
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

    snapshot_meta = {
        "item_count": item_count,
        "ai_annotated": ai_annotated,
        "human_verified": human_verified,
        "categories": categories,
        "avg_confidence": avg_confidence,
    }

    # Derive a quality score when none is supplied (same formula as quality report)
    if quality_score is None:
        coverage = ai_annotated / item_count if item_count else 0.0
        ver_ratio = human_verified / item_count if item_count else 0.0
        quality_score = round(
            (avg_confidence * 0.4 + coverage * 0.3 + ver_ratio * 0.3) * 100, 1
        )

    # Get the next version number
    ver_result = await db.execute(
        select(func.max(DataVersion.version_number)).where(
            DataVersion.dataset_id == dataset.id
        )
    )
    max_ver = ver_result.scalar() or 0
    version = DataVersion(
        dataset_id=dataset.id,
        version_number=max_ver + 1,
        item_count=item_count,
        change_log=change_log,
        quality_score=quality_score,
        snapshot_meta=snapshot_meta,
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)
    return version


# ── Quality Report ────────────────────────────────────────────────

async def generate_quality_report(
    db: AsyncSession,
    dataset: DataSet,
) -> dict:
    """Generate a data quality report for a dataset."""
    items_result = await db.execute(
        select(DataAnnotation).where(DataAnnotation.dataset_id == dataset.id)
    )
    items = items_result.scalars().all()

    total = len(items)
    annotated = sum(1 for i in items if i.annotated_by == "ai")
    verified = sum(1 for i in items if i.is_verified)

    # Label distribution
    label_dist = {}
    cat_dist = {}
    confidences = []
    for item in items:
        if item.label:
            label_dist[item.label] = label_dist.get(item.label, 0) + 1
        if item.category:
            cat_dist[item.category] = cat_dist.get(item.category, 0) + 1
        if item.confidence is not None:
            confidences.append(item.confidence)

    avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0
    completeness = round(annotated / total * 100, 1) if total > 0 else 0
    quality_score = round(
        (avg_conf * 0.4 + (completeness / 100) * 0.3 + (verified / max(total, 1)) * 0.3) * 100, 1
    )

    return {
        "dataset_id": str(dataset.id),
        "dataset_name": dataset.name,
        "total_items": total,
        "annotated_items": annotated,
        "verified_items": verified,
        "label_distribution": label_dist,
        "category_distribution": cat_dist,
        "avg_confidence": avg_conf,
        "quality_score": quality_score,
        "completeness": completeness,
    }
