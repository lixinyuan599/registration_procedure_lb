"""预约模型"""

from datetime import datetime, date
from sqlalchemy import (
    String, Text, Integer, ForeignKey, DateTime, Date,
    func, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Appointment(Base):
    """预约挂号表"""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=True, index=True,
        comment="所属企业 ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True,
        comment="用户 ID"
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.id"), nullable=False, index=True,
        comment="医生 ID"
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinics.id"), nullable=False, index=True,
        comment="门店 ID"
    )
    schedule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedules.id"), nullable=False,
        comment="排班 ID"
    )
    appointment_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="预约日期"
    )
    time_slot: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="时间段 (如 09:00-12:00)"
    )
    status: Mapped[str] = mapped_column(
        String(16), default="confirmed",
        comment="状态: confirmed(已确认) / cancelled(已取消) / completed(已完成)"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="患者备注 (病情描述等)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    user: Mapped["User"] = relationship(back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")
    clinic: Mapped["Clinic"] = relationship(back_populates="appointments")
    schedule: Mapped["Schedule"] = relationship(back_populates="appointments")

    # 联合唯一约束: 同一用户同一排班只能预约一次 (防止重复预约)
    __table_args__ = (
        UniqueConstraint(
            "user_id", "schedule_id",
            name="uq_user_schedule"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Appointment(id={self.id}, user_id={self.user_id}, "
            f"doctor_id={self.doctor_id}, date={self.appointment_date})>"
        )
