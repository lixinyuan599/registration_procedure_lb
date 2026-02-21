"""排班模板模型"""

from datetime import datetime, time
from sqlalchemy import (
    String, Integer, Boolean, ForeignKey, DateTime, Time,
    func, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScheduleTemplate(Base):
    """
    排班周模板 - 医生每周固定排班规则

    每条记录表示：某医生在某门店的某个星期几的某个时段出诊。
    系统根据模板自动生成未来具体日期的排班(schedules)。
    """

    __tablename__ = "schedule_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=True, index=True,
        comment="所属企业 ID"
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.id"), nullable=False, index=True,
        comment="医生 ID"
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinics.id"), nullable=False, index=True,
        comment="门店 ID"
    )
    weekday: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="星期几: 0=周一, 1=周二, ..., 6=周日"
    )
    start_time: Mapped[time] = mapped_column(
        Time, nullable=False, comment="开始时间"
    )
    end_time: Mapped[time] = mapped_column(
        Time, nullable=False, comment="结束时间"
    )
    max_patients: Mapped[int] = mapped_column(
        Integer, default=20, comment="最大接诊人数"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    doctor: Mapped["Doctor"] = relationship(back_populates="schedule_templates")
    clinic: Mapped["Clinic"] = relationship(back_populates="schedule_templates")

    # 约束
    __table_args__ = (
        UniqueConstraint(
            "doctor_id", "weekday", "start_time",
            name="uq_doctor_weekday_time"
        ),
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_weekday_range"),
    )

    @property
    def weekday_label(self) -> str:
        """星期几的中文标签"""
        labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return labels[self.weekday] if 0 <= self.weekday <= 6 else "未知"

    @property
    def time_period(self) -> str:
        """上午/下午标签"""
        if self.start_time and self.start_time.hour < 12:
            return "上午"
        return "下午"

    def __repr__(self) -> str:
        return (
            f"<ScheduleTemplate(id={self.id}, doctor_id={self.doctor_id}, "
            f"{self.weekday_label} {self.start_time}-{self.end_time})>"
        )
