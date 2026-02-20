"""认证路由 - 微信登录"""

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.common import success_response
from app.utils.exceptions import AppException
from app.utils.security import create_token

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    """微信登录请求"""
    code: str


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    openid: str
    is_new_user: bool
    role: str
    doctor_id: int | None = None


@router.post("/login", summary="微信登录")
async def wechat_login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    微信小程序登录

    流程:
    1. 前端调用 wx.login() 获取 code
    2. 前端将 code 发送到本接口
    3. 后端用 code + appid + secret 调微信 code2session 接口换取 openid
    4. 根据 openid 查找或创建用户
    5. 生成 JWT token 返回给前端

    开发模式: 如果 WX_APPID 未配置，则将 code 直接当作 openid 使用 (便于测试)
    """
    openid = await _get_openid(data.code)

    # 查找用户
    result = await db.execute(
        select(User).where(User.openid == openid)
    )
    user = result.scalar_one_or_none()
    is_new_user = user is None

    if is_new_user:
        # 自动注册
        user = User(openid=openid)
        db.add(user)
        await db.flush()
        await db.refresh(user)

    # 生成 JWT
    token = create_token(openid)

    return success_response(
        data=LoginResponse(
            token=token,
            openid=openid,
            is_new_user=is_new_user,
            role=user.role or "patient",
            doctor_id=user.doctor_id,
        ).model_dump(),
        message="登录成功",
    )


async def _get_openid(code: str) -> str:
    """
    通过微信 code2session 接口获取 openid

    开发模式 (WX_APPID 为空): 直接将 code 当 openid 使用
    生产模式: 调用微信接口
    """
    if not settings.WX_APPID or not settings.WX_SECRET:
        # 开发模式: code 直接作为 openid
        return code

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WX_APPID,
        "secret": settings.WX_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if "openid" not in data:
        errcode = data.get("errcode", -1)
        errmsg = data.get("errmsg", "微信登录失败")
        raise AppException(code=40101, message=f"微信登录失败: {errmsg}", status_code=401)

    return data["openid"]
