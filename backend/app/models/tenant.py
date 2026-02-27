"""企业/组织模型 - 多租户支持"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tenant(Base):
    """企业/组织表 - 每个入驻的企业是一个 tenant"""

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="企业名称"
    )
    contact_name: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="联系人姓名"
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="联系电话"
    )
    subtitle: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="企业标语/副标题 (显示在小程序首页)"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="企业简介"
    )
    logo_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="企业 Logo"
    )
    status: Mapped[str] = mapped_column(
        String(16), default="pending",
        comment="状态: pending(待审核) / approved(已通过) / rejected(已拒绝)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # ---- 关联关系 ----
    admin_users: Mapped[list["AdminUser"]] = relationship(
        back_populates="tenant", lazy="selectin",
        cascade="all, delete-orphan",
    )
    clinics: Mapped[list["Clinic"]] = relationship(
        back_populates="tenant", lazy="selectin",
    )
    doctors: Mapped[list["Doctor"]] = relationship(
        back_populates="tenant", lazy="selectin",
    )

    def __str__(self) -> str:
        return self.name or ""

    def __repr__(self) -> str:
        return self.name or ""
