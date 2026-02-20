"""门店 Schema"""

from datetime import datetime
from pydantic import BaseModel


class ClinicBase(BaseModel):
    """门店基础字段"""
    name: str
    address: str
    phone: str | None = None
    description: str | None = None
    image_url: str | None = None


class ClinicResponse(ClinicBase):
    """门店响应"""
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
