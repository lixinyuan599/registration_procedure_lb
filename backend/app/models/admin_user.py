"""管理员账号模型 - 支持多租户管理"""

import hashlib
import secrets
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AdminUser(Base):
    """管理后台账号表"""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="登录账号"
    )
    password_hash: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="密码哈希 (pbkdf2_sha256)"
    )
    display_name: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="显示名称"
    )
    tenant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tenants.id"), nullable=True, index=True,
        comment="所属企业 ID (NULL = 超级管理员)"
    )
    role: Mapped[str] = mapped_column(
        String(16), default="tenant_admin",
        comment="角色: super_admin / tenant_admin"
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

    # ---- 关联关系 ----
    tenant: Mapped["Tenant | None"] = relationship(
        back_populates="admin_users", lazy="selectin"
    )

    @property
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"

    def set_password(self, password: str) -> None:
        """设置密码（加盐哈希）"""
        salt = secrets.token_hex(16)
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        self.password_hash = f"{salt}:{h.hex()}"

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        if ":" not in self.password_hash:
            return False
        salt, hash_hex = self.password_hash.split(":", 1)
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return h.hex() == hash_hex

    def __str__(self) -> str:
        return self.display_name or self.username

    def __repr__(self) -> str:
        return f"<AdminUser(id={self.id}, username={self.username}, role={self.role})>"
