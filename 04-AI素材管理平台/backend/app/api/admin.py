"""Admin API routes (admin only)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func, case, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from app.models.asset import Asset

from app.core.auth import admin_required
from app.schemas.auth import UserResponse

router = APIRouter()


class UpdateUserRequest(BaseModel):
    """Request body for updating a user."""
    is_active: bool | None = Field(None, description="启用/禁用用户")
    role: str | None = Field(None, pattern="^(admin|user)$", description="用户角色")


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Update user status or role (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user_id == str(current_user.id):
        raise HTTPException(status_code=400, detail="不能修改自己的状态")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role is not None:
        user.role = body.role
    await db.flush()
    return {"message": "用户已更新"}


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Get system dashboard statistics (users, sessions, messages, assets)."""
    user_result = await db.execute(
        select(
            func.count(User.id).label("total_users"),
            func.sum(case((User.is_active == True, 1), else_=0)).label("active_users"),
        )
    )
    user_stats = user_result.one()

    msg_result = await db.execute(
        select(
            func.count(Message.id).label("total_messages"),
            func.sum(case((Message.feedback == "positive", 1), else_=0)).label("positive"),
            func.sum(case((Message.feedback == "negative", 1), else_=0)).label("negative"),
        )
    )
    msg_stats = msg_result.one()

    session_result = await db.execute(select(func.count(Session.id)))
    total_sessions = session_result.scalar()

    # ── Asset stats ──
    asset_total_q = select(func.count(Asset.id)).where(Asset.status != "deleted")
    asset_total = (await db.execute(asset_total_q)).scalar() or 0

    asset_tagged_q = select(func.count(Asset.id)).where(
        Asset.status != "deleted",
        (Asset.ai_tags != None) | (Asset.tags != None),
    )
    asset_tagged = (await db.execute(asset_tagged_q)).scalar() or 0

    asset_processing_q = select(func.count(Asset.id)).where(Asset.status == "processing")
    asset_processing = (await db.execute(asset_processing_q)).scalar() or 0

    asset_ready_q = select(func.count(Asset.id)).where(Asset.status == "ready")
    asset_ready = (await db.execute(asset_ready_q)).scalar() or 0

    storage_q = select(func.coalesce(func.sum(Asset.file_size), 0)).where(
        Asset.status != "deleted"
    )
    total_storage_bytes = (await db.execute(storage_q)).scalar() or 0

    # By type — compute category in Python to avoid SQLite POSITION() issues
    type_result = await db.execute(
        select(Asset.file_type, func.count(Asset.id))
        .where(Asset.status != "deleted").group_by(Asset.file_type)
    )
    assets_by_type: dict[str, int] = {}
    for file_type, count in type_result.all():
        category = file_type.split("/")[0] if "/" in file_type else file_type
        assets_by_type[category] = assets_by_type.get(category, 0) + count

    return {
        # User/session/message stats (compatible with original)
        "total_users": user_stats.total_users,
        "active_users": user_stats.active_users,
        "total_sessions": total_sessions,
        "total_messages": msg_stats.total_messages,
        "feedback": {
            "positive": msg_stats.positive or 0,
            "negative": msg_stats.negative or 0,
        },
        # Asset stats (DAM-specific)
        "total_assets": asset_total,
        "tagged_assets": asset_tagged,
        "tagged_percentage": round(asset_tagged / asset_total * 100, 1) if asset_total > 0 else 0,
        "processing_assets": asset_processing,
        "ready_assets": asset_ready,
        "total_storage_bytes": total_storage_bytes,
        "assets_by_type": assets_by_type,
    }
