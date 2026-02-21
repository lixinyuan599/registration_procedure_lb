"""
多租户迁移脚本

功能:
1. 创建 tenants, admin_users 新表
2. 给现有表添加 tenant_id 列
3. 创建一个默认企业, 把所有现有数据关联到该企业
4. 创建超级管理员账号
"""

import asyncio
import sys
from sqlalchemy import text

sys.path.insert(0, ".")

from app.database import engine, AsyncSessionLocal, init_db
from app.models.tenant import Tenant
from app.models.admin_user import AdminUser


async def migrate():
    # 1. 创建所有新表 (tenants, admin_users) + 新列不会自动添加
    print("[1/5] 创建新表 (tenants, admin_users) ...")
    await init_db()

    async with engine.begin() as conn:
        # 2. 给现有表添加 tenant_id 列 (如果不存在)
        tables_need_tenant = ["clinics", "doctors", "schedules", "schedule_templates", "appointments"]

        print("[2/5] 给现有表添加 tenant_id 列 ...")
        for table in tables_need_tenant:
            try:
                await conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)"
                ))
                print(f"      {table}.tenant_id  已添加")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"      {table}.tenant_id  已存在, 跳过")
                else:
                    print(f"      {table}.tenant_id  跳过 ({e})")

    # 3. 创建默认企业
    print("[3/5] 创建默认企业 ...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Tenant).where(Tenant.name == "默认企业").limit(1)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(
                name="默认企业",
                contact_name="管理员",
                status="approved",
            )
            session.add(tenant)
            await session.flush()
            print(f"      已创建: 默认企业 (id={tenant.id})")
        else:
            print(f"      已存在: 默认企业 (id={tenant.id})")

        tenant_id = tenant.id
        await session.commit()

    # 4. 把现有数据关联到默认企业
    print("[4/5] 迁移现有数据到默认企业 ...")
    async with engine.begin() as conn:
        for table in tables_need_tenant:
            result = await conn.execute(text(
                f"UPDATE {table} SET tenant_id = :tid WHERE tenant_id IS NULL"
            ), {"tid": tenant_id})
            print(f"      {table}: 更新了 {result.rowcount} 行")

    # 5. 创建超级管理员账号
    print("[5/5] 检查超级管理员账号 ...")
    async with AsyncSessionLocal() as session:
        from app.config import get_settings
        settings = get_settings()

        result = await session.execute(
            select(AdminUser).where(AdminUser.role == "super_admin").limit(1)
        )
        if result.scalar_one_or_none() is None:
            admin = AdminUser(
                username=settings.ADMIN_USERNAME,
                role="super_admin",
                display_name="超级管理员",
                is_active=True,
            )
            admin.set_password(settings.ADMIN_PASSWORD)
            session.add(admin)
            await session.commit()
            print(f"      已创建超级管理员: {settings.ADMIN_USERNAME}")
        else:
            print("      超级管理员已存在, 跳过")

        # 同时为默认企业创建一个企业管理员
        result = await session.execute(
            select(AdminUser).where(
                AdminUser.tenant_id == tenant_id,
                AdminUser.role == "tenant_admin",
            ).limit(1)
        )
        if result.scalar_one_or_none() is None:
            ta = AdminUser(
                username="tenant_admin",
                role="tenant_admin",
                display_name="默认企业管理员",
                tenant_id=tenant_id,
                is_active=True,
            )
            ta.set_password("admin123")
            session.add(ta)
            await session.commit()
            print("      已创建默认企业管理员: tenant_admin / admin123")
        else:
            print("      默认企业管理员已存在, 跳过")

    print("\n迁移完成!")
    print("=" * 40)
    print("超级管理员账号: 从 .env 中的 ADMIN_USERNAME / ADMIN_PASSWORD 读取")
    print("默认企业管理员: tenant_admin / admin123 (请及时修改密码)")


if __name__ == "__main__":
    asyncio.run(migrate())
