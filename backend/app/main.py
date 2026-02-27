"""FastAPI 应用入口"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.database import engine, init_db
from app.routers import clinic, doctor, schedule, schedule_template, appointment, auth, site_config, user, tenant
from app.admin import setup_admin
from app.views.weekly_schedule import router as weekly_schedule_router
from app.utils.exceptions import AppException, app_exception_handler, general_exception_handler
from app.utils.tenant_context import TenantMiddleware, get_tenant_filter_id

settings = get_settings()


async def _ensure_super_admin():
    """确保至少有一个超级管理员账号（首次启动时从环境变量创建）"""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.admin_user import AdminUser

    async with AsyncSessionLocal() as session:
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
            print(f"  已创建超级管理员: {settings.ADMIN_USERNAME}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    await _ensure_super_admin()
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION} 启动成功")
    print(f"  API 文档: http://127.0.0.1:8000/docs")
    print(f"  管理后台: http://127.0.0.1:8000/admin")
    yield
    print("  应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="门诊挂号系统 MVP - RESTful API",
    lifespan=lifespan,
)

setup_admin(app, engine)

app.add_middleware(TenantMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(clinic.router, prefix=settings.API_V1_PREFIX)
app.include_router(doctor.router, prefix=settings.API_V1_PREFIX)
app.include_router(doctor.doctor_router, prefix=settings.API_V1_PREFIX)
app.include_router(schedule.router, prefix=settings.API_V1_PREFIX)
app.include_router(schedule_template.router, prefix=settings.API_V1_PREFIX)
app.include_router(appointment.router, prefix=settings.API_V1_PREFIX)
app.include_router(site_config.router, prefix=settings.API_V1_PREFIX)
app.include_router(user.router, prefix=settings.API_V1_PREFIX)
app.include_router(tenant.router, prefix=settings.API_V1_PREFIX)

app.include_router(weekly_schedule_router)

# 静态文件: 上传的图片
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@app.post("/internal/upload", include_in_schema=False)
async def upload_image(file: UploadFile = File(...)):
    """管理后台用: 图片上传接口"""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"error": f"不支持的文件格式, 仅支持: {', '.join(ALLOWED_EXTENSIONS)}"}

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return {"error": "文件大小不能超过 5MB"}

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(content)

    return {"url": f"/uploads/{filename}"}


@app.get("/internal/clinics", include_in_schema=False)
async def admin_clinics_search(term: str = "", name: str = ""):
    """管理后台用: 门店搜索 (按租户过滤)"""
    from sqlalchemy import select, cast, String
    from app.database import AsyncSessionLocal
    from app.models.clinic import Clinic

    async with AsyncSessionLocal() as session:
        query = select(Clinic).order_by(Clinic.name)
        tid = get_tenant_filter_id()
        if tid is not None:
            query = query.where(Clinic.tenant_id == tid)
        if term and term.strip():
            query = query.where(
                cast(Clinic.name, String).ilike(f"%{term.strip()}%")
            )
        result = await session.execute(query)
        clinics = result.scalars().all()
        return {
            "results": [{"id": str(c.id), "text": c.name} for c in clinics]
        }


# ========== 企业自助注册 ==========

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>企业入驻申请</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, "Segoe UI", sans-serif; background: #f4f6f9; display: flex; justify-content: center; padding-top: 60px; min-height: 100vh; }
    .card { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); padding: 40px 36px; width: 420px; }
    h2 { text-align: center; margin-bottom: 24px; color: #333; font-size: 22px; }
    label { display: block; margin-bottom: 4px; color: #555; font-size: 14px; font-weight: 500; }
    input { width: 100%; padding: 10px 12px; border: 1px solid #d0d5dd; border-radius: 6px; font-size: 15px; margin-bottom: 16px; transition: border-color .2s; }
    input:focus { outline: none; border-color: #0d6efd; }
    .btn { width: 100%; padding: 12px; background: #0d6efd; color: #fff; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; transition: background .2s; }
    .btn:hover { background: #0b5ed7; }
    .msg { text-align: center; margin-top: 16px; font-size: 14px; }
    .msg.ok { color: #198754; }
    .msg.err { color: #dc3545; }
    .login-link { text-align: center; margin-top: 12px; font-size: 13px; }
    .login-link a { color: #0d6efd; text-decoration: none; }
  </style>
</head>
<body>
  <div class="card">
    <h2>企业入驻申请</h2>
    <form id="regForm">
      <label>企业名称 *</label>
      <input name="tenant_name" required placeholder="如：华草堂中医馆">
      <label>联系人 *</label>
      <input name="contact_name" required placeholder="姓名">
      <label>联系电话 *</label>
      <input name="contact_phone" required placeholder="手机号">
      <label>管理员账号 *</label>
      <input name="username" required placeholder="登录用的账号名">
      <label>管理员密码 *</label>
      <input name="password" type="password" required placeholder="至少 6 位">
      <button type="submit" class="btn">提交申请</button>
    </form>
    <div class="msg" id="msg"></div>
    <div class="login-link">已有账号？<a href="/admin">去登录</a></div>
  </div>
  <script>
    document.getElementById('regForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      var fd = new FormData(this);
      var msg = document.getElementById('msg');
      msg.textContent = '提交中...';
      msg.className = 'msg';
      try {
        var res = await fetch('/internal/register', { method: 'POST', body: fd });
        var data = await res.json();
        if (data.ok) {
          msg.textContent = data.message;
          msg.className = 'msg ok';
          this.reset();
        } else {
          msg.textContent = data.message;
          msg.className = 'msg err';
        }
      } catch (err) {
        msg.textContent = '网络错误，请重试';
        msg.className = 'msg err';
      }
    });
  </script>
</body>
</html>
"""


@app.get("/register", include_in_schema=False)
async def register_page():
    """企业自助注册页面"""
    return HTMLResponse(REGISTER_HTML)


@app.post("/internal/register", include_in_schema=False)
async def register_tenant(
    tenant_name: str = Form(...),
    contact_name: str = Form(...),
    contact_phone: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
):
    """企业自助注册接口"""
    if len(password) < 6:
        return {"ok": False, "message": "密码长度至少 6 位"}

    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.tenant import Tenant
    from app.models.admin_user import AdminUser

    async with AsyncSessionLocal() as session:
        dup_tenant = await session.execute(
            select(Tenant).where(Tenant.name == tenant_name).limit(1)
        )
        if dup_tenant.scalar_one_or_none():
            return {"ok": False, "message": "该企业名称已被注册"}

        dup_user = await session.execute(
            select(AdminUser).where(AdminUser.username == username).limit(1)
        )
        if dup_user.scalar_one_or_none():
            return {"ok": False, "message": "该账号名已被占用"}

        tenant = Tenant(
            name=tenant_name,
            contact_name=contact_name,
            contact_phone=contact_phone,
            status="pending",
        )
        session.add(tenant)
        await session.flush()

        admin_user = AdminUser(
            username=username,
            display_name=contact_name,
            tenant_id=tenant.id,
            role="tenant_admin",
            is_active=True,
        )
        admin_user.set_password(password)
        session.add(admin_user)
        await session.commit()

    return {"ok": True, "message": "申请已提交，请等待超级管理员审核通过后即可登录"}


@app.get("/", tags=["健康检查"])
async def health_check():
    """服务健康检查"""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        },
    }
