"""Shared rate limiter instance (separate module to avoid circular imports).

slowapi 的官方推荐模式：Limiter 定义在独立模块，main.py 和路由
都可以安全 import，不会产生循环依赖。
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _safe_remote_address(request) -> str:
    """Return client IP, falling back when request.client is None.

    Test clients (httpx ASGITransport) don't populate request.client,
    which would make get_remote_address raise and break every rate-
    limited route in the test suite.
    """
    try:
        return get_remote_address(request)
    except Exception:
        return "127.0.0.1"


limiter = Limiter(
    key_func=_safe_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)
