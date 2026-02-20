"""应用配置管理"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置 - 支持 .env 文件和环境变量"""

    # 应用信息
    APP_NAME: str = "门诊挂号系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置 (开发环境使用 SQLite，生产切换 PostgreSQL)
    # SQLite: sqlite+aiosqlite:///./clinic.db
    # PostgreSQL: postgresql+asyncpg://user:pass@host:5432/dbname
    DATABASE_URL: str = "sqlite+aiosqlite:///./clinic.db"

    # API 配置
    API_V1_PREFIX: str = "/api/v1"

    # CORS 配置 (小程序和本地开发)
    CORS_ORIGINS: list[str] = ["*"]

    # 管理后台
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_SECRET_KEY: str = "clinic-admin-secret-key-change-me"

    # 微信小程序
    WX_APPID: str = ""
    WX_SECRET: str = ""

    # JWT 配置
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 168  # 7 天

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    """缓存配置单例"""
    return Settings()
