"""医生路由"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.models.doctor_clinic import doctor_clinics
from app.models.clinic import Clinic
from app.services import doctor_service
from app.schemas.doctor import DoctorResponse, ClinicBrief
from app.schemas.common import success_response
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/clinics", tags=["医生"])


@router.get("/{clinic_id}/doctors", summary="获取门店医生列表")
async def list_doctors_by_clinic(
    clinic_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取指定门店的医生列表 (通过多对多关联表查询)"""
    doctors = await doctor_service.get_doctors_by_clinic(db, clinic_id)
    return success_response(
        data=[DoctorResponse.model_validate(d) for d in doctors]
    )


# 独立路由 (不依赖 /clinics 前缀)
doctor_router = APIRouter(prefix="/doctors", tags=["医生"])


@doctor_router.get("", summary="获取全部在职医生列表")
async def list_all_doctors(
    search: str | None = Query(None, description="搜索姓名/擅长领域"),
    db: AsyncSession = Depends(get_db),
):
    """获取全部在职医生列表，支持模糊搜索"""
    doctors = await doctor_service.get_all_doctors(db, search)
    return success_response(
        data=[DoctorResponse.model_validate(d) for d in doctors]
    )


@doctor_router.get("/{doctor_id}/clinics", summary="获取医生的关联门店列表")
async def get_doctor_clinics(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取医生关联的所有出诊门店 (多对多)"""
    doc_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = doc_result.scalar_one_or_none()
    if not doctor:
        raise NotFoundException(f"医生不存在 (id={doctor_id})")

    # 通过多对多关联表查询
    result = await db.execute(
        select(Clinic)
        .join(doctor_clinics, Clinic.id == doctor_clinics.c.clinic_id)
        .where(doctor_clinics.c.doctor_id == doctor_id, Clinic.is_active == True)
        .order_by(Clinic.id)
    )
    clinics_list = list(result.scalars().unique().all())

    return success_response(
        data=[ClinicBrief.model_validate(c) for c in clinics_list]
    )
