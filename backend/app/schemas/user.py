"""用户 Schema"""

from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    """用户基础字段"""
    nickname: str | None = None
    phone: str | None = None
    avatar_url: str | None = None


class UserCreate(BaseModel):
    """创建/注册用户 (微信登录)"""
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    """用户响应"""
    id: int
    openid: str
    created_at: datetime

    model_config = {"from_attributes": True}
