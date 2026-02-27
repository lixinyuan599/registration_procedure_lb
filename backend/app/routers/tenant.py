"""企业/租户路由"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.tenant import Tenant
from app.schemas.common import success_response
from app.utils.deps import get_tenant_id

router = APIRouter(prefix="/tenants", tags=["企业"])


class TenantBranding(BaseModel):
    id: int
    name: str
    subtitle: str | None = None
    description: str | None = None
    logo_url: str | None = None
    contact_phone: str | None = None

    model_config = {"from_attributes": True}


@router.get("/current", summary="获取当前企业品牌信息")
async def get_current_tenant(
    tenant_id: Optional[int] = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    根据 X-Tenant-Id 返回当前企业的品牌信息（名称、标语、Logo 等）。
    小程序首页用此接口动态展示企业品牌。
    """
    if not tenant_id:
        tenant_id = 1

    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if tenant is None:
        return success_response(data={
            "id": tenant_id,
            "name": "门诊挂号",
            "subtitle": None,
            "description": None,
            "logo_url": None,
            "contact_phone": None,
        })

    return success_response(data=TenantBranding.model_validate(tenant))
