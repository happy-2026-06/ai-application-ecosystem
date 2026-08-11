"""Pydantic schemas for authentication."""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: str | None = Field(None, max_length=100, description="邮箱（可选）")
    display_name: str | None = Field(None, max_length=100, description="显示名称（可选）")


class LoginRequest(BaseModel):
    """Login request."""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: dict | None = None  # {id, username, email, display_name, role, is_active}


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class UserResponse(BaseModel):
    """Public user information."""
    id: str
    username: str
    email: str | None = None
    display_name: str | None = None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="刷新令牌")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    username: str = Field(..., description="用户名")


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    username: str = Field(..., description="用户名")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")
