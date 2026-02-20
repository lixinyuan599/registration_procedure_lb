"""预约业务逻辑"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.schedule import Schedule
from app.schemas.appointment import AppointmentCreate
from app.utils.exceptions import (
    NotFoundException,
    ScheduleFullException,
    ScheduleClosedException,
    DuplicateAppointmentException,
)


async def create_appointment(
    db: AsyncSession,
    user_id: int,
    data: AppointmentCreate,
) -> Appointment:
    """
    创建预约挂号

    业务规则：
    1. 排班必须存在且状态为 open
    2. 排班未满 (current_patients < max_patients)
    3. 用户不能重复预约同一排班
    4. 创建预约后更新排班的 current_patients
    5. 若排班满员则自动更新状态为 full
    """
    # 1. 查询排班 (使用 with_for_update 加行锁，防止并发超卖)
    result = await db.execute(
        select(Schedule)
        .where(Schedule.id == data.schedule_id)
        .with_for_update()
    )
    schedule = result.scalar_one_or_none()

    if schedule is None:
        raise NotFoundException("排班不存在")

    # 2. 检查排班状态
    if schedule.status == "closed":
        raise ScheduleClosedException()
    if schedule.status == "full" or schedule.current_patients >= schedule.max_patients:
        raise ScheduleFullException()

    # 3. 检查重复预约
    existing = await db.execute(
        select(Appointment).where(
            Appointment.user_id == user_id,
            Appointment.schedule_id == data.schedule_id,
            Appointment.status != "cancelled",
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise DuplicateAppointmentException()

    # 4. 创建预约
    time_slot = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
    appointment = Appointment(
        user_id=user_id,
        doctor_id=data.doctor_id,
        clinic_id=data.clinic_id,
        schedule_id=data.schedule_id,
        appointment_date=schedule.date,
        time_slot=time_slot,
        status="confirmed",
        notes=data.notes,
    )
    db.add(appointment)

    # 5. 更新排班已预约人数
    schedule.current_patients += 1
    if schedule.current_patients >= schedule.max_patients:
        schedule.status = "full"

    await db.flush()
    await db.refresh(appointment)
    return appointment


async def get_user_appointments(
    db: AsyncSession,
    user_id: int,
) -> list[Appointment]:
    """
    获取用户的全部预约记录

    按创建时间倒序，关联加载医生和门店信息
    """
    result = await db.execute(
        select(Appointment)
        .where(Appointment.user_id == user_id)
        .options(
            selectinload(Appointment.doctor),
            selectinload(Appointment.clinic),
        )
        .order_by(Appointment.created_at.desc())
    )
    return list(result.scalars().all())


async def cancel_appointment(
    db: AsyncSession,
    user_id: int,
    appointment_id: int,
) -> Appointment:
    """
    取消预约

    业务规则：
    1. 预约必须属于当前用户
    2. 只有 confirmed 状态的预约可以取消
    3. 取消后归还排班名额
    """
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.user_id == user_id,
        )
    )
    appointment = result.scalar_one_or_none()

    if appointment is None:
        raise NotFoundException("预约不存在")

    if appointment.status != "confirmed":
        raise NotFoundException("该预约无法取消")

    # 更新预约状态
    appointment.status = "cancelled"

    # 归还排班名额
    schedule_result = await db.execute(
        select(Schedule)
        .where(Schedule.id == appointment.schedule_id)
        .with_for_update()
    )
    schedule = schedule_result.scalar_one_or_none()
    if schedule:
        schedule.current_patients = max(0, schedule.current_patients - 1)
        if schedule.status == "full":
            schedule.status = "open"

    await db.flush()
    await db.refresh(appointment)
    return appointment
