"""医生-门店 多对多关联表"""

from sqlalchemy import Table, Column, Integer, ForeignKey, UniqueConstraint
from app.database import Base

doctor_clinics = Table(
    "doctor_clinics",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("doctor_id", Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("clinic_id", Integer, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True),
    UniqueConstraint("doctor_id", "clinic_id", name="uq_doctor_clinic"),
)
