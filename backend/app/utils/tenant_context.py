"""租户上下文 - 用 contextvars 让 sqladmin 的视图方法能获取当前登录管理员信息"""

from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


current_tenant_id: ContextVar[Optional[int]] = ContextVar("current_tenant_id", default=None)
current_admin_role: ContextVar[Optional[str]] = ContextVar("current_admin_role", default=None)
current_admin_id: ContextVar[Optional[int]] = ContextVar("current_admin_id", default=None)


class TenantMiddleware(BaseHTTPMiddleware):
    """从 session 中提取当前管理员的 tenant 信息，写入 contextvars"""

    async def dispatch(self, request: Request, call_next):
        session = request.scope.get("session", {})
        tenant_id = session.get("tenant_id")
        admin_role = session.get("admin_role")
        admin_id = session.get("admin_id")

        t1 = current_tenant_id.set(tenant_id)
        t2 = current_admin_role.set(admin_role)
        t3 = current_admin_id.set(admin_id)
        try:
            response = await call_next(request)
            return response
        finally:
            current_tenant_id.reset(t1)
            current_admin_role.reset(t2)
            current_admin_id.reset(t3)


def is_super_admin() -> bool:
    return current_admin_role.get() == "super_admin"


def get_tenant_filter_id() -> Optional[int]:
    """获取当前管理员的 tenant_id，超级管理员返回 None（不过滤）"""
    if is_super_admin():
        return None
    return current_tenant_id.get()
