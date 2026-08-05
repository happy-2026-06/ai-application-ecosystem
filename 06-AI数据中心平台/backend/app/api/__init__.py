"""API v1 router aggregation."""
from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router
from app.api.system import router as system_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(chat_router, prefix="/chat", tags=["对话"])
api_router.include_router(admin_router, prefix="/admin", tags=["管理"])
api_router.include_router(system_router, prefix="/system", tags=["系统"])
