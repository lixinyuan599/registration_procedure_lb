"""
管理后台 - 基于 sqladmin

提供门店、医生、排班、预约、用户的可视化管理界面。
访问地址: http://127.0.0.1:8000/admin
"""

from sqladmin import Admin, ModelView, BaseView, expose
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import SelectField

from app.models.user import User
from app.models.clinic import Clinic
from app.models.doctor import Doctor
from app.models.schedule import Schedule
from app.models.schedule_template import ScheduleTemplate
from app.models.appointment import Appointment
from app.models.site_config import SiteConfig


# ========== 管理后台认证 (简易密码保护) ==========

class AdminAuth(AuthenticationBackend):
    """
    管理后台登录认证

    默认账号: admin / admin123
    生产环境请通过环境变量 ADMIN_USERNAME / ADMIN_PASSWORD 修改
    """

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # 从配置读取，默认值用于开发
        from app.config import get_settings
        settings = get_settings()
        valid_username = getattr(settings, "ADMIN_USERNAME", "admin")
        valid_password = getattr(settings, "ADMIN_PASSWORD", "admin123")

        if username == valid_username and password == valid_password:
            request.session.update({"authenticated": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("authenticated", False)


# ========== 模型管理视图 ==========

class ClinicAdmin(ModelView, model=Clinic):
    """门店管理"""
    name = "门店"
    name_plural = "门店管理"
    icon = "fa-solid fa-hospital"

    column_list = [
        Clinic.id, Clinic.name, Clinic.address,
        Clinic.phone, Clinic.is_active, Clinic.created_at,
    ]
    column_searchable_list = [Clinic.name, Clinic.address]
    column_sortable_list = [Clinic.id, Clinic.name, Clinic.created_at]
    column_default_sort = ("id", False)

    form_columns = [
        Clinic.name, Clinic.address, Clinic.phone,
        Clinic.description, Clinic.image_url, Clinic.is_active,
    ]

    column_labels = {
        Clinic.id: "ID",
        Clinic.name: "门店名称",
        Clinic.address: "地址",
        Clinic.phone: "电话",
        Clinic.description: "简介",
        Clinic.image_url: "图片URL",
        Clinic.is_active: "营业中",
        Clinic.created_at: "创建时间",
    }


class DoctorAdmin(ModelView, model=Doctor):
    """医生管理"""
    name = "医生"
    name_plural = "医生管理"
    icon = "fa-solid fa-user-doctor"

    column_list = [
        Doctor.id, Doctor.name, Doctor.expertise,
        "clinics", Doctor.is_active,
    ]
    column_searchable_list = [Doctor.name, Doctor.expertise]
    column_sortable_list = [Doctor.id, Doctor.name]
    column_default_sort = ("id", False)

    form_columns = [
        "clinics", "name", "expertise",
        "description", "avatar_url", "is_active",
    ]

    # 使用 ajax_refs 让 sqladmin 渲染为 Select2 控件,
    # 实际搜索由自定义模板 JS 接管 (支持空搜索返回全部门店)
    form_ajax_refs = {
        "clinics": {
            "fields": ("name",),
            "order_by": ("name",),
        },
    }

    column_labels = {
        Doctor.id: "ID",
        Doctor.name: "姓名",
        Doctor.expertise: "擅长领域",
        "clinics": "出诊门店",
        Doctor.description: "简介",
        Doctor.avatar_url: "头像URL",
        Doctor.is_active: "在职",
        Doctor.created_at: "创建时间",
    }


class ScheduleAdmin(ModelView, model=Schedule):
    """排班管理"""
    name = "排班"
    name_plural = "排班管理"
    icon = "fa-solid fa-calendar-days"

    column_list = [
        Schedule.id, Schedule.doctor, Schedule.clinic,
        Schedule.date, Schedule.start_time, Schedule.end_time,
        Schedule.max_patients, Schedule.current_patients, Schedule.status,
    ]
    column_searchable_list = [Schedule.date, Schedule.status]
    column_sortable_list = [Schedule.id, Schedule.date, Schedule.doctor_id]
    column_default_sort = [("date", True), ("start_time", False)]

    form_columns = [
        Schedule.doctor, Schedule.clinic,
        Schedule.date, Schedule.start_time, Schedule.end_time,
        Schedule.max_patients, Schedule.current_patients, Schedule.status,
    ]

    column_labels = {
        Schedule.id: "ID",
        Schedule.doctor: "医生",
        Schedule.clinic: "门店",
        Schedule.date: "日期",
        Schedule.start_time: "开始时间",
        Schedule.end_time: "结束时间",
        Schedule.max_patients: "最大接诊数",
        Schedule.current_patients: "已预约数",
        Schedule.status: "状态",
    }


class AppointmentAdmin(ModelView, model=Appointment):
    """预约管理"""
    name = "预约"
    name_plural = "预约管理"
    icon = "fa-solid fa-bookmark"

    column_list = [
        Appointment.id, Appointment.user, Appointment.doctor,
        Appointment.clinic, Appointment.appointment_date,
        Appointment.time_slot, Appointment.status,
    ]
    column_searchable_list = [Appointment.status, Appointment.appointment_date]
    column_sortable_list = [Appointment.id, Appointment.appointment_date, Appointment.status]
    column_default_sort = ("id", True)

    form_columns = [
        Appointment.user, Appointment.doctor, Appointment.clinic,
        Appointment.schedule, Appointment.appointment_date,
        Appointment.time_slot, Appointment.status, Appointment.notes,
    ]

    column_labels = {
        Appointment.id: "ID",
        Appointment.user: "用户",
        Appointment.doctor: "医生",
        Appointment.clinic: "门店",
        Appointment.appointment_date: "预约日期",
        Appointment.time_slot: "时段",
        Appointment.status: "状态",
        Appointment.notes: "备注",
        Appointment.created_at: "创建时间",
    }


class ScheduleTemplateAdmin(ModelView, model=ScheduleTemplate):
    """排班模板管理"""
    name = "排班模板"
    name_plural = "排班模板管理"
    icon = "fa-solid fa-clock-rotate-left"

    column_list = [
        ScheduleTemplate.id, ScheduleTemplate.doctor,
        ScheduleTemplate.clinic, ScheduleTemplate.weekday,
        ScheduleTemplate.start_time, ScheduleTemplate.end_time,
        ScheduleTemplate.max_patients, ScheduleTemplate.is_active,
    ]
    column_sortable_list = [
        ScheduleTemplate.id, ScheduleTemplate.doctor_id,
        ScheduleTemplate.weekday,
    ]
    column_default_sort = [("doctor_id", False), ("weekday", False)]

    form_columns = [
        ScheduleTemplate.doctor, ScheduleTemplate.clinic,
        ScheduleTemplate.weekday, ScheduleTemplate.start_time,
        ScheduleTemplate.end_time, ScheduleTemplate.max_patients,
        ScheduleTemplate.is_active,
    ]

    column_labels = {
        ScheduleTemplate.id: "ID",
        ScheduleTemplate.doctor: "医生",
        ScheduleTemplate.clinic: "门店",
        ScheduleTemplate.weekday: "星期几 (0=周一)",
        ScheduleTemplate.start_time: "开始时间",
        ScheduleTemplate.end_time: "结束时间",
        ScheduleTemplate.max_patients: "最大接诊数",
        ScheduleTemplate.is_active: "启用",
    }


class UserAdmin(ModelView, model=User):
    """用户管理"""
    name = "用户"
    name_plural = "用户管理"
    icon = "fa-solid fa-users"

    column_list = [
        User.id, User.openid, User.nickname,
        User.phone, User.role, User.doctor, User.created_at,
    ]
    column_searchable_list = [User.openid, User.nickname, User.phone]
    column_sortable_list = [User.id, User.role, User.created_at]
    column_default_sort = ("id", True)

    can_create = False
    can_edit = True

    form_columns = [
        User.nickname, User.phone, User.avatar_url,
        User.role, User.doctor,
    ]

    form_args = {
        "role": {
            "choices": [
                ("patient", "患者"),
                ("doctor", "医生"),
                ("admin", "管理员"),
            ],
        },
    }

    form_overrides = {
        "role": SelectField,
    }

    column_labels = {
        User.id: "ID",
        User.openid: "OpenID",
        User.nickname: "昵称",
        User.phone: "手机号",
        User.avatar_url: "头像",
        User.role: "角色",
        User.doctor: "关联医生",
        User.doctor_id: "关联医生ID",
        User.created_at: "注册时间",
    }


class SiteConfigAdmin(ModelView, model=SiteConfig):
    """系统配置"""
    name = "显示配置"
    name_plural = "显示配置"
    icon = "fa-solid fa-gear"

    column_list = [
        SiteConfig.id,
        SiteConfig.show_remaining_slots,
        SiteConfig.clinic_name,
        SiteConfig.updated_at,
    ]

    can_create = True
    can_delete = False

    form_columns = [
        SiteConfig.show_remaining_slots,
        SiteConfig.clinic_name,
    ]

    column_labels = {
        SiteConfig.id: "ID",
        SiteConfig.show_remaining_slots: "显示余号",
        SiteConfig.clinic_name: "系统名称",
        SiteConfig.updated_at: "更新时间",
    }


class WeeklyScheduleLink(BaseView):
    """周排班总览 - 跳转到可视化排班页"""
    name = "周排班总览"
    icon = "fa-solid fa-table-cells-large"

    @expose("/weekly-overview", methods=["GET"])
    async def weekly_overview(self, request: Request):
        return RedirectResponse(url="/dashboard/weekly-schedule")


def setup_admin(app, engine) -> Admin:
    """初始化管理后台并注册到 FastAPI"""
    authentication_backend = AdminAuth(secret_key="clinic-admin-secret-key-change-me")

    admin = Admin(
        app,
        engine,
        title="门诊挂号 · 管理后台",
        authentication_backend=authentication_backend,
        templates_dir="templates",
    )

    admin.add_view(SiteConfigAdmin)
    admin.add_view(ClinicAdmin)
    admin.add_view(DoctorAdmin)
    admin.add_view(WeeklyScheduleLink)
    admin.add_view(ScheduleTemplateAdmin)
    admin.add_view(ScheduleAdmin)
    admin.add_view(AppointmentAdmin)
    admin.add_view(UserAdmin)

    return admin
