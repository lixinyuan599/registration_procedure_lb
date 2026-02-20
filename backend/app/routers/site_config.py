"""系统显示配置路由"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.site_config import SiteConfig
from app.schemas.common import success_response

router = APIRouter(tags=["系统配置"])


@router.get("/config/display", summary="获取显示配置")
async def get_display_config(db: AsyncSession = Depends(get_db)):
    """
    获取小程序显示配置 (公开接口，无需认证)

    返回: { show_remaining_slots: true/false, clinic_name: "..." }
    """
    result = await db.execute(select(SiteConfig).where(SiteConfig.id == 1))
    config = result.scalar_one_or_none()

    if config is None:
        # 首次访问自动创建默认配置
        config = SiteConfig(id=1, show_remaining_slots=True, clinic_name="门诊挂号系统")
        db.add(config)
        await db.flush()
        await db.refresh(config)

    return success_response(data={
        "show_remaining_slots": config.show_remaining_slots,
        "clinic_name": config.clinic_name,
    })
