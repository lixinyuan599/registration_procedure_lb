"""门店模型"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.doctor_clinic import doctor_clinics


class Clinic(Base):
    """门店表 - 医院/门诊分院"""

    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="门店名称"
    )
    address: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="门店地址"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="联系电话"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="门店介绍"
    )
    image_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="门店图片"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否营业"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # ---- 关联关系 ----

    # 多对多: 所有在该门店出诊的医生
    m2m_doctors: Mapped[list["Doctor"]] = relationship(
        secondary=doctor_clinics,
        back_populates="clinics",
        lazy="selectin",
    )

    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="clinic", lazy="selectin"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="clinic", lazy="selectin"
    )
    schedule_templates: Mapped[list["ScheduleTemplate"]] = relationship(
        back_populates="clinic", lazy="selectin"
    )

    def __str__(self) -> str:
        return self.name or ""

    def __repr__(self) -> str:
        return self.name or ""
