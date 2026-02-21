"""医生模型"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.doctor_clinic import doctor_clinics


class Doctor(Base):
    """医生表"""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=True, index=True,
        comment="所属企业 ID"
    )
    # clinic_id 保留在数据库中 (SQLite 不支持 DROP COLUMN), 但设为 nullable, 代码不再使用
    clinic_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("clinics.id"), nullable=True, index=True,
        comment="(已废弃) 旧主门店 ID, 请使用 clinics 多对多关系"
    )
    name: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="医生姓名"
    )
    expertise: Mapped[str] = mapped_column(
        String(256), nullable=False, default="",
        comment="擅长领域 (如: 针灸调理失眠、中药治疗脾胃病等)"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="医生简介"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="医生头像"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否在职"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # ---- 关联关系 ----
    tenant: Mapped["Tenant | None"] = relationship(
        back_populates="doctors", lazy="selectin"
    )

    # 多对多: 医生可在多个门店出诊 (唯一的门店关系)
    clinics: Mapped[list["Clinic"]] = relationship(
        secondary=doctor_clinics,
        back_populates="m2m_doctors",
        lazy="selectin",
    )

    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="doctor", lazy="selectin"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="doctor", lazy="selectin"
    )
    schedule_templates: Mapped[list["ScheduleTemplate"]] = relationship(
        back_populates="doctor", lazy="selectin"
    )

    @property
    def first_clinic_id(self) -> int | None:
        """获取第一个关联门店 ID (兼容旧逻辑)"""
        if self.clinics:
            return self.clinics[0].id
        return self.clinic_id

    def __str__(self) -> str:
        return self.name or ""

    def __repr__(self) -> str:
        return self.name or ""
