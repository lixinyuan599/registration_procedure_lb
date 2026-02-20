"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, init_db
from app.routers import clinic, doctor, schedule, schedule_template, appointment, auth, site_config
from app.admin import setup_admin
from app.views.weekly_schedule import router as weekly_schedule_router
from app.utils.exceptions import AppException, app_exception_handler, general_exception_handler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：初始化数据库
    await init_db()
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} 启动成功")
    print(f"📖 API 文档: http://127.0.0.1:8000/docs")
    print(f"🔧 管理后台: http://127.0.0.1:8000/admin")
    yield
    # 关闭时：清理资源
    print("👋 应用关闭")


# 创建 FastAPI 实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="门诊挂号系统 MVP - RESTful API",
    lifespan=lifespan,
)

# 注册管理后台 (必须在 CORS 之前)
setup_admin(app, engine)

# CORS 中间件 (允许小程序跨域访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册统一异常处理
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由 (统一 /api/v1 前缀)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(clinic.router, prefix=settings.API_V1_PREFIX)
app.include_router(doctor.router, prefix=settings.API_V1_PREFIX)
app.include_router(doctor.doctor_router, prefix=settings.API_V1_PREFIX)
app.include_router(schedule.router, prefix=settings.API_V1_PREFIX)
app.include_router(schedule_template.router, prefix=settings.API_V1_PREFIX)
app.include_router(appointment.router, prefix=settings.API_V1_PREFIX)
app.include_router(site_config.router, prefix=settings.API_V1_PREFIX)

# 管理后台扩展页面 (HTML 视图, 无前缀)
app.include_router(weekly_schedule_router)


@app.get("/internal/clinics", include_in_schema=False)
async def admin_clinics_search(term: str = "", name: str = ""):
    """管理后台用: 门店搜索接口, 支持空搜索返回全部 (Select2 格式)"""
    from sqlalchemy import select, cast, String
    from app.database import AsyncSessionLocal
    from app.models.clinic import Clinic

    async with AsyncSessionLocal() as session:
        query = select(Clinic).order_by(Clinic.name)
        if term and term.strip():
            query = query.where(
                cast(Clinic.name, String).ilike(f"%{term.strip()}%")
            )
        result = await session.execute(query)
        clinics = result.scalars().all()
        return {
            "results": [{"id": str(c.id), "text": c.name} for c in clinics]
        }


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
