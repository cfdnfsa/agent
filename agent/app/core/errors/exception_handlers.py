"""公共异常处理：保留 HTTP 状态码，统一错误 JSON，并隐藏内部异常细节。"""

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.core.errors.exceptions import BusinessError
from app.core.app_logging import logger
from app.core.response.responses import Result


def _error_response(
    request: Request,
    status_code: int,
    message: str,
    data: Any = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """构造统一错误结果；系统异常经过外层处理时，也保留请求ID响应头。"""
    error_result = Result[Any](code=status_code, message=message, data=data)
    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = getattr(request.state, "request_id", "-")
    return JSONResponse(
        status_code=status_code,
        content=error_result.model_dump(mode="json"),
        headers=response_headers,
    )


async def business_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """返回业务主动给出的公开说明，例如模型配置不存在。"""
    # 框架回调要求接收 Exception；明确判断后，类型检查器才能安全读取业务异常字段。
    if not isinstance(exception, BusinessError):
        raise exception
    return _error_response(request, exception.status_code, exception.message)


async def validation_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """返回字段校验原因，不回显原始输入，避免 API Key 等信息泄露。"""
    if not isinstance(exception, RequestValidationError):
        raise exception
    validation_errors = [
        {"type": field_error["type"], "loc": field_error["loc"], "msg": field_error["msg"]}
        for field_error in exception.errors()
    ]
    return _error_response(request, HTTPStatus.UNPROCESSABLE_ENTITY, "参数校验失败", validation_errors)


async def http_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """将找不到路由、请求方法不支持等 HTTP 错误转换为统一结构。"""
    if not isinstance(exception, HTTPException):
        raise exception
    error_message = exception.detail if isinstance(exception.detail, str) else "请求处理失败"
    error_details = None if isinstance(exception.detail, str) else exception.detail
    # 保留框架生成的响应头，例如 405 响应中的 Allow。
    return _error_response(request, exception.status_code, error_message, error_details, exception.headers)


async def database_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """记录数据库异常堆栈，客户端只返回通用说明。"""
    logger.error(
        "request_id=%s path=%s 数据库操作失败",
        getattr(request.state, "request_id", "-"), request.url.path,
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    return _error_response(
        request, HTTPStatus.INTERNAL_SERVER_ERROR, "数据库操作失败，请检查数据库连接和表结构"
    )


async def unexpected_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """未预期异常也返回统一结果，不把内部堆栈作为响应发送给客户端。"""
    logger.error(
        "request_id=%s method=%s path=%s 请求处理异常",
        getattr(request.state, "request_id", "-"), request.method, request.url.path,
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    return _error_response(request, HTTPStatus.INTERNAL_SERVER_ERROR, "服务器内部错误")


def register_exception_handlers(application: FastAPI) -> None:
    """启动时统一注册异常处理器，业务模块无需各自注册同类处理逻辑。"""
    application.add_exception_handler(BusinessError, business_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(SQLAlchemyError, database_error_handler)
    application.add_exception_handler(Exception, unexpected_error_handler)
