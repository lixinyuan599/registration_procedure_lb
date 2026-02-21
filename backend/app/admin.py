"""
管理后台 - 基于 sqladmin (多租户版)

权限模型:
- super_admin: 看到所有企业的所有数据, 管理企业和管理员账号
- tenant_admin: 只看到/编辑自己企业的数据
"""

from typing import Any

from sqlalchemy import select, func as sa_func
from sqladmin import Admin, ModelView, BaseView, expose
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import SelectField, StringField

from app.models.tenant import Tenant
from app.models.admin_user import AdminUser
from app.models.user import User
from app.models.clinic import Clinic
from app.models.doctor import Doctor
from app.models.schedule import Schedule
from app.models.schedule_template import ScheduleTemplate
from app.models.appointment import Appointment
from app.models.site_config import SiteConfig

from app.utils.tenant_context import get_tenant_filter_id, is_super_admin


# ========== 管理后台认证 (数据库多账号) ==========

class AdminAuth(AuthenticationBackend):
    """管理后台登录认证 - 从 admin_users 表验证, 支持多租户"""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == username)
            )
            admin_user = result.scalar_one_or_none()

        if admin_user is None:
            from app.config import get_settings
            settings = get_settings()
            if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
                request.session.update({
                    "authenticated": True,
                    "admin_id": 0,
                    "admin_role": "super_admin",
                    "tenant_id": None,
                    "admin_name": "超级管理员",
                })
                return True
            return False

        if not admin_user.is_active:
            return False
        if not admin_user.verify_password(password):
            return False

        if admin_user.tenant_id and admin_user.tenant:
            if admin_user.tenant.status != "approved":
                return False

        request.session.update({
            "authenticated": True,
            "admin_id": admin_user.id,
            "admin_role": admin_user.role,
            "tenant_id": admin_user.tenant_id,
            "admin_name": str(admin_user),
        })
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("authenticated", False)


# ========== 权限辅助 ==========

def _is_super(request: Request) -> bool:
    return request.session.get("admin_role") == "super_admin"


# ========== 租户过滤基类 ==========

class TenantModelView(ModelView):
    """带租户数据隔离的 ModelView 基类"""

    @property
    def list_query(self):
        stmt = select(self.model)
        tid = get_tenant_filter_id()
        if tid is not None and hasattr(self.model, "tenant_id"):
            stmt = stmt.where(self.model.tenant_id == tid)
        return stmt

    @property
    def count_query(self):
        stmt = select(sa_func.count()).select_from(self.model)
        tid = get_tenant_filter_id()
        if tid is not None and hasattr(self.model, "tenant_id"):
            stmt = stmt.where(self.model.tenant_id == tid)
        return stmt

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        """创建记录时自动设置 tenant_id"""
        if is_created and hasattr(model, "tenant_id"):
            tid = request.session.get("tenant_id")
            if tid is not None:
                model.tenant_id = tid


# ========== 超级管理员专用视图 ==========

class TenantAdmin(ModelView, model=Tenant):
    """企业/组织管理 (超级管理员专用)"""
    name = "企业"
    name_plural = "企业管理"
    icon = "fa-solid fa-building"

    def is_accessible(self, request: Request) -> bool:
        return _is_super(request)

    def is_visible(self, request: Request) -> bool:
        return _is_super(request)

    column_list = [
        Tenant.id, Tenant.name, Tenant.contact_name,
        Tenant.contact_phone, Tenant.status, Tenant.created_at,
    ]
    column_searchable_list = [Tenant.name, Tenant.contact_name]
    column_sortable_list = [Tenant.id, Tenant.name, Tenant.status, Tenant.created_at]
    column_default_sort = ("id", True)

    form_columns = [
        "name", "contact_name", "contact_phone",
        "description", "logo_url", "status",
    ]

    form_overrides = {"status": SelectField}
    form_args = {
        "status": {
            "choices": [
                ("pending", "待审核"),
                ("approved", "已通过"),
                ("rejected", "已拒绝"),
            ],
        },
    }

    column_labels = {
        Tenant.id: "ID",
        Tenant.name: "企业名称",
        Tenant.contact_name: "联系人",
        Tenant.contact_phone: "联系电话",
        Tenant.description: "简介",
        Tenant.logo_url: "Logo",
        Tenant.status: "状态",
        Tenant.created_at: "创建时间",
    }


class AdminUserAdmin(ModelView, model=AdminUser):
    """管理员账号管理 (超级管理员专用)"""
    name = "管理员"
    name_plural = "管理员账号"
    icon = "fa-solid fa-user-shield"

    def is_accessible(self, request: Request) -> bool:
        return _is_super(request)

    def is_visible(self, request: Request) -> bool:
        return _is_super(request)

    column_list = [
        AdminUser.id, AdminUser.username, AdminUser.display_name,
        AdminUser.tenant, AdminUser.role, AdminUser.is_active, AdminUser.created_at,
    ]
    column_searchable_list = [AdminUser.username, AdminUser.display_name]
    column_sortable_list = [AdminUser.id, AdminUser.username, AdminUser.role]
    column_default_sort = ("id", True)

    form_columns = [
        "username", "password_hash", "display_name",
        "tenant", "role", "is_active",
    ]

    form_overrides = {
        "password_hash": StringField,
        "role": SelectField,
    }
    form_args = {
        "password_hash": {"label": "密码 (新建必填, 编辑时留空则不修改)"},
        "role": {
            "choices": [
                ("super_admin", "超级管理员"),
                ("tenant_admin", "企业管理员"),
            ],
        },
    }

    column_labels = {
        AdminUser.id: "ID",
        AdminUser.username: "登录账号",
        AdminUser.display_name: "显示名称",
        AdminUser.password_hash: "密码",
        AdminUser.tenant: "所属企业",
        AdminUser.role: "角色",
        AdminUser.is_active: "启用",
        AdminUser.created_at: "创建时间",
    }

    column_details_exclude_list = [AdminUser.password_hash]

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        pw = data.get("password_hash", "")
        if pw and ":" not in pw:
            model.set_password(pw)
        elif not is_created and not pw:
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AdminUser.password_hash).where(AdminUser.id == model.id)
                )
                original = result.scalar_one_or_none()
                if original:
                    model.password_hash = original


# ========== 业务数据视图 (租户隔离) ==========

class ClinicAdmin(TenantModelView, model=Clinic):
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


class DoctorAdmin(TenantModelView, model=Doctor):
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


class ScheduleAdmin(TenantModelView, model=Schedule):
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


class AppointmentAdmin(TenantModelView, model=Appointment):
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


class ScheduleTemplateAdmin(TenantModelView, model=ScheduleTemplate):
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
    """用户管理 (超级管理员专用)"""
    name = "用户"
    name_plural = "用户管理"
    icon = "fa-solid fa-users"

    def is_accessible(self, request: Request) -> bool:
        return _is_super(request)

    def is_visible(self, request: Request) -> bool:
        return _is_super(request)

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
    """系统配置 (超级管理员专用)"""
    name = "显示配置"
    name_plural = "显示配置"
    icon = "fa-solid fa-gear"

    def is_accessible(self, request: Request) -> bool:
        return _is_super(request)

    def is_visible(self, request: Request) -> bool:
        return _is_super(request)

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


# ========== 初始化入口 ==========

def setup_admin(app, engine) -> Admin:
    """初始化管理后台并注册到 FastAPI"""
    from app.config import get_settings
    settings = get_settings()

    authentication_backend = AdminAuth(
        secret_key=settings.ADMIN_SECRET_KEY,
    )

    admin = Admin(
        app,
        engine,
        title="门诊挂号 · 管理后台",
        authentication_backend=authentication_backend,
        templates_dir="templates",
    )

    # 超级管理员专用
    admin.add_view(TenantAdmin)
    admin.add_view(AdminUserAdmin)

    # 业务数据 (租户隔离)
    admin.add_view(ClinicAdmin)
    admin.add_view(DoctorAdmin)
    admin.add_view(WeeklyScheduleLink)
    admin.add_view(ScheduleTemplateAdmin)
    admin.add_view(ScheduleAdmin)
    admin.add_view(AppointmentAdmin)

    # 超级管理员专用
    admin.add_view(SiteConfigAdmin)
    admin.add_view(UserAdmin)

    return admin
