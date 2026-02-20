"""预约 Schema"""

from datetime import date, datetime
from pydantic import BaseModel

from app.schemas.doctor import DoctorBrief
from app.schemas.clinic import ClinicResponse


class AppointmentCreate(BaseModel):
    """创建预约请求"""
    doctor_id: int
    clinic_id: int
    schedule_id: int
    notes: str | None = None


class AppointmentResponse(BaseModel):
    """预约响应"""
    id: int
    user_id: int
    doctor_id: int
    clinic_id: int
    schedule_id: int
    appointment_date: date
    time_slot: str
    status: str
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AppointmentDetail(BaseModel):
    """预约详情响应 (含医生和门店信息)"""
    id: int
    status: str
    appointment_date: date
    time_slot: str
    notes: str | None = None
    doctor: DoctorBrief
    clinic: ClinicResponse
    created_at: datetime

    model_config = {"from_attributes": True}
