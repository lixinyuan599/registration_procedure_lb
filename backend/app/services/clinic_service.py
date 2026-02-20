"""门店业务逻辑"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.utils.exceptions import NotFoundException


async def get_all_clinics(db: AsyncSession) -> list[Clinic]:
    """获取所有营业中的门店"""
    result = await db.execute(
        select(Clinic)
        .where(Clinic.is_active == True)
        .order_by(Clinic.id)
    )
    return list(result.scalars().all())


async def get_clinic_by_id(db: AsyncSession, clinic_id: int) -> Clinic:
    """根据 ID 获取门店"""
    result = await db.execute(
        select(Clinic).where(Clinic.id == clinic_id)
    )
    clinic = result.scalar_one_or_none()
    if clinic is None:
        raise NotFoundException(f"门店不存在 (id={clinic_id})")
    return clinic
