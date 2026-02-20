"""医生 Schema"""

from datetime import datetime
from pydantic import BaseModel


class ClinicBrief(BaseModel):
    """门店简要信息 (嵌套在医生响应中)"""
    id: int
    name: str

    model_config = {"from_attributes": True}


class DoctorBase(BaseModel):
    """医生基础字段"""
    name: str
    expertise: str
    description: str | None = None
    avatar_url: str | None = None


class DoctorResponse(DoctorBase):
    """医生响应"""
    id: int
    is_active: bool
    created_at: datetime
    clinics: list[ClinicBrief] = []

    model_config = {"from_attributes": True}


class DoctorBrief(BaseModel):
    """医生简要信息 (用于预约详情中嵌套)"""
    id: int
    name: str
    expertise: str

    model_config = {"from_attributes": True}
