"""Authentication service: register, login, password management, admin seeding."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.config import settings


async def register_user(
    db: AsyncSession,
    username: str,
    password: str,
    email: str | None = None,
    phone: str | None = None,
    display_name: str | None = None,
) -> User:
    """Register a new user."""
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )

    user = User(
        username=username,
        email=email,
        phone=phone,
        display_name=display_name if display_name is not None else username,
        hashed_password=get_password_hash(password),
        role="user",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def login_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> dict:
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"X-Error-Code": "USER_NOT_FOUND"},
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"X-Error-Code": "WRONG_PASSWORD"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
            headers={"X-Error-Code": "ACCOUNT_DISABLED"},
        )

    # Create tokens
    token_data = {"sub": str(user.id), "username": user.username, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "is_active": user.is_active,
        },
    }


async def change_password(
    db: AsyncSession,
    user: User,
    old_password: str,
    new_password: str,
) -> None:
    """Change user's password."""
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码不正确",
        )

    user.hashed_password = get_password_hash(new_password)
    await db.flush()


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> dict:
    """Refresh an access token using a refresh token."""
    from app.core.security import decode_token

    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )

    token_data = {"sub": str(user.id), "username": user.username, "role": user.role}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


async def seed_admin_user(db: AsyncSession) -> None:
    """Ensure an admin user exists with the configured credentials.

    Creates the admin user if absent. Does NOT reset the password on restart
    — once created, the admin password persists from the database.
    To reset the admin password, use a CLI script or change it via the web UI.
    """
    import logging
    logger = logging.getLogger(__name__)

    result = await db.execute(
        select(User).where(User.username == settings.ADMIN_USERNAME)
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            display_name="系统管理员",
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.flush()
        logger.info("Admin user '%s' created", settings.ADMIN_USERNAME)
    else:
        # Restore admin role if it drifted
        if admin.role != "admin":
            admin.role = "admin"
            await db.flush()
            logger.info("Admin user '%s' role corrected to admin", settings.ADMIN_USERNAME)
        # Sync password on every restart so changing .env + restart works
        if not verify_password(settings.ADMIN_PASSWORD, admin.hashed_password):
            admin.hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            await db.flush()
            logger.info("Admin user '%s' password synced to current config", settings.ADMIN_USERNAME)
