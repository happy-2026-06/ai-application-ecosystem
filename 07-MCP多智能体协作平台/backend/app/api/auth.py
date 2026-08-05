"""Authentication API routes."""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ChangePasswordRequest,
    UserResponse,
    RefreshTokenRequest,
)
from app.services import auth_service

router = APIRouter()


class ProfileUpdate(BaseModel):
    """Request body for profile updates."""
    display_name: str | None = None


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    user = await auth_service.register_user(
        db=db,
        username=request.username,
        password=request.password,
        email=request.email,
        display_name=request.display_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login and receive JWT access/refresh tokens."""
    return await auth_service.login_user(
        db=db,
        username=request.username,
        password=request.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh an expired access token."""
    return await auth_service.refresh_access_token(
        db=db,
        refresh_token=request.refresh_token,
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    await auth_service.change_password(
        db=db,
        user=current_user,
        old_password=request.old_password,
        new_password=request.new_password,
    )
    return {"message": "密码修改成功"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's information."""
    return current_user


@router.patch("/profile")
async def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile (display name only)."""
    if body.display_name and body.display_name.strip():
        current_user.display_name = body.display_name.strip()
        await db.flush()
    return {"message": "个人信息已更新", "display_name": current_user.display_name}
