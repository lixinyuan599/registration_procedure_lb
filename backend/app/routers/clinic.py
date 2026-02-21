"""门店路由"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import clinic_service
from app.schemas.clinic import ClinicResponse
from app.schemas.common import success_response
from app.utils.deps import get_tenant_id

router = APIRouter(prefix="/clinics", tags=["门店"])


@router.get("", summary="获取门店列表")
async def list_clinics(
    tenant_id: Optional[int] = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """获取所有营业中的门店列表 (按企业过滤)"""
    clinics = await clinic_service.get_all_clinics(db, tenant_id=tenant_id)
    return success_response(
        data=[ClinicResponse.model_validate(c) for c in clinics]
    )


@router.get("/{clinic_id}", summary="获取门店详情")
async def get_clinic(
    clinic_id: int,
    db: AsyncSession = Depends(get_db),
):
    """根据 ID 获取门店详情"""
    clinic = await clinic_service.get_clinic_by_id(db, clinic_id)
    return success_response(data=ClinicResponse.model_validate(clinic))
