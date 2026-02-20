"""排班 Schema"""

from datetime import date, time, datetime
from pydantic import BaseModel


class ScheduleBase(BaseModel):
    """排班基础字段"""
    doctor_id: int
    clinic_id: int
    date: date
    start_time: time
    end_time: time
    max_patients: int = 20


class ScheduleResponse(BaseModel):
    """排班响应"""
    id: int
    doctor_id: int
    clinic_id: int
    date: date
    start_time: time
    end_time: time
    max_patients: int
    current_patients: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
