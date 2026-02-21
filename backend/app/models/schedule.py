"""排班模型"""

from datetime import datetime, date, time
from sqlalchemy import (
    String, Integer, ForeignKey, DateTime, Date, Time,
    func, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Schedule(Base):
    """排班表 - 医生在某门店的出诊时间段"""

    __tablename__ = "schedules"

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
    date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="排班日期"
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
    current_patients: Mapped[int] = mapped_column(
        Integer, default=0, comment="当前已预约人数"
    )
    status: Mapped[str] = mapped_column(
        String(16), default="open",
        comment="状态: open(开放) / full(已满) / closed(关闭)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    doctor: Mapped["Doctor"] = relationship(back_populates="schedules")
    clinic: Mapped["Clinic"] = relationship(back_populates="schedules")
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="schedule", lazy="selectin",
        cascade="all, delete-orphan",
    )

    # 联合唯一约束: 同一医生同一天同一时段不能重复排班
    __table_args__ = (
        UniqueConstraint(
            "doctor_id", "date", "start_time",
            name="uq_doctor_date_time"
        ),
    )

    @property
    def is_available(self) -> bool:
        """是否还有余号"""
        return self.status == "open" and self.current_patients < self.max_patients

    def __repr__(self) -> str:
        return (
            f"<Schedule(id={self.id}, doctor_id={self.doctor_id}, "
            f"date={self.date}, {self.start_time}-{self.end_time})>"
        )
