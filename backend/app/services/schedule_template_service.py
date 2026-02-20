"""排班模板业务逻辑"""

from datetime import date, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.models.schedule import Schedule
from app.models.schedule_template import ScheduleTemplate
from app.schemas.schedule_template import TemplateSlot
from app.utils.exceptions import NotFoundException


async def get_doctor_templates(
    db: AsyncSession, doctor_id: int, clinic_id: int | None = None,
) -> list[ScheduleTemplate]:
    """
    获取医生的周模板

    如果指定 clinic_id, 只返回该门店的模板;
    否则返回所有门店的模板
    """
    query = (
        select(ScheduleTemplate)
        .where(ScheduleTemplate.doctor_id == doctor_id)
        .order_by(ScheduleTemplate.weekday, ScheduleTemplate.start_time)
    )
    if clinic_id:
        query = query.where(ScheduleTemplate.clinic_id == clinic_id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_doctor_templates(
    db: AsyncSession,
    doctor_id: int,
    slots: list[TemplateSlot],
    clinic_id: int | None = None,
) -> list[ScheduleTemplate]:
    """
    整体更新医生的周模板

    如果指定 clinic_id, 只删除并重建该门店的模板;
    否则使用医生的主门店 clinic_id (兼容旧逻辑)
    """
    # 查询医生
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor_id)
    )
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise NotFoundException(f"医生不存在 (id={doctor_id})")

    # 确定使用的 clinic_id (优先参数, 其次第一个关联门店)
    target_clinic_id = clinic_id or doctor.first_clinic_id
    if not target_clinic_id:
        from app.utils.exceptions import AppException
        raise AppException(code=40001, message="医生未关联任何门店", status_code=400)

    # 删除旧模板 (只删对应门店的)
    del_query = delete(ScheduleTemplate).where(
        ScheduleTemplate.doctor_id == doctor_id,
        ScheduleTemplate.clinic_id == target_clinic_id,
    )
    await db.execute(del_query)

    # 创建新模板
    templates = []
    for slot in slots:
        t = ScheduleTemplate(
            doctor_id=doctor_id,
            clinic_id=target_clinic_id,
            weekday=slot.weekday,
            start_time=slot.start_time,
            end_time=slot.end_time,
            max_patients=slot.max_patients,
            is_active=slot.is_active,
        )
        db.add(t)
        templates.append(t)

    await db.flush()
    for t in templates:
        await db.refresh(t)
    return templates


async def generate_schedules_from_templates(
    db: AsyncSession,
    weeks: int = 1,
    doctor_id: int | None = None,
) -> dict:
    """
    根据模板生成未来 N 周的具体排班

    逻辑:
    1. 有模板 -> 按模板生成 (每个模板自带 clinic_id)
    2. 无模板 -> 查找上周实际排班作为参考
    3. 上周也没有 -> 跳过该医生

    返回: { "created": int, "skipped": int }
    """
    # 查询所有医生的模板
    query = select(ScheduleTemplate).where(ScheduleTemplate.is_active == True)
    if doctor_id:
        query = query.where(ScheduleTemplate.doctor_id == doctor_id)
    result = await db.execute(query)
    templates = list(result.scalars().all())

    # 按医生分组
    doctor_templates: dict[int, list[ScheduleTemplate]] = {}
    for t in templates:
        doctor_templates.setdefault(t.doctor_id, []).append(t)

    # 如果指定了医生但没有模板，尝试从上周排班推导
    if doctor_id and doctor_id not in doctor_templates:
        inferred = await _infer_from_last_week(db, doctor_id)
        if inferred:
            doctor_templates[doctor_id] = inferred

    # 如果没有指定医生，也要为没有模板的活跃医生尝试推导
    if not doctor_id:
        active_doctors = await db.execute(
            select(Doctor).where(Doctor.is_active == True)
        )
        for doc in active_doctors.scalars().all():
            if doc.id not in doctor_templates:
                inferred = await _infer_from_last_week(db, doc.id)
                if inferred:
                    doctor_templates[doc.id] = inferred

    today = date.today()
    total_days = weeks * 7
    created = 0
    skipped = 0

    for doc_id, tmpl_list in doctor_templates.items():
        for day_offset in range(1, total_days + 1):
            current_date = today + timedelta(days=day_offset)
            weekday = current_date.weekday()  # 0=周一

            # 找到该星期几的模板
            day_slots = [t for t in tmpl_list if t.weekday == weekday]
            for slot in day_slots:
                # 检查是否已存在
                exists = await db.execute(
                    select(Schedule).where(
                        Schedule.doctor_id == doc_id,
                        Schedule.date == current_date,
                        Schedule.start_time == slot.start_time,
                    )
                )
                if exists.scalar_one_or_none():
                    skipped += 1
                    continue

                schedule = Schedule(
                    doctor_id=doc_id,
                    clinic_id=slot.clinic_id,
                    date=current_date,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    max_patients=slot.max_patients,
                    current_patients=0,
                    status="open",
                )
                db.add(schedule)
                created += 1

    await db.flush()
    return {"created": created, "skipped": skipped}


async def _infer_from_last_week(
    db: AsyncSession, doctor_id: int
) -> list[ScheduleTemplate] | None:
    """
    从上周的实际排班推导出模板

    返回伪 ScheduleTemplate 对象列表 (用于生成逻辑复用)
    """
    today = date.today()
    last_week_start = today - timedelta(days=today.weekday() + 7)
    last_week_end = last_week_start + timedelta(days=6)

    result = await db.execute(
        select(Schedule).where(
            Schedule.doctor_id == doctor_id,
            Schedule.date >= last_week_start,
            Schedule.date <= last_week_end,
        )
    )
    last_schedules = list(result.scalars().all())

    if not last_schedules:
        return None

    # 转换为模板格式
    templates = []
    for s in last_schedules:
        t = ScheduleTemplate(
            doctor_id=s.doctor_id,
            clinic_id=s.clinic_id,
            weekday=s.date.weekday(),
            start_time=s.start_time,
            end_time=s.end_time,
            max_patients=s.max_patients,
            is_active=True,
        )
        templates.append(t)

    return templates
