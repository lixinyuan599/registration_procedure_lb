"""自定义异常与统一错误处理"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """业务异常基类"""

    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


class NotFoundException(AppException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=40001, message=message, status_code=404)


class ScheduleFullException(AppException):
    """排班已满"""

    def __init__(self, message: str = "该时段已约满"):
        super().__init__(code=40002, message=message, status_code=400)


class ScheduleClosedException(AppException):
    """排班已关闭"""

    def __init__(self, message: str = "排班不存在或已关闭"):
        super().__init__(code=40003, message=message, status_code=400)


class DuplicateAppointmentException(AppException):
    """重复预约"""

    def __init__(self, message: str = "您已预约该时段，请勿重复预约"):
        super().__init__(code=40004, message=message, status_code=400)


class UnauthorizedException(AppException):
    """未认证"""

    def __init__(self, message: str = "用户未认证"):
        super().__init__(code=40101, message=message, status_code=401)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """业务异常统一处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """未捕获异常兜底处理"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 50001,
            "message": "服务器内部错误",
            "data": None,
        },
    )
