"""医生业务逻辑"""

from typing import Optional
from sqlalchemy import select, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.models.doctor_clinic import doctor_clinics
from app.utils.exceptions import NotFoundException


async def get_all_doctors(
    db: AsyncSession,
    search: str | None = None,
    tenant_id: Optional[int] = None,
) -> list[Doctor]:
    """获取所有在职医生列表 (可按企业过滤, 支持搜索)"""
    query = select(Doctor).where(Doctor.is_active == True).order_by(Doctor.id)
    if tenant_id is not None:
        query = query.where(Doctor.tenant_id == tenant_id)
    if search and search.strip():
        keyword = f"%{search.strip()}%"
        query = query.where(
            or_(
                cast(Doctor.name, String).ilike(keyword),
                cast(Doctor.expertise, String).ilike(keyword),
            )
        )
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def get_doctors_by_clinic(
    db: AsyncSession, clinic_id: int
) -> list[Doctor]:
    """获取指定门店的在职医生列表 (多对多)"""
    result = await db.execute(
        select(Doctor)
        .join(doctor_clinics, Doctor.id == doctor_clinics.c.doctor_id)
        .where(doctor_clinics.c.clinic_id == clinic_id, Doctor.is_active == True)
        .order_by(Doctor.id)
    )
    return list(result.scalars().unique().all())


async def get_doctor_by_id(db: AsyncSession, doctor_id: int) -> Doctor:
    """根据 ID 获取医生"""
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor_id)
    )
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise NotFoundException(f"医生不存在 (id={doctor_id})")
    return doctor
