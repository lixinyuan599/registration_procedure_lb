"""依赖注入 - 公共依赖"""

from typing import Optional
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.utils.exceptions import UnauthorizedException
from app.utils.security import decode_token


async def get_tenant_id(
    x_tenant_id: Optional[str] = Header(None, description="企业 ID (多租户)"),
) -> Optional[int]:
    """从请求头 X-Tenant-Id 中获取企业 ID"""
    if x_tenant_id:
        try:
            return int(x_tenant_id)
        except (ValueError, TypeError):
            return None
    return None


async def get_current_user(
    authorization: str = Header(None, description="Bearer JWT Token"),
    x_user_openid: str = Header(None, description="(开发调试) 微信用户 openid"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前用户 (依赖注入)

    认证优先级:
    1. Authorization: Bearer <jwt_token>  (生产模式)
    2. X-User-OpenID: <openid>           (开发调试兼容)

    两者都没有则返回 401
    """
    openid = None

    # 优先解析 JWT Token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        openid = decode_token(token)
        if openid is None:
            raise UnauthorizedException("Token 无效或已过期")

    # 降级: 开发模式用 X-User-OpenID
    if openid is None and x_user_openid:
        openid = x_user_openid

    if not openid:
        raise UnauthorizedException()

    result = await db.execute(
        select(User).where(User.openid == openid)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # 首次使用自动注册 (静默注册)
        user = User(openid=openid)
        db.add(user)
        await db.flush()
        await db.refresh(user)

    return user
