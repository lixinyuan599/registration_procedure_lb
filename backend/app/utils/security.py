"""JWT 令牌工具"""

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.config import get_settings

settings = get_settings()


def create_token(openid: str) -> str:
    """
    生成 JWT Token

    payload: { "sub": openid, "exp": 过期时间 }
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": openid,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> str | None:
    """
    解析 JWT Token，返回 openid

    失败返回 None
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None
