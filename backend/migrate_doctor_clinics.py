"""
数据库迁移脚本: 添加 doctor_clinics 多对多关联表

运行方式: cd backend && python migrate_doctor_clinics.py

功能:
1. 创建 doctor_clinics 关联表
2. 将现有医生的 clinic_id (主门店) 自动写入关联表
"""

import asyncio
from sqlalchemy import text
from app.database import engine, AsyncSessionLocal


async def migrate():
    print("=" * 50)
    print("开始迁移: 创建 doctor_clinics 多对多关联表")
    print("=" * 50)

    async with engine.begin() as conn:
        # 检查表是否已存在
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='doctor_clinics'")
        )
        if result.scalar():
            print("  doctor_clinics 表已存在, 跳过创建")
        else:
            # 创建关联表
            await conn.execute(text("""
                CREATE TABLE doctor_clinics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL,
                    clinic_id INTEGER NOT NULL,
                    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
                    FOREIGN KEY (clinic_id) REFERENCES clinics(id),
                    UNIQUE (doctor_id, clinic_id)
                )
            """))
            await conn.execute(text(
                "CREATE INDEX ix_doctor_clinics_doctor_id ON doctor_clinics(doctor_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX ix_doctor_clinics_clinic_id ON doctor_clinics(clinic_id)"
            ))
            print("  doctor_clinics 表创建成功")

    # 将现有医生的主门店写入关联表
    async with AsyncSessionLocal() as session:
        # 查询所有医生的 clinic_id
        result = await session.execute(text("SELECT id, clinic_id FROM doctors"))
        doctors = result.fetchall()

        inserted = 0
        skipped = 0

        for doc_id, clinic_id in doctors:
            # 检查是否已存在
            exists = await session.execute(
                text("SELECT 1 FROM doctor_clinics WHERE doctor_id=:did AND clinic_id=:cid"),
                {"did": doc_id, "cid": clinic_id},
            )
            if exists.scalar():
                skipped += 1
                continue

            await session.execute(
                text("INSERT INTO doctor_clinics (doctor_id, clinic_id) VALUES (:did, :cid)"),
                {"did": doc_id, "cid": clinic_id},
            )
            inserted += 1

        await session.commit()

        print(f"  关联数据: 新增 {inserted} 条, 已存在 {skipped} 条")
        print()
        print("迁移完成!")
        print()
        print("  现在可以在管理后台的「医生管理」中为医生配置多个出诊门店。")
        print("  编辑医生 -> 在「出诊门店(多选)」中选择门店 -> 保存")
        print()


if __name__ == "__main__":
    asyncio.run(migrate())
