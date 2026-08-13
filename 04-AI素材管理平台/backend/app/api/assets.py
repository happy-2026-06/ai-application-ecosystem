"""Asset management API routes."""
import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import re
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Body, Request, Form
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, cast, String, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.asset import Asset
from app.core.auth import get_current_user, oauth2_scheme
from app.core.security import decode_token
from app.config import settings
from app.schemas.asset import (
    AssetUpdateRequest,
    AssetResponse,
    AssetListResponse,
    AssetStatsResponse,
    PopularTagsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["图库管理"])


# ═══════════════════════════════════════════════════════════════════════
# Auth helpers (must be defined BEFORE routes that reference them)
# ═══════════════════════════════════════════════════════════════════════

async def _try_get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Optional auth: return user if token is valid, None otherwise."""
    try:
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None


async def _get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """Extract user from a raw JWT token string (for query-param auth)."""
    try:
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════
# Static-path routes (MUST be defined BEFORE /{asset_id} wildcard routes)
# ═══════════════════════════════════════════════════════════════════════

# ── Upload ──────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    tags: str | None = Form(None, description="Comma-separated user tags"),
    filename: str | None = Form(None, description="Custom filename (without extension)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a digital asset (image/video/document)."""
    logger.info(f"UPLOAD START: filename={file.filename}, content_type={file.content_type}, size_hint={file.size}, user={current_user.username}")

    safe_filename = os.path.basename(file.filename or "untitled")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    ext = os.path.splitext(safe_filename)[1].lower()

    # Allow custom filename override (preserves extension)
    if filename:
        custom = filename.strip()
        if custom:
            safe_filename = custom + ext
    type_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp",
        ".mp4": "video/mp4", ".mov": "video/mov",
        ".pdf": "document/pdf", ".doc": "document/doc", ".docx": "document/docx",
    }
    # Extension whitelist — reject unsupported file types outright
    if ext not in type_map:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext or '(无扩展名)'}，仅支持：{', '.join(type_map.keys())}",
        )
    file_type = type_map[ext]

    content = await file.read()
    max_size = 200 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File size exceeds 200MB limit")

    asset_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.UPLOAD_DIR, "assets", asset_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, safe_filename)
    with open(file_path, "wb") as f:
        f.write(content)

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

    async def _ai_tagging():
        async with AsyncSessionLocal() as bg_db:
            try:
                await asyncio.wait_for(_generate_ai_tags(asset_id, bg_db), timeout=120)
            except asyncio.TimeoutError:
                logger.error("AI tagging timed out: %s", asset_id)
            except Exception:
                logger.exception("AI tagging failed: %s", asset_id)

    asyncio.create_task(_ai_tagging())

    return _asset_to_response(asset)


# ── List ────────────────────────────────────────────────────────────

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
        query = query.where(Asset.tags.contains([tag]) | Asset.ai_tags.contains([tag]))
    if search:
        query = query.where(Asset.filename.ilike(f"%{search}%")
                            | Asset.ai_description.ilike(f"%{search}%"))
    if file_type:
        query = query.where(Asset.file_type.startswith(file_type))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Asset.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return {
        "items": [_asset_to_response(a) for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── Stats ───────────────────────────────────────────────────────────

@router.get("/stats", response_model=AssetStatsResponse)
async def get_asset_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get quick asset statistics for sidebar/dashboard."""
    total_q = select(func.count(Asset.id)).where(Asset.status != "deleted")
    total = (await db.execute(total_q)).scalar() or 0

    tagged_q = select(func.count(Asset.id)).where(
        Asset.status != "deleted",
        (Asset.ai_tags != None) | (Asset.tags != None),
    )
    tagged = (await db.execute(tagged_q)).scalar() or 0

    size_q = select(func.coalesce(func.sum(Asset.file_size), 0)).where(Asset.status != "deleted")
    total_size_bytes = (await db.execute(size_q)).scalar() or 0

    # By type — compute category in Python to avoid SQLite POSITION() compatibility
    type_result = await db.execute(
        select(Asset.file_type, func.count(Asset.id))
        .where(Asset.status != "deleted").group_by(Asset.file_type)
    )
    by_type: dict[str, int] = {}
    for file_type, count in type_result.all():
        category = file_type.split("/")[0] if "/" in file_type else file_type
        by_type[category] = by_type.get(category, 0) + count

    status_q = await db.execute(
        select(Asset.status, func.count(Asset.id))
        .where(Asset.status != "deleted").group_by(Asset.status)
    )
    by_status = {row[0]: row[1] for row in status_q.all()}

    return AssetStatsResponse(
        total=total, tagged=tagged, total_size_bytes=total_size_bytes,
        by_type=by_type, by_status=by_status,
    )


# ── Popular Tags ────────────────────────────────────────────────────

@router.get("/tags/popular", response_model=PopularTagsResponse)
async def get_popular_tags(
    limit: int = Query(20, ge=5, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get most-used AI tags from the asset collection."""
    result = await db.execute(
        select(Asset.ai_tags).where(Asset.status != "deleted", Asset.ai_tags != None)
    )
    tag_counter: dict[str, int] = {}
    for (tags,) in result.all():
        if tags:
            for t in tags:
                t = str(t).strip()
                if t:
                    tag_counter[t] = tag_counter.get(t, 0) + 1

    sorted_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)
    return PopularTagsResponse(tags=[t[0] for t in sorted_tags[:limit]])


# ── Free Stock Photos (public, no auth required) ─────────────────────

@router.get("/free-stock-photos")
async def get_free_stock_photos(
    page: int = Query(1, ge=1, le=10),
    per_page: int = Query(12, ge=4, le=48),
):
    """Get free stock photo URLs from Lorem Picsum (no API key required)."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                "https://picsum.photos/v2/list",
                params={"page": page, "limit": per_page},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Free stock service temporarily unavailable")

            photos = resp.json()
            results = []
            for p in photos:
                pid = p["id"]
                results.append({
                    "id": pid,
                    "author": p.get("author", "Unknown"),
                    "width": p.get("width", 0),
                    "height": p.get("height", 0),
                    "url": p.get("download_url", f"https://picsum.photos/id/{pid}/800/600"),
                    "thumbnail": f"https://picsum.photos/id/{pid}/200/150",
                    "preview": f"https://picsum.photos/id/{pid}/400/300",
                    "download_url": f"https://picsum.photos/id/{pid}/800/600.jpg",
                })

            return {
                "photos": results,
                "source": "Lorem Picsum",
                "source_url": "https://picsum.photos/",
                "license": "Free to use",
                "page": page,
            }
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Cannot connect to free photo service. Please check your network.")


# ── External Stock Photos: Unsplash & Pexels ─────────────────────────

@router.get("/unsplash/search")
async def search_unsplash_photos(
    q: str = Query(..., min_length=1, description="Search keyword (English recommended)"),
    page: int = Query(1, ge=1, le=100),
    per_page: int = Query(12, ge=1, le=30),
):
    """Search free photos on Unsplash (requires UNSPLASH_API_KEY in .env)."""
    if not settings.UNSPLASH_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="请在 .env 配置 UNSPLASH_API_KEY（注册 https://unsplash.com/developers 免费获取）",
        )

    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": q, "page": page, "per_page": per_page},
                headers={"Authorization": f"Client-ID {settings.UNSPLASH_API_KEY}"},
            )
            if resp.status_code != 200:
                logger.warning("Unsplash API error %s: %s", resp.status_code, resp.text[:300])
                raise HTTPException(status_code=502, detail=f"Unsplash 服务暂时不可用 (HTTP {resp.status_code})")

            data = resp.json()
            results = []
            for p in data.get("results", []):
                urls = p.get("urls") or {}
                user = p.get("user") or {}
                results.append({
                    "id": str(p.get("id", "")),
                    "description": p.get("description") or p.get("alt_description") or "",
                    "width": p.get("width", 0),
                    "height": p.get("height", 0),
                    "url": urls.get("regular") or urls.get("raw") or "",
                    "thumbnail": urls.get("thumb") or urls.get("small") or "",
                    "download_url": urls.get("raw") or urls.get("regular") or "",
                    "author": user.get("name") or "Unknown",
                })

            return {
                "photos": results,
                "source": "Unsplash",
                "total": data.get("total", len(results)),
                "page": page,
            }
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Cannot connect to Unsplash. Please check your network.")


@router.get("/pexels/search")
async def search_pexels(
    q: str = Query(..., min_length=1, description="Search keyword (English recommended)"),
    page: int = Query(1, ge=1, le=100),
    per_page: int = Query(12, ge=1, le=80),
    type: str = Query("photos", pattern="^(photos|videos)$", description="photos | videos"),
):
    """Search free photos/videos on Pexels (requires PEXELS_API_KEY in .env)."""
    if not settings.PEXELS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="请在 .env 配置 PEXELS_API_KEY（注册 https://www.pexels.com/api 免费获取）",
        )

    is_videos = type == "videos"
    endpoint = "https://api.pexels.com/videos/search" if is_videos else "https://api.pexels.com/v1/search"

    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                endpoint,
                params={"query": q, "page": page, "per_page": per_page},
                headers={"Authorization": settings.PEXELS_API_KEY},
            )
            if resp.status_code != 200:
                logger.warning("Pexels API error %s: %s", resp.status_code, resp.text[:300])
                raise HTTPException(status_code=502, detail=f"Pexels 服务暂时不可用 (HTTP {resp.status_code})")

            data = resp.json()

            if is_videos:
                videos = []
                for v in data.get("videos", []):
                    files = v.get("video_files") or []

                    def _file_score(f: dict) -> tuple:
                        quality = (f.get("quality") or "").lower()
                        qs = {"uhd": 5, "hd": 4, "sd": 3}
                        return (qs.get(quality, 2), (f.get("width") or 0) * (f.get("height") or 0))

                    best = sorted(files, key=_file_score, reverse=True)[0] if files else {}
                    pictures = v.get("video_pictures") or []
                    user = v.get("user") or {}
                    videos.append({
                        "id": str(v.get("id", "")),
                        "url": v.get("url") or "",
                        "thumbnail": pictures[0].get("picture") if pictures else "",
                        "download_url": best.get("link") or "",
                        "width": best.get("width") or 0,
                        "height": best.get("height") or 0,
                        "duration": v.get("duration") or 0,
                        "author": user.get("name") or "Unknown",
                    })

                return {
                    "videos": videos,
                    "source": "Pexels",
                    "total": data.get("total_results", len(videos)),
                    "page": page,
                }

            photos = []
            for p in data.get("photos", []):
                src = p.get("src") or {}
                photos.append({
                    "id": str(p.get("id", "")),
                    "description": p.get("alt") or "",
                    "width": p.get("width", 0),
                    "height": p.get("height", 0),
                    "url": src.get("large") or src.get("medium") or src.get("original") or "",
                    "thumbnail": src.get("medium") or src.get("small") or src.get("large") or "",
                    "download_url": src.get("original") or src.get("large2x") or src.get("large") or "",
                    "author": p.get("photographer") or "Unknown",
                })

            return {
                "photos": photos,
                "source": "Pexels",
                "total": data.get("total_results", len(photos)),
                "page": page,
            }
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Cannot connect to Pexels. Please check your network.")


# ── Import from URL ─────────────────────────────────────────────────

class ImportFromUrlRequest(BaseModel):
    url: str
    tags: str | None = None


@router.post("/import-from-url")
async def import_asset_from_url(
    body: ImportFromUrlRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import an image from a public URL into the asset library."""
    url = body.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    parsed = url.split("?")[0]
    safe_name = os.path.basename(parsed)
    if not safe_name or "." not in safe_name:
        safe_name = f"imported_{uuid.uuid4().hex[:8]}.jpg"

    ext = os.path.splitext(safe_name)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".gif": "image/gif", ".webp": "image/webp",
                ".mp4": "video/mp4", ".mov": "video/mov"}
    file_type = mime_map.get(ext, "image/jpeg")

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Download failed: HTTP {resp.status_code}")
            content = resp.content
    except httpx.TimeoutException:
        raise HTTPException(status_code=400, detail="Download timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {e}")

    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 200MB limit")

    asset_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.UPLOAD_DIR, "assets", asset_id)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    user_tags = [t.strip() for t in (body.tags or "").split(",") if t.strip()]

    asset = Asset(
        id=asset_id, filename=safe_name, original_name=safe_name,
        file_type=file_type, file_size=len(content), file_path=file_path,
        tags=user_tags or None, ai_tags=None, ai_description=None,
        status="processing", uploaded_by=current_user.id,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    async def _bg_tag():
        async with AsyncSessionLocal() as bg_db:
            try:
                await asyncio.wait_for(_generate_ai_tags(asset_id, bg_db), timeout=120)
            except Exception:
                logger.exception("AI tagging failed: %s", asset_id)

    asyncio.create_task(_bg_tag())
    return _asset_to_response(asset)


# ── Search by Image (以图搜图) ───────────────────────────────────────

@router.post("/search-by-image")
async def search_assets_by_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """以图搜图: generate an AI description of the uploaded image, then search similar assets.

    Vision models (CLIP/BLIP) are not integrated yet, so the description is inferred
    from the image's metadata (filename/type/size) by the LLM — same approach as AI
    tagging. Falls back to filename-keyword search when the LLM is unavailable.
    """
    filename = os.path.basename(file.filename or "search_image")
    ext = os.path.splitext(filename)[1].lower()
    content_type = (file.content_type or "").lower()
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
    if not content_type.startswith("image/") and ext not in image_exts:
        raise HTTPException(status_code=400, detail="请上传图片文件（jpg/png/webp 等）")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="搜索图片不能超过 10MB")

    name_lower = filename.lower()
    description = ""
    keywords: list[str] = []
    fallback = False
    note: str | None = None

    # 1) Generate AI description + search keywords from the image metadata
    try:
        from app.rag.chain import get_llm
        llm = get_llm()
        search_prompt = (
            "You are a DAM (Digital Asset Management) search assistant. "
            "A user uploaded an image for 'search by image'. "
            "The vision model is not available, so you only know the file's metadata. "
            "Based on the filename, infer what the image likely contains.\n\n"
            f"Filename: {filename}\n"
            f"File type: {content_type or ext}\n"
            f"File size: {len(content) / 1024:.1f} KB\n\n"
            "Output ONLY JSON (no markdown):\n"
            '{"description": "a concise description of the image in Chinese", '
            '"keywords": ["k1", "k2", "k3"]}\n\n'
            "Requirements:\n"
            "- description: one sentence in Chinese describing the likely content\n"
            "- keywords: 4-8 search keywords covering subject, scene, style, color tone "
            "(mix of Chinese and English, lowercase)\n"
        )
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=search_prompt)])
        resp_content = response.content if hasattr(response, 'content') else str(response)

        resp_content = resp_content.strip()
        if resp_content.startswith("```"):
            resp_content = resp_content.split("\n", 1)[1].rsplit("\n", 1)[0]
        if resp_content.startswith("```json"):
            resp_content = resp_content[7:]
        parsed = json.loads(resp_content)
        description = str(parsed.get("description", "")).strip()
        keywords = [str(k).strip() for k in parsed.get("keywords", []) if str(k).strip()]
    except Exception as e:
        logger.warning("LLM unavailable for image search, using filename fallback: %s", e)
        fallback = True
        note = "AI 未连接，已按文件名关键词进行搜索"

    if not keywords:
        fallback = True
        keywords = _keywords_from_filename(name_lower)
        if not note:
            note = "AI 未能生成关键词，已按文件名关键词进行搜索"
    if not description:
        description = f"图片: {filename}"

    keywords = keywords[:8]

    # 2) Search existing assets by the keywords (ranked by hit count)
    items = await _search_assets_by_keywords(keywords, db, limit=24)

    return {
        "description": description,
        "keywords": keywords,
        "fallback": fallback,
        "note": note,
        "items": items,
        "total": len(items),
    }


# ═══════════════════════════════════════════════════════════════════════
# Wildcard-path routes (/{asset_id} — MUST be defined AFTER static paths)
# ═══════════════════════════════════════════════════════════════════════

# ── File Serve (/{asset_id}/file — before /{asset_id}) ──────────────

@router.get("/{asset_id}/file")
async def get_asset_file(
    asset_id: str,
    request: Request,
    token: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Serve the actual file content for an asset (preview/download).

    Authentication via Authorization header (for API clients) OR
    ?token= query param (for <img> tags / <a> downloads in browser).
    """
    # Resolve user: try Authorization header first, then ?token= query param
    user: User | None = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw_token = auth_header[7:]
        user = await _get_user_from_token(raw_token, db)
    if user is None and token:
        user = await _get_user_from_token(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="请提供认证Token(可通过?token=参数传递)")

    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    file_path = asset.file_path
    if not file_path or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found or deleted")

    return FileResponse(path=file_path, media_type=asset.file_type or "application/octet-stream",
                        filename=asset.original_name)


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
        raise HTTPException(status_code=404, detail="Asset not found")
    return _asset_to_response(asset)


# ── Public Search (for cross-project use by ②灵笔/③视界) ──────────

@router.get("/public/search")
async def public_search_assets(
    q: str = Query("", description="Search keyword"),
    file_type: str = Query("all", description="image/video/document/all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Public asset search — no auth required, for ②灵笔 and ③视界."""
    query = select(Asset).where(Asset.status == "ready")

    if q:
        search = f"%{q}%"
        query = query.where(
            (Asset.original_name.ilike(search)) |
            (Asset.filename.ilike(search)) |
            (Asset.ai_description.ilike(search)) |
            (cast(Asset.ai_tags, String).ilike(search)) |
            (cast(Asset.tags, String).ilike(search))
        )

    if file_type != "all":
        query = query.where(Asset.file_type.ilike(f"{file_type}/%"))

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Asset.created_at.desc()).offset(offset).limit(page_size))
    assets = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_asset_to_response(a) for a in assets],
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
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.status = "deleted"
    await db.flush()
    return {"message": "Asset deleted"}


# ── Update ──────────────────────────────────────────────────────────

@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    body: AssetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update asset metadata (tags, name, status, AI description)."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if body.original_name is not None:
        asset.original_name = body.original_name
    if body.tags is not None:
        asset.tags = body.tags
    if body.ai_description is not None:
        asset.ai_description = body.ai_description
    if body.status is not None:
        asset.status = body.status

    await db.flush()
    await db.refresh(asset)
    return _asset_to_response(asset)


# ═══════════════════════════════════════════════════════════════════════
# Data Helpers
# ═══════════════════════════════════════════════════════════════════════

async def _generate_ai_tags(asset_id: str, db: AsyncSession) -> None:
    """Background task: generate AI tags for an asset using LLM."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        return

    try:
        name_lower = asset.original_name.lower()
        ext = os.path.splitext(asset.original_name)[1].lower()
        type_label = "image" if asset.file_type.startswith("image") else ("video" if asset.file_type.startswith("video") else "document")

        try:
            from app.rag.chain import get_llm
            llm = get_llm()
            tagging_prompt = (
                f"You are a professional DAM tagging expert. Generate precise tags for this asset.\n\n"
                f"Filename: {asset.original_name}\n"
                f"File type: {asset.file_type} ({type_label})\n"
                f"File size: {asset.file_size / 1024:.1f} KB\n\n"
                f"Output ONLY JSON (no markdown):\n"
                f'{{"tags": ["tag1", "tag2", "tag3", "tag4", "tag5"], "description": "A concise description"}}\n\n'
                f"Requirements:\n"
                f"- 3-5 specific tags\n"
                f"- Include: subject, scene, style, color tone\n"
            )
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=tagging_prompt)])
            resp_content = response.content if hasattr(response, 'content') else str(response)

            resp_content = resp_content.strip()
            if resp_content.startswith("```"):
                resp_content = resp_content.split("\n", 1)[1].rsplit("\n", 1)[0]
            if resp_content.startswith("```json"):
                resp_content = resp_content[7:]
            parsed = json.loads(resp_content)
            ai_tags = parsed.get("tags", [])[:8]
            ai_desc = parsed.get("description", f"Asset: {asset.original_name}")
        except Exception as e:
            logger.warning("LLM tagging failed, using keyword fallback: %s", e)
            ai_tags = _mock_tag_from_name(name_lower)
            ai_desc = f"Asset: {asset.original_name}"

        asset.ai_tags = ai_tags or _mock_tag_from_name(name_lower)
        asset.ai_description = ai_desc or f"Asset: {asset.original_name}"
        asset.status = "ready"
        await db.flush()
        await db.commit()

        # Cross-project: push AI tags to 数据中枢(⑥) as annotation reference (best-effort)
        try:
            from app.services.datahub_client import push_asset_tags_to_datahub
            await push_asset_tags_to_datahub(
                filename=asset.original_name,
                ai_description=asset.ai_description or "",
                ai_tags=asset.ai_tags or [],
            )
        except Exception:
            logger.debug("DataHub tag push failed (best-effort): %s", asset_id)
    except Exception as e:
        logger.exception("AI tagging completely failed: %s", asset_id)
        asset.status = "ready"
        asset.ai_tags = _mock_tag_from_name(asset.original_name.lower())
        asset.ai_description = f"Asset: {asset.original_name}"
        await db.flush()
        await db.commit()


def _mock_tag_from_name(name: str) -> list[str]:
    """Simple mock tag generator from filename."""
    tags = []
    if any(w in name for w in ["sunset", "beach", "silhouette"]): tags.append("sunset")
    if any(w in name for w in ["city", "skyline"]): tags.append("city")
    if any(w in name for w in ["ocean", "wave", "sea"]): tags.append("ocean")
    if any(w in name for w in ["car", "sports"]): tags.append("automotive")
    if any(w in name for w in ["food", "fruit", "platter"]): tags.append("food")
    if any(w in name for w in ["portrait", "business"]): tags.append("portrait")
    if any(w in name for w in ["building", "architecture"]): tags.append("architecture")
    if any(w in name for w in ["nature", "landscape", "mountain", "forest"]): tags.append("nature")
    if any(w in name for w in ["product", "tech", "showcase"]): tags.append("product")
    if any(w in name for w in ["cat", "pet", "animal"]): tags.append("animal")
    if any(w in name for w in ["winter", "snow", "aurora"]): tags.append("winter")
    if any(w in name for w in ["spring", "cherry", "flower"]): tags.append("spring")
    if any(w in name for w in ["autumn", "fall"]): tags.append("autumn")
    if any(w in name for w in ["summer", "sunflower"]): tags.append("summer")
    if any(w in name for w in ["coffee", "interior", "shop"]): tags.append("interior")
    if any(w in name for w in ["yoga", "meditation"]): tags.append("wellness")
    if any(w in name for w in ["pottery", "handmade", "art"]): tags.append("art")
    if any(w in name for w in ["logo", "brand", "design"]): tags.append("design")
    if any(w in name for w in ["rainy", "night", "neon"]): tags.append("night")
    if not tags:
        tags = ["uncategorized"]
    return tags


def _keywords_from_filename(name_lower: str) -> list[str]:
    """Extract search keywords from a filename (LLM fallback for image search)."""
    stem = os.path.splitext(name_lower)[0]
    # Chinese filenames often glue words with 的/与/和 — split them into usable keywords
    stem = re.sub(r"[的与和及]", " ", stem)
    parts = re.split(r"[^a-z0-9一-鿿]+", stem)
    stopwords = {
        "img", "image", "photo", "pic", "picture", "dsc", "screenshot",
        "wechat", "mmexport", "untitled", "tmp", "final", "copy",
        "v1", "v2", "v3", "new",
    }
    keywords = [p for p in parts if len(p) >= 2 and p not in stopwords]
    return keywords[:8]


async def _search_assets_by_keywords(
    keywords: list[str], db: AsyncSession, limit: int = 24
) -> list[dict]:
    """Search assets matching any keyword, ranked by total keyword hits."""
    if not keywords:
        return []

    conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append(Asset.filename.ilike(pattern))
        conditions.append(Asset.ai_description.ilike(pattern))
        conditions.append(cast(Asset.ai_tags, String).ilike(pattern))
        conditions.append(cast(Asset.tags, String).ilike(pattern))

    result = await db.execute(
        select(Asset)
        .where(Asset.status != "deleted", or_(*conditions))
        .limit(200)
    )
    assets = result.scalars().all()

    def _score(a: Asset) -> int:
        haystacks = {
            "ai_tags": " ".join(a.ai_tags or []).lower(),
            "tags": " ".join(a.tags or []).lower(),
            "filename": (a.filename or "").lower(),
            "desc": (a.ai_description or "").lower(),
        }
        score = 0
        for kw in keywords:
            kwl = kw.lower()
            if kwl in haystacks["ai_tags"]:
                score += 3
            if kwl in haystacks["tags"]:
                score += 2
            if kwl in haystacks["filename"]:
                score += 2
            if kwl in haystacks["desc"]:
                score += 1
        return score

    ranked = sorted(
        assets,
        key=lambda a: (_score(a), a.created_at.timestamp() if a.created_at else 0),
        reverse=True,
    )
    return [_asset_to_response(a) for a in ranked[:limit]]


def _asset_to_response(a: Asset) -> dict:
    """Convert an Asset ORM object to a response dict."""
    return {
        "id": a.id,
        "filename": a.original_name,
        "original_name": a.original_name,
        "file_type": a.file_type,
        "file_size": a.file_size,
        "tags": a.tags or [],
        "ai_tags": a.ai_tags or [],
        "ai_description": a.ai_description,
        "thumbnail_url": f"/api/assets/{a.id}/file" if a.file_type.startswith("image") else None,
        "width": a.width,
        "height": a.height,
        "duration_seconds": a.duration_seconds,
        "status": a.status,
        "version": a.version,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }
