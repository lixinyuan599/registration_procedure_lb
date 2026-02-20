"""用户模型"""

from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """用户表 - 对应微信小程序用户"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, comment="微信 openid"
    )
    nickname: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="用户昵称"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="手机号"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="头像 URL"
    )
    role: Mapped[str] = mapped_column(
        String(16), default="patient",
        comment="角色: patient(患者) / doctor(医生) / admin(管理员)"
    )
    doctor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("doctors.id"), nullable=True,
        comment="关联医生 ID (仅 role=doctor 时有值)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    doctor: Mapped["Doctor | None"] = relationship(
        foreign_keys=[doctor_id], lazy="selectin"
    )

    @property
    def is_doctor(self) -> bool:
        return self.role == "doctor" and self.doctor_id is not None

    def __repr__(self) -> str:
        return f"<User(id={self.id}, openid={self.openid}, role={self.role})>"
