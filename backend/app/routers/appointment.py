"""预约路由"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services import appointment_service
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentDetail,
)
from app.schemas.doctor import DoctorBrief
from app.schemas.clinic import ClinicResponse
from app.schemas.common import success_response
from app.utils.deps import get_current_user

router = APIRouter(prefix="/appointments", tags=["预约"])


@router.post("", summary="创建预约")
async def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建预约挂号

    需要在 Header 中传递 X-User-OpenID

    业务校验：
    - 排班必须存在且开放
    - 排班未满
    - 不可重复预约
    """
    appointment = await appointment_service.create_appointment(
        db, current_user.id, data
    )
    return success_response(
        data=AppointmentResponse.model_validate(appointment),
        message="预约成功",
    )


@router.get("/me", summary="我的预约")
async def my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的所有预约记录

    需要在 Header 中传递 X-User-OpenID
    返回预约详情，包含医生和门店信息
    """
    appointments = await appointment_service.get_user_appointments(
        db, current_user.id
    )
    result = []
    for apt in appointments:
        detail = AppointmentDetail(
            id=apt.id,
            status=apt.status,
            appointment_date=apt.appointment_date,
            time_slot=apt.time_slot,
            notes=apt.notes,
            doctor=DoctorBrief.model_validate(apt.doctor),
            clinic=ClinicResponse.model_validate(apt.clinic),
            created_at=apt.created_at,
        )
        result.append(detail)
    return success_response(data=result)


@router.put("/{appointment_id}/cancel", summary="取消预约")
async def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    取消预约

    需要在 Header 中传递 X-User-OpenID
    只能取消自己的、状态为 confirmed 的预约
    """
    appointment = await appointment_service.cancel_appointment(
        db, current_user.id, appointment_id
    )
    return success_response(
        data=AppointmentResponse.model_validate(appointment),
        message="预约已取消",
    )
