"""
医生周排班总览 - 可视化 HTML 页面

路由: /admin/weekly-schedule
功能: 以表格形式展示每位医生一周的出诊时间排班图
"""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.models.doctor_clinic import doctor_clinics
from app.models.clinic import Clinic
from app.models.schedule_template import ScheduleTemplate

router = APIRouter()

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@router.get("/dashboard/weekly-schedule", response_class=HTMLResponse, include_in_schema=False)
async def weekly_schedule_page(
    clinic_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """医生周排班总览页"""

    # 获取所有门店 (用于筛选下拉)
    clinics_result = await db.execute(
        select(Clinic).where(Clinic.is_active == True).order_by(Clinic.id)
    )
    clinics = list(clinics_result.scalars().all())

    # 获取医生 (通过多对多关联表过滤)
    if clinic_id:
        doc_result = await db.execute(
            select(Doctor)
            .join(doctor_clinics, Doctor.id == doctor_clinics.c.doctor_id)
            .where(doctor_clinics.c.clinic_id == clinic_id, Doctor.is_active == True)
            .order_by(Doctor.id)
        )
        doctors = list(doc_result.scalars().unique().all())
    else:
        doc_result = await db.execute(
            select(Doctor).where(Doctor.is_active == True).order_by(Doctor.id)
        )
        doctors = list(doc_result.scalars().all())

    # 获取所有模板
    tmpl_query = select(ScheduleTemplate).where(ScheduleTemplate.is_active == True)
    if clinic_id:
        tmpl_query = tmpl_query.where(ScheduleTemplate.clinic_id == clinic_id)
    tmpl_result = await db.execute(tmpl_query)
    templates = list(tmpl_result.scalars().all())

    # 按医生分组模板
    doctor_templates: dict[int, list[ScheduleTemplate]] = {}
    for t in templates:
        doctor_templates.setdefault(t.doctor_id, []).append(t)

    # 构建 HTML
    doctor_cards_html = ""
    # 构建门店 ID->名称 映射
    clinic_map = {c.id: c.name for c in clinics}

    for doc in doctors:
        tpls = doctor_templates.get(doc.id, [])

        # 收集该医生关联的所有门店名 (从多对多关系)
        doc_clinic_names = [c.name for c in doc.clinics] if doc.clinics else []
        # 补充从模板中提取的门店名
        for t in tpls:
            cn = clinic_map.get(t.clinic_id, "")
            if cn and cn not in doc_clinic_names:
                doc_clinic_names.append(cn)

        clinic_label = " / ".join(doc_clinic_names) if doc_clinic_names else "未分配"
        doctor_cards_html += _build_doctor_card(doc, clinic_label, tpls)

    # 门店筛选下拉
    clinic_options = '<option value="">全部门店</option>'
    for c in clinics:
        selected = "selected" if clinic_id and c.id == clinic_id else ""
        clinic_options += f'<option value="{c.id}" {selected}>{c.name}</option>'

    if not doctors:
        doctor_cards_html = '<div class="empty-msg">暂无在职医生数据</div>'

    html = _page_template(clinic_options, doctor_cards_html)
    return HTMLResponse(content=html)


def _build_doctor_card(doctor, clinic_name: str, templates: list) -> str:
    """构建单个医生的排班卡片 HTML"""
    # 构建 7天 x 2时段 网格
    grid = {}
    for t in templates:
        hour = t.start_time.hour if t.start_time else 0
        period = "morning" if hour < 12 else "afternoon"
        grid[(t.weekday, period)] = t

    rows_html = ""
    for wd in range(7):
        morning = grid.get((wd, "morning"))
        afternoon = grid.get((wd, "afternoon"))

        m_class = "cell-on" if morning else "cell-off"
        m_text = f'{morning.start_time.strftime("%H:%M")}-{morning.end_time.strftime("%H:%M")}<br><small>限{morning.max_patients}人</small>' if morning else "休息"

        a_class = "cell-on" if afternoon else "cell-off"
        a_text = f'{afternoon.start_time.strftime("%H:%M")}-{afternoon.end_time.strftime("%H:%M")}<br><small>限{afternoon.max_patients}人</small>' if afternoon else "休息"

        rows_html += f"""
        <tr>
            <td class="day-label">{WEEKDAY_NAMES[wd]}</td>
            <td class="{m_class}">{m_text}</td>
            <td class="{a_class}">{a_text}</td>
        </tr>"""

    has_template = len(templates) > 0
    badge = '<span class="badge badge-ok">已配置</span>' if has_template else '<span class="badge badge-none">未设置模板</span>'

    return f"""
    <div class="doctor-card">
        <div class="card-header">
            <div class="doc-info">
                <span class="doc-name">{doctor.name}</span>
                <span class="doc-expertise">{doctor.expertise}</span>
            </div>
            <div class="doc-meta">
                <span class="clinic-badge">{clinic_name}</span>
                {badge}
            </div>
        </div>
        <table class="schedule-grid">
            <thead>
                <tr>
                    <th style="width:70px"></th>
                    <th>上午</th>
                    <th>下午</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """


def _page_template(clinic_options: str, doctor_cards: str) -> str:
    """完整页面 HTML 模板"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>医生周排班总览 - 管理后台</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary: #4A90D9;
            --primary-light: #E8F1FB;
            --success: #52C41A;
            --success-light: #E6F7E6;
            --gray: #F5F5F5;
            --gray-dark: #999;
            --danger-light: #FFF1F0;
        }}
        body {{
            background: #f0f2f5;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            padding: 0;
            margin: 0;
        }}
        .top-bar {{
            background: white;
            padding: 16px 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .top-bar h1 {{
            font-size: 20px;
            font-weight: 600;
            margin: 0;
            color: #333;
        }}
        .top-bar .controls {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .top-bar select {{
            padding: 6px 12px;
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            font-size: 14px;
            background: white;
        }}
        .top-bar a {{
            color: var(--primary);
            text-decoration: none;
            font-size: 14px;
        }}
        .content {{
            max-width: 1200px;
            margin: 24px auto;
            padding: 0 24px;
        }}
        .doctor-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
            gap: 20px;
        }}
        .doctor-card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 6px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        .card-header {{
            padding: 16px 20px;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .doc-info {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .doc-name {{
            font-size: 17px;
            font-weight: 600;
            color: #333;
        }}
        .doc-expertise {{
            font-size: 12px;
            color: var(--gray-dark);
            margin-left: 4px;
        }}
        .doc-meta {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .clinic-badge {{
            font-size: 11px;
            background: #f5f5f5;
            color: #666;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .badge {{
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .badge-ok {{
            background: var(--success-light);
            color: var(--success);
        }}
        .badge-none {{
            background: var(--danger-light);
            color: #ff4d4f;
        }}
        .schedule-grid {{
            width: 100%;
            border-collapse: collapse;
        }}
        .schedule-grid th {{
            text-align: center;
            padding: 10px 8px;
            font-size: 13px;
            font-weight: 600;
            color: #666;
            background: #fafafa;
            border-bottom: 1px solid #f0f0f0;
        }}
        .schedule-grid td {{
            text-align: center;
            padding: 10px 8px;
            font-size: 13px;
            border-bottom: 1px solid #f5f5f5;
            vertical-align: middle;
        }}
        .day-label {{
            font-weight: 500;
            color: #333;
            background: #fafafa;
            text-align: center !important;
        }}
        .cell-on {{
            background: var(--success-light);
            color: var(--success);
            font-weight: 500;
        }}
        .cell-on small {{
            color: #999;
            font-weight: 400;
        }}
        .cell-off {{
            background: var(--gray);
            color: #ccc;
        }}
        .empty-msg {{
            text-align: center;
            padding: 80px 20px;
            color: #999;
            font-size: 16px;
        }}
        @media (max-width: 480px) {{
            .doctor-cards {{
                grid-template-columns: 1fr;
            }}
            .card-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>医生周排班总览</h1>
        <div class="controls">
            <select id="clinicFilter" onchange="filterClinic()">
                {clinic_options}
            </select>
            <a href="/admin">← 返回管理后台</a>
        </div>
    </div>
    <div class="content">
        <div class="doctor-cards">
            {doctor_cards}
        </div>
    </div>
    <script>
        function filterClinic() {{
            const v = document.getElementById('clinicFilter').value;
            const url = new URL(window.location);
            if (v) {{
                url.searchParams.set('clinic_id', v);
            }} else {{
                url.searchParams.delete('clinic_id');
            }}
            window.location = url;
        }}
    </script>
</body>
</html>"""
