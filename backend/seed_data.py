"""
测试数据填充脚本

运行方式: python seed_data.py
功能: 创建门店、医生、排班等测试数据, 含多对多关联
"""

import asyncio
from datetime import date, time, timedelta

from app.database import engine, AsyncSessionLocal, Base
from app.models.user import User
from app.models.clinic import Clinic
from app.models.doctor import Doctor
from app.models.doctor_clinic import doctor_clinics
from app.models.schedule import Schedule


async def seed():
    """填充测试数据"""

    # 重建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # ========== 1. 创建测试用户 ==========
        users = [
            User(openid="test_user_001", nickname="测试用户A", phone="13800000001"),
            User(openid="test_user_002", nickname="测试用户B", phone="13800000002"),
        ]
        session.add_all(users)

        # ========== 2. 创建门店 ==========
        clinics = [
            Clinic(
                name="仁心堂中医门诊（总院）",
                address="北京市朝阳区建国路100号",
                phone="010-12345678",
                description="综合门诊，专注中西医结合治疗，拥有20年历史",
                image_url="https://picsum.photos/seed/clinic1/400/200",
            ),
            Clinic(
                name="仁心堂中医门诊（海淀分院）",
                address="北京市海淀区中关村大街50号",
                phone="010-87654321",
                description="分院门诊，侧重儿科与妇科",
                image_url="https://picsum.photos/seed/clinic2/400/200",
            ),
            Clinic(
                name="仁心堂中医门诊（西城分院）",
                address="北京市西城区西单北大街80号",
                phone="010-11112222",
                description="特色针灸推拿，骨伤康复专科",
                image_url="https://picsum.photos/seed/clinic3/400/200",
            ),
        ]
        session.add_all(clinics)
        await session.flush()  # 获取 ID

        # ========== 3. 创建医生 (不再设置 clinic_id, 全部通过多对多关联) ==========
        # doctor_clinic_map: 记录每个医生的主门店索引, 用于后续关联和排班
        doctor_defs = [
            # (门店索引, 名字, 擅长领域, 简介, 头像)
            (0, "张明", "中西医结合治疗高血压、糖尿病、心血管疾病",
             "从医25年，师从国医大师，精通经方与现代医学结合",
             "https://picsum.photos/seed/doc1/100/100"),
            (0, "李芳", "体质调理、失眠多梦、脾胃虚寒、亚健康调理",
             "中医世家第三代传人，善用膏方与食疗",
             "https://picsum.photos/seed/doc2/100/100"),
            (0, "王强", "中药内服调理肝胆疾病、湿热体质",
             "二十年临床经验，擅长疑难杂症辨证论治",
             "https://picsum.photos/seed/doc3/100/100"),
            (1, "赵丽", "小儿推拿、儿童体质调理、反复感冒咳嗽",
             "儿科中医专家，30年儿童健康管理经验",
             "https://picsum.photos/seed/doc4/100/100"),
            (1, "陈静", "月经不调、痛经、备孕调理、更年期综合征",
             "专注女性中医调理，温和疗法深受信赖",
             "https://picsum.photos/seed/doc5/100/100"),
            (2, "刘伟", "颈椎病、腰椎间盘突出、骨关节退行性病变",
             "骨伤科专家，擅长正骨手法与中药外敷结合治疗",
             "https://picsum.photos/seed/doc6/100/100"),
            (2, "孙燕", "针灸治疗颈肩腰腿痛、面瘫、头痛、失眠",
             "传统针灸推拿传承人，精通经络辨证",
             "https://picsum.photos/seed/doc7/100/100"),
        ]

        doctors = []
        primary_clinic_map = {}  # doctor index -> clinic index
        for i, (clinic_idx, name, expertise, desc, avatar) in enumerate(doctor_defs):
            doc = Doctor(
                name=name,
                expertise=expertise,
                description=desc,
                avatar_url=avatar,
            )
            doctors.append(doc)
            primary_clinic_map[i] = clinic_idx

        session.add_all(doctors)
        await session.flush()

        # ========== 4. 多对多关联: 医生 <-> 门店 ==========
        associations = []
        for i, doc in enumerate(doctors):
            clinic_idx = primary_clinic_map[i]
            associations.append({"doctor_id": doc.id, "clinic_id": clinics[clinic_idx].id})

        # 张明(总院) 也在海淀分院出诊
        associations.append({"doctor_id": doctors[0].id, "clinic_id": clinics[1].id})
        # 李芳(总院) 也在西城分院出诊
        associations.append({"doctor_id": doctors[1].id, "clinic_id": clinics[2].id})
        # 孙燕(西城) 也在总院出诊
        associations.append({"doctor_id": doctors[6].id, "clinic_id": clinics[0].id})

        await session.execute(doctor_clinics.insert(), associations)

        # ========== 5. 创建排班 (未来7天) ==========
        schedules = []
        today = date.today()

        time_slots = [
            (time(9, 0), time(12, 0)),    # 上午
            (time(14, 0), time(17, 0)),   # 下午
        ]

        for i, doctor in enumerate(doctors):
            primary_clinic_id = clinics[primary_clinic_map[i]].id
            for day_offset in range(1, 8):  # 未来7天
                current_date = today + timedelta(days=day_offset)
                weekday = current_date.weekday()
                slots = time_slots if weekday < 5 else [time_slots[0]]

                for start, end in slots:
                    schedules.append(
                        Schedule(
                            doctor_id=doctor.id,
                            clinic_id=primary_clinic_id,
                            date=current_date,
                            start_time=start,
                            end_time=end,
                            max_patients=20,
                            current_patients=0,
                            status="open",
                        )
                    )

        session.add_all(schedules)
        await session.commit()

        print("=" * 50)
        print("  测试数据填充完成!")
        print(f"   用户: {len(users)} 个")
        print(f"   门店: {len(clinics)} 个")
        print(f"   医生: {len(doctors)} 个")
        print(f"   医生-门店关联: {len(associations)} 条")
        print(f"   排班: {len(schedules)} 条")
        print("=" * 50)
        print()
        print("多门店医生示例:")
        print("  - 张明: 总院 + 海淀分院")
        print("  - 李芳: 总院 + 西城分院")
        print("  - 孙燕: 西城分院 + 总院")
        print()
        print("测试用户 openid:")
        for u in users:
            print(f"  - {u.openid} ({u.nickname})")
        print()
        print("可通过以下方式测试 API:")
        print('  curl http://127.0.0.1:8000/api/v1/clinics')
        print('  curl http://127.0.0.1:8000/api/v1/clinics/1/doctors')
        print('  curl http://127.0.0.1:8000/api/v1/doctors/1/clinics')
        print()


if __name__ == "__main__":
    asyncio.run(seed())
