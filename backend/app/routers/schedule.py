"""排班路由"""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import schedule_service
from app.schemas.schedule import ScheduleResponse
from app.schemas.common import success_response

router = APIRouter(prefix="/doctors", tags=["排班"])


@router.get("/{doctor_id}/schedules", summary="获取医生排班")
async def list_schedules_by_doctor(
    doctor_id: int,
    date_from: date | None = Query(None, description="起始日期 (默认今天)"),
    date_to: date | None = Query(None, description="结束日期 (默认起始日期+7天)"),
    clinic_id: int | None = Query(None, description="按门店过滤"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定医生的排班列表

    - 默认查询从今天起 7 天内的可预约排班
    - 支持通过 date_from / date_to 自定义日期范围
    - 支持通过 clinic_id 过滤特定门店的排班
    """
    schedules = await schedule_service.get_schedules_by_doctor(
        db, doctor_id, date_from, date_to, clinic_id=clinic_id
    )
    return success_response(
        data=[ScheduleResponse.model_validate(s) for s in schedules]
    )
