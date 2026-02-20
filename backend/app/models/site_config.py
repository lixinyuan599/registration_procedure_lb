"""系统显示配置模型"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SiteConfig(Base):
    """
    全局显示配置 (单行表)

    管理员在后台切换开关，控制小程序端的显示行为。
    系统始终只有 1 条记录 (id=1)。
    """

    __tablename__ = "site_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    show_remaining_slots: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="小程序是否显示余号数量 (关闭后只显示 可预约/已约满)"
    )
    clinic_name: Mapped[str] = mapped_column(
        String(128), default="门诊挂号系统",
        comment="系统名称 (显示在小程序标题等处)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(),
        comment="最后修改时间"
    )

    def __repr__(self) -> str:
        return f"<SiteConfig(show_remaining={self.show_remaining_slots})>"
