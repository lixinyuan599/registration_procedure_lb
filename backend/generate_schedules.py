"""
排班批量生成工具（基于模板）

优先级:
  1. 如果医生有排班模板 (schedule_templates) -> 按模板生成
  2. 如果没有模板 -> 查找上周实际排班作为参考（沿用上周）
  3. 如果上周也没有 -> 使用默认规则（工作日上下午、周末仅上午）

运行方式:
  python generate_schedules.py              # 默认生成未来 2 周
  python generate_schedules.py --weeks 4    # 生成未来 4 周
  python generate_schedules.py --doctor 1   # 只为指定医生生成
"""

import argparse
import asyncio
from datetime import date, time, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import engine, AsyncSessionLocal, Base
from app.models.doctor import Doctor
from app.models.schedule import Schedule
from app.models.schedule_template import ScheduleTemplate


# 默认时段模板（无模板且无上周排班时的兜底方案）
WEEKDAY_SLOTS = [
    (time(9, 0), time(12, 0)),   # 上午
    (time(14, 0), time(17, 0)),  # 下午
]
WEEKEND_SLOTS = [
    (time(9, 0), time(12, 0)),   # 仅上午
]
DEFAULT_MAX_PATIENTS = 20


async def generate(weeks: int = 2, doctor_id: int | None = None):
    """生成排班"""

    async with AsyncSessionLocal() as session:
        # 查询医生
        query = select(Doctor).where(Doctor.is_active == True)
        if doctor_id:
            query = query.where(Doctor.id == doctor_id)
        result = await session.execute(query)
        doctors = list(result.scalars().all())

        if not doctors:
            print("❌ 没有找到在职医生，请先通过管理后台添加医生")
            return

        # 加载所有模板，按医生分组
        tmpl_query = select(ScheduleTemplate).where(ScheduleTemplate.is_active == True)
        if doctor_id:
            tmpl_query = tmpl_query.where(ScheduleTemplate.doctor_id == doctor_id)
        tmpl_result = await session.execute(tmpl_query)
        all_templates = list(tmpl_result.scalars().all())

        doctor_templates: dict[int, list[ScheduleTemplate]] = {}
        for t in all_templates:
            doctor_templates.setdefault(t.doctor_id, []).append(t)

        today = date.today()
        total_days = weeks * 7
        created = 0
        skipped = 0
        template_used = 0
        last_week_used = 0
        default_used = 0

        for doctor in doctors:
            templates = doctor_templates.get(doctor.id)
            last_week_schedules = None

            # 如果没有模板，尝试获取上周排班
            if not templates:
                last_week_schedules = await _get_last_week_schedules(
                    session, doctor.id, today
                )

            for day_offset in range(1, total_days + 1):
                current_date = today + timedelta(days=day_offset)
                weekday = current_date.weekday()

                # 获取当天的时段列表
                slots = _get_day_slots(
                    doctor, weekday, templates, last_week_schedules
                )

                for start, end, max_p, source in slots:
                    # 检查是否已存在
                    exists_query = select(Schedule).where(
                        Schedule.doctor_id == doctor.id,
                        Schedule.date == current_date,
                        Schedule.start_time == start,
                    )
                    exists = await session.execute(exists_query)
                    if exists.scalar_one_or_none():
                        skipped += 1
                        continue

                    schedule = Schedule(
                        doctor_id=doctor.id,
                        clinic_id=doctor.first_clinic_id,
                        date=current_date,
                        start_time=start,
                        end_time=end,
                        max_patients=max_p,
                        current_patients=0,
                        status="open",
                    )
                    session.add(schedule)
                    created += 1

                    if source == "template":
                        template_used += 1
                    elif source == "last_week":
                        last_week_used += 1
                    else:
                        default_used += 1

        await session.commit()

        print("=" * 50)
        print("✅ 排班生成完成!")
        print(f"   医生数: {len(doctors)}")
        print(f"   时间范围: {today + timedelta(days=1)} ~ {today + timedelta(days=total_days)}")
        print(f"   新建排班: {created} 条")
        print(f"   跳过(已存在): {skipped} 条")
        print(f"   来源统计:")
        print(f"     - 按模板生成: {template_used} 条")
        print(f"     - 沿用上周:   {last_week_used} 条")
        print(f"     - 默认规则:   {default_used} 条")
        print("=" * 50)
        print()
        print("排班详情可在管理后台查看: http://127.0.0.1:8000/admin")


def _get_day_slots(
    doctor,
    weekday: int,
    templates: list[ScheduleTemplate] | None,
    last_week_schedules: list[Schedule] | None,
) -> list[tuple]:
    """
    获取某天的排班时段

    返回: [(start_time, end_time, max_patients, source), ...]
    """
    # 优先级 1: 模板
    if templates:
        day_tmpl = [t for t in templates if t.weekday == weekday]
        if day_tmpl:
            return [
                (t.start_time, t.end_time, t.max_patients, "template")
                for t in day_tmpl
            ]

    # 优先级 2: 上周排班
    if last_week_schedules:
        day_schedules = [s for s in last_week_schedules if s.date.weekday() == weekday]
        if day_schedules:
            return [
                (s.start_time, s.end_time, s.max_patients, "last_week")
                for s in day_schedules
            ]

    # 优先级 3: 默认规则
    slots = WEEKDAY_SLOTS if weekday < 5 else WEEKEND_SLOTS
    return [
        (start, end, DEFAULT_MAX_PATIENTS, "default")
        for start, end in slots
    ]


async def _get_last_week_schedules(session, doctor_id: int, today: date) -> list:
    """获取医生上周的排班记录"""
    last_week_start = today - timedelta(days=today.weekday() + 7)
    last_week_end = last_week_start + timedelta(days=6)

    result = await session.execute(
        select(Schedule).where(
            Schedule.doctor_id == doctor_id,
            Schedule.date >= last_week_start,
            Schedule.date <= last_week_end,
        )
    )
    schedules = list(result.scalars().all())
    return schedules if schedules else None


def main():
    parser = argparse.ArgumentParser(description="批量生成排班 (基于模板)")
    parser.add_argument("--weeks", type=int, default=2, help="生成未来 N 周的排班 (默认 2)")
    parser.add_argument("--doctor", type=int, default=None, help="只为指定医生 ID 生成")
    args = parser.parse_args()

    asyncio.run(generate(weeks=args.weeks, doctor_id=args.doctor))


if __name__ == "__main__":
    main()
