"""排班模板路由 + 周排班编辑"""

from datetime import date, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.models.schedule import Schedule
from app.models.user import User
from app.services import schedule_template_service
from app.schemas.schedule_template import (
    ScheduleTemplateResponse,
    WeekTemplateUpdate,
)
from app.schemas.common import success_response
from app.utils.deps import get_current_user
from app.utils.exceptions import AppException, NotFoundException

router = APIRouter(tags=["排班模板"])


@router.get("/doctors/{doctor_id}/schedule-template", summary="获取医生周模板")
async def get_doctor_template(
    doctor_id: int,
    clinic_id: int | None = Query(None, description="门店 ID, 不传则返回所有门店模板"),
    db: AsyncSession = Depends(get_db),
):
    """获取指定医生的排班周模板, 可按门店过滤"""
    templates = await schedule_template_service.get_doctor_templates(
        db, doctor_id, clinic_id=clinic_id
    )
    return success_response(
        data=[ScheduleTemplateResponse.model_validate(t) for t in templates]
    )


@router.put("/doctors/{doctor_id}/schedule-template", summary="更新医生周模板")
async def update_doctor_template(
    doctor_id: int,
    data: WeekTemplateUpdate,
    clinic_id: int | None = Query(None, description="目标门店 ID, 不传则使用主门店"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新医生的排班周模板

    权限: 医生本人 或 管理员
    前端提交完整的一周模板，后端会替换对应门店的旧模板
    """
    # 权限检查
    if current_user.role == "doctor":
        if current_user.doctor_id != doctor_id:
            raise AppException(code=40301, message="只能修改自己的排班模板", status_code=403)
    elif current_user.role != "admin":
        raise AppException(code=40301, message="无权操作", status_code=403)

    templates = await schedule_template_service.update_doctor_templates(
        db, doctor_id, data.slots, clinic_id=clinic_id
    )
    return success_response(
        data=[ScheduleTemplateResponse.model_validate(t) for t in templates],
        message="排班模板已更新",
    )


@router.post("/schedules/generate", summary="根据模板生成排班")
async def generate_schedules(
    weeks: int = 1,
    doctor_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    根据模板生成未来 N 周的排班

    - 管理员: 可为所有医生或指定医生生成
    - 医生: 只能为自己生成

    逻辑: 有模板按模板，无模板沿用上周排班
    """
    # 权限检查
    if current_user.role == "doctor":
        doctor_id = current_user.doctor_id
        if not doctor_id:
            raise AppException(code=40001, message="账号未关联医生信息", status_code=400)
    elif current_user.role != "admin":
        raise AppException(code=40301, message="无权操作", status_code=403)

    result = await schedule_template_service.generate_schedules_from_templates(
        db, weeks=weeks, doctor_id=doctor_id
    )
    return success_response(
        data=result,
        message=f"生成完成: 新建 {result['created']} 条, 跳过 {result['skipped']} 条",
    )


# ========== 本周/下周排班编辑 ==========

def _get_week_range(week: str) -> tuple[date, date]:
    """计算本周或下周的日期范围 (周一~周日)"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    if week == "next":
        monday += timedelta(weeks=1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


class WeekScheduleSlot(BaseModel):
    """单天排班时段"""
    date: date
    start_time: time
    end_time: time
    is_open: bool
    max_patients: int = 20
    clinic_id: int | None = None


class WeekScheduleUpdate(BaseModel):
    """一周排班更新请求"""
    slots: list[WeekScheduleSlot]


@router.get(
    "/doctors/{doctor_id}/week-schedules/{week}",
    summary="获取医生本周或下周排班",
)
async def get_week_schedules(
    doctor_id: int,
    week: Literal["current", "next"],
    clinic_id: int | None = Query(None, description="按门店过滤排班"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取医生本周(current)或下周(next)的实际排班记录

    可通过 clinic_id 过滤特定门店的排班
    """
    monday, sunday = _get_week_range(week)

    query = (
        select(Schedule)
        .where(
            Schedule.doctor_id == doctor_id,
            Schedule.date >= monday,
            Schedule.date <= sunday,
        )
        .order_by(Schedule.date, Schedule.start_time)
    )
    if clinic_id:
        query = query.where(Schedule.clinic_id == clinic_id)

    result = await db.execute(query)
    schedules = list(result.scalars().all())

    data = []
    for s in schedules:
        data.append({
            "id": s.id,
            "date": s.date.isoformat(),
            "weekday": s.date.weekday(),
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "max_patients": s.max_patients,
            "current_patients": s.current_patients,
            "status": s.status,
            "clinic_id": s.clinic_id,
        })

    return success_response(data={
        "week": week,
        "date_from": monday.isoformat(),
        "date_to": sunday.isoformat(),
        "schedules": data,
    })


@router.put(
    "/doctors/{doctor_id}/week-schedules/{week}",
    summary="修改医生本周或下周排班",
)
async def update_week_schedules(
    doctor_id: int,
    week: Literal["current", "next"],
    data: WeekScheduleUpdate,
    clinic_id: int | None = Query(None, description="目标门店 ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    修改医生本周(current)或下周(next)的排班

    权限: 医生本人或管理员
    可通过 clinic_id 指定门店, 不传则使用主门店
    """
    # 权限检查
    if current_user.role == "doctor":
        if current_user.doctor_id != doctor_id:
            raise AppException(code=40301, message="只能修改自己的排班", status_code=403)
    elif current_user.role != "admin":
        raise AppException(code=40301, message="无权操作", status_code=403)

    # 获取医生
    doc_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = doc_result.scalar_one_or_none()
    if not doctor:
        raise NotFoundException(f"医生不存在 (id={doctor_id})")

    # 确定目标门店 (优先参数, 其次第一个关联门店)
    target_clinic_id = clinic_id or doctor.first_clinic_id
    if not target_clinic_id:
        raise AppException(code=40001, message="医生未关联任何门店", status_code=400)

    monday, sunday = _get_week_range(week)
    created = 0
    updated = 0
    closed = 0

    for slot in data.slots:
        # 确保日期在目标周范围内
        if slot.date < monday or slot.date > sunday:
            continue

        # 该时段使用的门店: 优先 slot 级别, 其次全局
        slot_clinic_id = slot.clinic_id or target_clinic_id

        # 查找已有排班
        exist_result = await db.execute(
            select(Schedule).where(
                Schedule.doctor_id == doctor_id,
                Schedule.date == slot.date,
                Schedule.start_time == slot.start_time,
            )
        )
        existing = exist_result.scalar_one_or_none()

        if slot.is_open:
            if existing:
                if existing.status == "closed":
                    existing.status = "open"
                    updated += 1
                existing.max_patients = slot.max_patients
                existing.clinic_id = slot_clinic_id
            else:
                new_schedule = Schedule(
                    doctor_id=doctor_id,
                    clinic_id=slot_clinic_id,
                    date=slot.date,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    max_patients=slot.max_patients,
                    current_patients=0,
                    status="open",
                )
                db.add(new_schedule)
                created += 1
        else:
            if existing and existing.status != "closed":
                existing.status = "closed"
                closed += 1

    await db.flush()

    return success_response(
        data={"created": created, "updated": updated, "closed": closed},
        message=f"排班已更新: 新建{created}条, 恢复{updated}条, 关闭{closed}条",
    )
