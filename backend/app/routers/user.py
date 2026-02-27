"""用户路由 - 个人信息 & 医生身份绑定"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.schemas.common import success_response
from app.utils.deps import get_current_user
from app.utils.exceptions import AppException

router = APIRouter(prefix="/users", tags=["用户"])


class UserProfileResponse(BaseModel):
    id: int
    openid: str
    nickname: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    role: str
    doctor_id: int | None = None
    doctor_name: str | None = None

    model_config = {"from_attributes": True}


class BindDoctorRequest(BaseModel):
    invite_code: str


@router.get("/me", summary="获取当前用户信息")
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doctor_name = None
    if user.doctor_id:
        result = await db.execute(
            select(Doctor.name).where(Doctor.id == user.doctor_id)
        )
        doctor_name = result.scalar_one_or_none()

    return success_response(
        data=UserProfileResponse(
            id=user.id,
            openid=user.openid,
            nickname=user.nickname,
            phone=user.phone,
            avatar_url=user.avatar_url,
            role=user.role or "patient",
            doctor_id=user.doctor_id,
            doctor_name=doctor_name,
        ).model_dump()
    )


@router.post("/bind-doctor", summary="通过邀请码绑定医生身份")
async def bind_doctor(
    data: BindDoctorRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    用户输入管理员提供的邀请码，绑定为对应医生身份。
    绑定后 role 变为 doctor，doctor_id 指向对应医生。
    """
    if user.role == "doctor" and user.doctor_id:
        raise AppException(code=40001, message="您已经是医生身份，无需重复绑定")

    code = data.invite_code.strip().upper()
    if not code:
        raise AppException(code=40002, message="请输入邀请码")

    result = await db.execute(
        select(Doctor).where(Doctor.invite_code == code, Doctor.is_active == True)
    )
    doctor = result.scalar_one_or_none()

    if doctor is None:
        raise AppException(code=40003, message="邀请码无效，请核实后重试")

    existing = await db.execute(
        select(User).where(User.doctor_id == doctor.id, User.role == "doctor")
    )
    if existing.scalar_one_or_none():
        raise AppException(code=40004, message="该医生已被其他账号绑定")

    user.role = "doctor"
    user.doctor_id = doctor.id
    await db.flush()
    await db.refresh(user)

    return success_response(
        data={
            "role": user.role,
            "doctor_id": user.doctor_id,
            "doctor_name": doctor.name,
        },
        message=f"绑定成功！您已认证为 {doctor.name} 医生",
    )


@router.post("/unbind-doctor", summary="解除医生身份绑定")
async def unbind_doctor(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "doctor":
        raise AppException(code=40005, message="当前不是医生身份")

    user.role = "patient"
    user.doctor_id = None
    await db.flush()

    return success_response(message="已解除医生身份")
