"""排班模板 Schema"""

from datetime import time
from pydantic import BaseModel


class TemplateSlot(BaseModel):
    """单个时段模板"""
    weekday: int          # 0=周一 ... 6=周日
    start_time: time      # 09:00
    end_time: time        # 12:00
    max_patients: int = 20
    is_active: bool = True


class ScheduleTemplateResponse(BaseModel):
    """排班模板响应"""
    id: int
    doctor_id: int
    clinic_id: int
    weekday: int
    start_time: time
    end_time: time
    max_patients: int
    is_active: bool

    model_config = {"from_attributes": True}


class WeekTemplateUpdate(BaseModel):
    """
    整周模板更新请求

    前端提交 7 天 x N 个时段的完整模板列表。
    后端会删除旧模板，重新创建。
    """
    slots: list[TemplateSlot]
