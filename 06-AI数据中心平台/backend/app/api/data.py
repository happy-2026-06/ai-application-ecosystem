"""Data pipeline API routes."""
import json
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status, Body
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.data import DataSet, DataVersion, DataAnnotation
from app.core.auth import get_current_user
from app.core.security import get_password_hash
from app.schemas.data import (
    DataSetCreate, DataSetResponse, DataVersionResponse,
    AnnotationRequest, AnnotationResponse, QualityReport,
    DashboardStats, CleanRequest,
)
from app.services import data_service

router = APIRouter()


async def internal_call_or_user(
    request: Request,
    x_internal_call: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Accept EITHER X-Internal-Call shared secret OR normal JWT auth.

    Other projects (①⑤⑧ etc.) push data via the X-Internal-Call header
    carrying settings.INTERNAL_CALL_SECRET; these calls are treated as a
    built-in "system" admin user. Regular users keep using JWT Bearer tokens.
    """
    if x_internal_call == settings.INTERNAL_CALL_SECRET:
        # Cross-project internal call: reuse/create a dedicated system user
        result = await db.execute(select(User).where(User.username == "system"))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                username="system",
                email="system@ai-ecosystem.local",
                display_name="系统内部调用",
                hashed_password=get_password_hash(settings.INTERNAL_CALL_SECRET),
                role="admin",
                is_active=True,
            )
            db.add(user)
            await db.flush()
        return user

    # Fall back to JWT auth (raises 401 if missing/invalid).
    # Note: get_current_user normally resolves the token via oauth2_scheme,
    # so extract it from the Authorization header and pass it explicitly.
    authorization = request.headers.get("Authorization", "")
    token = authorization[7:].strip() if authorization.startswith("Bearer ") else ""
    return await get_current_user(token=token, db=db)


# ── DataSets CRUD ─────────────────────────────────────────────────

@router.get("/datasets", response_model=list[DataSetResponse])
async def list_datasets(
    page: int = 1, page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List datasets."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(DataSet).order_by(DataSet.updated_at.desc()).offset(offset).limit(page_size)
    )
    return result.scalars().all()


@router.post("/datasets", response_model=DataSetResponse, status_code=201)
async def create_dataset(
    request: DataSetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new dataset."""
    ds = DataSet(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        source=request.source,
    )
    db.add(ds)
    await db.flush()
    await db.refresh(ds)
    return ds


@router.get("/datasets/{dataset_id}", response_model=DataSetResponse)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dataset details."""
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return ds


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a dataset."""
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")
    ds.status = "archived"
    await db.flush()
    return {"message": "数据集已归档"}


# ── Data Ingestion ────────────────────────────────────────────────

@router.post("/datasets/{dataset_id}/ingest")
async def ingest_data(
    dataset_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ingest raw text data into a dataset."""
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    texts = body.get("texts", [])
    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        raise HTTPException(status_code=400, detail="请提供要采集的数据")

    count = await data_service.ingest_text_data(db, ds, texts)
    return {"message": f"成功采集 {count} 条数据", "count": count}


# ── Data Cleaning ─────────────────────────────────────────────────

@router.post("/datasets/{dataset_id}/clean")
async def clean_dataset(
    dataset_id: str,
    request: CleanRequest = CleanRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clean a dataset."""
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    stats = await data_service.clean_dataset(
        db, ds,
        remove_duplicates=request.remove_duplicates,
        remove_empty=request.remove_empty,
        normalize_text=request.normalize_text,
    )
    return stats


# ── AI Annotation ─────────────────────────────────────────────────

@router.get("/datasets/{dataset_id}/annotations", response_model=list[AnnotationResponse])
async def list_annotations(
    dataset_id: str,
    page: int = 1, page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List annotations for a dataset."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(DataAnnotation)
        .where(DataAnnotation.dataset_id == dataset_id)
        .order_by(DataAnnotation.created_at.desc())
        .offset(offset).limit(page_size)
    )
    return result.scalars().all()


@router.post("/datasets/{dataset_id}/annotate")
async def auto_annotate(
    dataset_id: str,
    request: AnnotationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run AI auto-annotation on selected items."""
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    # Get item IDs based on indices — frontend sends page indices ordered by
    # created_at DESC (same as the annotations list endpoint), so order here
    # must match or the wrong items get annotated.
    items_result = await db.execute(
        select(DataAnnotation)
        .where(DataAnnotation.dataset_id == dataset_id)
        .order_by(DataAnnotation.created_at.desc())
    )
    all_items = list(items_result.scalars().all())
    indices = {item.index for item in request.items}
    target_ids = [all_items[i].id for i in indices if i < len(all_items)]

    if not target_ids:
        raise HTTPException(status_code=400, detail="未找到匹配的数据项")

    stats = await data_service.auto_annotate_items(db, ds, target_ids)
    return stats


@router.patch("/annotations/{annotation_id}")
async def verify_annotation(
    annotation_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually verify/correct an annotation."""
    result = await db.execute(select(DataAnnotation).where(DataAnnotation.id == annotation_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="标注记录不存在")

    if "label" in body:
        ann.label = body["label"]
    if "category" in body:
        ann.category = body["category"]
    if "sentiment" in body:
        ann.sentiment = body["sentiment"]
    ann.is_verified = True
    ann.annotated_by = "manual"
    await db.flush()
    return {"message": "标注已更新"}


# ── Versioning ────────────────────────────────────────────────────

@router.get("/datasets/{dataset_id}/versions", response_model=list[DataVersionResponse])
async def list_versions(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List versions of a dataset."""
    result = await db.execute(
        select(DataVersion)
        .where(DataVersion.dataset_id == dataset_id)
        .order_by(DataVersion.version_number.desc())
    )
    return result.scalars().all()


@router.post("/datasets/{dataset_id}/versions", response_model=DataVersionResponse, status_code=201)
async def create_dataset_version(
    dataset_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new version snapshot."""
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    version = await data_service.create_version(
        db, ds,
        change_log=body.get("change_log"),
        quality_score=body.get("quality_score"),
    )
    return version


# ── Quality Report ────────────────────────────────────────────────

@router.get("/datasets/{dataset_id}/versions/compare")
async def compare_versions(
    dataset_id: str,
    from_v: str,
    to_v: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare two version snapshots of the same dataset.

    Returns both snapshots side by side plus a computed diff
    (item count, AI annotation coverage, verification ratio,
    category distribution and average confidence changes).
    """
    result = await db.execute(
        select(DataVersion).where(
            DataVersion.dataset_id == dataset_id,
            DataVersion.id.in_([from_v, to_v]),
        )
    )
    versions = {str(v.id): v for v in result.scalars().all()}
    if from_v not in versions or to_v not in versions:
        raise HTTPException(status_code=404, detail="版本不存在")

    v_from = versions[from_v]
    v_to = versions[to_v]
    meta_from = v_from.snapshot_meta or {}
    meta_to = v_to.snapshot_meta or {}

    # Category diff (union of both snapshots' categories)
    cats_from = meta_from.get("categories", {})
    cats_to = meta_to.get("categories", {})
    category_diff = {}
    for cat in set(cats_from) | set(cats_to):
        delta = cats_to.get(cat, 0) - cats_from.get(cat, 0)
        if delta != 0:
            category_diff[cat] = delta

    return {
        "dataset_id": dataset_id,
        "from": {
            "id": str(v_from.id),
            "version_number": v_from.version_number,
            "snapshot": meta_from,
            "quality_score": v_from.quality_score,
            "created_at": v_from.created_at.isoformat() if v_from.created_at else None,
        },
        "to": {
            "id": str(v_to.id),
            "version_number": v_to.version_number,
            "snapshot": meta_to,
            "quality_score": v_to.quality_score,
            "created_at": v_to.created_at.isoformat() if v_to.created_at else None,
        },
        "diff": {
            "item_count": meta_to.get("item_count", 0) - meta_from.get("item_count", 0),
            "ai_annotated": meta_to.get("ai_annotated", 0) - meta_from.get("ai_annotated", 0),
            "human_verified": meta_to.get("human_verified", 0) - meta_from.get("human_verified", 0),
            "avg_confidence": round(
                meta_to.get("avg_confidence", 0) - meta_from.get("avg_confidence", 0), 4
            ),
            "quality_score": (v_to.quality_score or 0) - (v_from.quality_score or 0),
            "category_changes": category_diff,
        },
    }


@router.get("/datasets/{dataset_id}/quality")
async def get_quality_report(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get data quality report for a dataset."""
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    return await data_service.generate_quality_report(db, ds)


# ── Dashboard ─────────────────────────────────────────────────────

@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get data center dashboard overview."""
    ds_count = (await db.execute(select(func.count(DataSet.id)))).scalar() or 0
    ann_count = (await db.execute(select(func.count(DataAnnotation.id)))).scalar() or 0
    ai_count = (await db.execute(
        select(func.count(DataAnnotation.id)).where(DataAnnotation.annotated_by == "ai")
    )).scalar() or 0
    verified = (await db.execute(
        select(func.count(DataAnnotation.id)).where(DataAnnotation.is_verified == True)
    )).scalar() or 0

    recent = (await db.execute(
        select(DataSet).order_by(DataSet.updated_at.desc()).limit(6)
    )).scalars().all()

    # Real average quality score across all annotated items (not hardcoded)
    avg_conf = (await db.execute(
        select(func.avg(DataAnnotation.confidence)).where(DataAnnotation.confidence.isnot(None))
    )).scalar()
    avg_confidence = round(float(avg_conf or 0), 4)
    coverage = ai_count / ann_count if ann_count else 0.0
    ver_ratio = verified / ann_count if ann_count else 0.0
    avg_quality = round((avg_confidence * 0.4 + coverage * 0.3 + ver_ratio * 0.3) * 100, 1)

    return {
        "total_datasets": ds_count,
        "total_items": ann_count,
        "total_annotations": ai_count,
        "ai_annotated": ai_count,
        "human_verified": verified,
        "avg_quality_score": avg_quality,
        "recent_datasets": list(recent),
    }


# ── Cross-Project External APIs ──────────────────────────────────

@router.post("/external/ingest")
async def external_ingest(
    body: dict,
    current_user: User = Depends(internal_call_or_user),
    db: AsyncSession = Depends(get_db),
):
    """Receive data from other projects (客服/话术/内容 etc.)."""
    source_project = body.get("source_project", "unknown")
    data_type = body.get("data_type", "text")
    texts = body.get("texts", [])
    dataset_name = body.get("dataset_name", f"来自{source_project}的数据")

    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        raise HTTPException(status_code=400, detail="请提供要接入的数据 (texts)")

    # Find or create auto-import dataset for this project source
    result = await db.execute(
        select(DataSet).where(DataSet.name == dataset_name, DataSet.source == source_project)
    )
    ds = result.scalar_one_or_none()
    if not ds:
        ds = DataSet(
            user_id=current_user.id,
            name=dataset_name,
            description=body.get("description", f"从 {source_project} 自动汇入的{data_type}数据"),
            source=source_project,
        )
        db.add(ds)
        await db.flush()
        await db.refresh(ds)

    count = await data_service.ingest_text_data(db, ds, texts)
    # Auto-clean on ingest
    await data_service.clean_dataset(db, ds)

    return {
        "message": f"成功从 {source_project} 接入 {count} 条数据",
        "dataset_id": str(ds.id),
        "dataset_name": ds.name,
        "count": count,
    }


@router.get("/datasets/{dataset_id}/export-for-finetune")
async def export_for_finetune(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export dataset in finetune-ready format with structured labels.

    Returns samples with text, category, keywords, and label fields
    for ⑧'s Smart Proxy Few-shot retrieval.
    """
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    items_result = await db.execute(
        select(DataAnnotation).where(DataAnnotation.dataset_id == dataset_id)
    )
    items = items_result.scalars().all()

    samples = []
    for item in items[:500]:  # Max 500 samples per export
        sample = {
            "text": item.data_item[:600],
            "label": item.label or "",
            "category": item.category or _infer_category(item.data_item),
            "sentiment": item.sentiment or "",
            "keywords": _extract_keywords(item.data_item, item.category),
        }
        samples.append(sample)

    return {
        "dataset_id": str(ds.id),
        "dataset_name": ds.name,
        "item_count": len(samples),
        "format": "instruction-response-with-labels",
        "samples": samples,
    }


# ── Training Cache API (for ⑧ Smart Proxy) ───────────────────────

@router.get("/datasets/{dataset_id}/training-cache")
async def get_training_cache(
    dataset_id: str,
    current_user: User = Depends(internal_call_or_user),
    db: AsyncSession = Depends(get_db),
):
    """⑧训练完成后拉取结构化训练数据缓存。

    供⑧模型工厂内部调用，不需要认证（用X-Internal-Call头）。
    返回带标签、关键词、类别的训练样本，用于Smart Proxy的Few-shot检索。
    """
    result = await db.execute(select(DataSet).where(DataSet.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    items_result = await db.execute(
        select(DataAnnotation).where(DataAnnotation.dataset_id == dataset_id)
    )
    items = items_result.scalars().all()

    samples = []
    categories_seen: set[str] = set()

    for item in items[:200]:  # Cache up to 200 samples
        category = item.category or _infer_category(item.data_item)
        if category:
            categories_seen.add(category)

        samples.append({
            "text": item.data_item[:500],
            "label": item.label or "",
            "category": category,
            "keywords": _extract_keywords(item.data_item, item.category),
            "sentiment": item.sentiment or "",
        })

    return {
        "dataset_id": str(ds.id),
        "dataset_name": ds.name,
        "total_items": len(samples),
        "domains": list(categories_seen),
        "samples": samples,
    }


# ── Private Helpers ────────────────────────────────────────────────

# Simple keyword-to-category mapping for auto-categorization
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "退货退款": ["退货", "退款", "退换", "退换货", "寄回", "运费险", "退款流程", "收到退款"],
    "促销活动": ["优惠", "满减", "秒杀", "折扣", "活动", "优惠券", "红包", "促销", "限时"],
    "产品参数": ["规格", "参数", "尺寸", "型号", "颜色", "材质", "重量", "容量", "功率"],
    "物流配送": ["发货", "快递", "物流", "配送", "到货", "签收", "包裹", "运输", "包邮"],
    "售后服务": ["售后", "保修", "维修", "投诉", "客服", "质量问题", "故障", "破损"],
    "订单管理": ["订单", "下单", "取消订单", "修改订单", "订单状态", "订单号", "查订单"],
    "支付问题": ["支付", "付款", "微信支付", "支付宝", "银行卡", "分期", "扣款"],
}


def _infer_category(text: str) -> str:
    """Infer the business category from text content via keyword matching."""
    if not text:
        return "通用"
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "通用"


def _extract_keywords(text: str, category: str | None = None) -> list[str]:
    """Extract keywords from text for Few-shot matching."""
    import re
    if not text:
        return []
    # Extract 2-6 char Chinese phrases as candidate keywords
    phrases = re.findall(r'[一-鿿]{2,6}', text)
    # Filter common stop words
    stop_words = {"怎么操作", "可以吗", "是什么", "有没有", "能不能",
                  "我们要", "这是", "需要", "这个", "所以", "因为",
                  "如果", "但是", "而且", "或者", "以及"}
    keywords = [p for p in phrases if p not in stop_words]
    # Return top 8 unique keywords, sorted by length desc
    unique = list(dict.fromkeys(keywords))
    unique.sort(key=len, reverse=True)
    return unique[:8]
