"""Asset management API routes."""
import asyncio
import hashlib
import logging
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.asset import Asset
from app.core.auth import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["素材管理"])


# ── Upload ──────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    tags: str | None = None,  # comma-separated user tags
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a digital asset (image/video/document)."""
    safe_filename = os.path.basename(file.filename or "untitled")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    # Validate type
    ext = os.path.splitext(safe_filename)[1].lower()
    type_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp",
        ".mp4": "video/mp4", ".mov": "video/mov",
        ".pdf": "document/pdf", ".doc": "document/doc", ".docx": "document/docx",
    }
    file_type = type_map.get(ext, "application/octet-stream")

    # Validate size (200MB max for assets)
    content = await file.read()
    max_size = 200 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 (200MB)")

    # Dedup check
    content_hash = hashlib.sha256(content).hexdigest()

    # Save file
    asset_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.UPLOAD_DIR, "assets", asset_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, safe_filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # Create asset record
    user_tags = [t.strip() for t in (tags or "").split(",") if t.strip()]

    asset = Asset(
        id=asset_id,
        filename=safe_filename,
        original_name=safe_filename,
        file_type=file_type,
        file_size=len(content),
        file_path=file_path,
        tags=user_tags or None,
        ai_tags=None,
        ai_description=None,
        status="processing",
        uploaded_by=current_user.id,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    # Trigger AI tagging in background (with own session)
    async def _ai_tagging():
        async with AsyncSessionLocal() as bg_db:
            try:
                await asyncio.wait_for(
                    _generate_ai_tags(asset_id, bg_db),
                    timeout=120,
                )
            except asyncio.TimeoutError:
                logger.error("AI tagging timed out: %s", asset_id)
            except Exception:
                logger.exception("AI tagging failed: %s", asset_id)

    asyncio.create_task(_ai_tagging())

    return {
        "id": asset.id,
        "filename": asset.original_name,
        "file_type": asset.file_type,
        "file_size": asset.file_size,
        "tags": asset.tags,
        "status": asset.status,
    }


async def _generate_ai_tags(asset_id: str, db: AsyncSession) -> None:
    """Background task: generate AI tags for an asset using LLM."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        return

    try:
        # Try LLM-based tagging first
        name_lower = asset.original_name.lower()
        ext = os.path.splitext(asset.original_name)[1].lower()
        type_label = "图片" if asset.file_type.startswith("image") else ("视频" if asset.file_type.startswith("video") else "文档")

        try:
            from app.rag.chain import get_llm_client
            llm = get_llm_client()
            tagging_prompt = (
                f"你是一个专业的数字资产管理(DAM)标签专家。请为以下素材生成精确的标签和描述。\n\n"
                f"文件名: {asset.original_name}\n"
                f"文件类型: {asset.file_type}（{type_label}）\n"
                f"文件大小: {asset.file_size / 1024:.1f} KB\n\n"
                f"请以JSON格式输出（只输出JSON，不要其他内容）：\n"
                f'{{"tags": ["标签1", "标签2", "标签3", "标签4", "标签5"], "description": "一段简洁的中文描述，包含主体、场景、风格、色调等信息"}}\n\n'
                f"标签要求：\n"
                f"- 3-5个中文标签\n"
                f"- 标签要具体（如'夕阳海滩剪影'而非'风景'）\n"
                f"- 包含：主体、场景、风格、色调等维度\n"
            )
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=tagging_prompt)])
            content = response.content if hasattr(response, 'content') else str(response)

            # Parse JSON
            import json
            content = content.strip()
            if content.startswith("```"):  # Remove markdown code fences
                content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
            if content.startswith("```json"):
                content = content[7:]
            parsed = json.loads(content)
            ai_tags = parsed.get("tags", [])[:8]
            ai_desc = parsed.get("description", f"素材: {asset.original_name}")
        except Exception as e:
            logger.warning("LLM tagging failed, using keyword fallback: %s", e)
            ai_tags = _mock_tag_from_name(name_lower)
            ai_desc = f"素材: {asset.original_name}"

        asset.ai_tags = ai_tags or _mock_tag_from_name(name_lower)
        asset.ai_description = ai_desc or f"素材: {asset.original_name}"
        asset.status = "ready"
        await db.flush()
        await db.commit()
    except Exception as e:
        logger.exception("AI tagging completely failed: %s", asset_id)
        asset.status = "ready"  # Still usable, just no AI tags
        asset.ai_tags = _mock_tag_from_name(asset.original_name.lower())
        ai_desc = f"素材: {asset.original_name}"
        await db.flush()
        await db.commit()


def _mock_tag_from_name(name: str) -> list[str]:
    """Simple mock tag generator from filename (placeholder for CLIP)."""
    tags = []
    if any(w in name for w in ["夕阳", "日落", "sunset"]): tags.append("夕阳")
    if any(w in name for w in ["城市", "city", "天际线"]): tags.append("城市")
    if any(w in name for w in ["海滩", "beach", "海洋"]): tags.append("海滩")
    if any(w in name for w in ["车", "car", "跑车"]): tags.append("汽车")
    if any(w in name for w in ["食物", "food", "美食"]): tags.append("美食")
    if any(w in name for w in ["人物", "portrait", "人像"]): tags.append("人物")
    if any(w in name for w in ["建筑", "building", "arch"]): tags.append("建筑")
    if any(w in name for w in ["风景", "landscape", "自然"]): tags.append("风景")
    if any(w in name for w in ["产品", "product", "商品"]): tags.append("产品")
    if not tags:
        tags = ["未分类"]
    return tags


# ── List & Search ───────────────────────────────────────────────────

@router.get("/list")
async def list_assets(
    page: int = 1,
    page_size: int = 24,
    tag: str | None = None,
    search: str | None = None,
    file_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List assets with optional tag/search/type filter."""
    query = select(Asset).where(Asset.status != "deleted")

    if tag:
        # Filter by tag in either user tags or AI tags
        query = query.where(
            Asset.tags.contains([tag]) | Asset.ai_tags.contains([tag])
        )
    if search:
        query = query.where(
            Asset.filename.ilike(f"%{search}%") |
            Asset.ai_description.ilike(f"%{search}%")
        )
    if file_type:
        query = query.where(Asset.file_type.startswith(file_type))

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Asset.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": a.id,
                "filename": a.original_name,
                "file_type": a.file_type,
                "file_size": a.file_size,
                "tags": a.tags or [],
                "ai_tags": a.ai_tags or [],
                "ai_description": a.ai_description,
                "thumbnail_path": a.thumbnail_path,
                "status": a.status,
                "version": a.version,
                "created_at": a.created_at.isoformat(),
            }
            for a in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── Detail ──────────────────────────────────────────────────────────

@router.get("/{asset_id}")
async def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get asset detail."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")

    return {
        "id": asset.id,
        "filename": asset.original_name,
        "file_type": asset.file_type,
        "file_size": asset.file_size,
        "tags": asset.tags or [],
        "ai_tags": asset.ai_tags or [],
        "ai_description": asset.ai_description,
        "width": asset.width,
        "height": asset.height,
        "duration_seconds": asset.duration_seconds,
        "status": asset.status,
        "version": asset.version,
        "created_at": asset.created_at.isoformat(),
        "updated_at": asset.updated_at.isoformat(),
    }


# ── Delete ──────────────────────────────────────────────────────────

@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an asset."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")

    asset.status = "deleted"
    await db.flush()
    return {"message": "素材已删除"}
