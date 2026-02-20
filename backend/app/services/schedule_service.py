"""排班业务逻辑"""

from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.utils.exceptions import NotFoundException


async def get_schedules_by_doctor(
    db: AsyncSession,
    doctor_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    clinic_id: int | None = None,
) -> list[Schedule]:
    """
    获取医生排班列表

    - 默认查询从今天起 7 天内的排班
    - 仅返回开放状态 (open) 的排班
    - 支持 clinic_id 过滤特定门店
    """
    if date_from is None:
        date_from = date.today()
    if date_to is None:
        date_to = date_from + timedelta(days=7)

    query = (
        select(Schedule)
        .where(
            Schedule.doctor_id == doctor_id,
            Schedule.date >= date_from,
            Schedule.date <= date_to,
            Schedule.status.in_(["open", "full"]),
        )
        .order_by(Schedule.date, Schedule.start_time)
    )
    if clinic_id:
        query = query.where(Schedule.clinic_id == clinic_id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_schedule_by_id(db: AsyncSession, schedule_id: int) -> Schedule:
    """根据 ID 获取排班"""
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise NotFoundException(f"排班不存在 (id={schedule_id})")
    return schedule
