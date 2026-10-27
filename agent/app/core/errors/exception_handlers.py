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


# ---------- 构造统一错误响应
def build_error_response(
    request: Request,
    status_code: int,
    message: str,
    data: Any = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """构造公共错误响应，所有异常处理器共用这个普通函数。

    Args:
        request: 当前 HTTP 请求，用来取得请求ID。
        status_code: 本次失败对应的 HTTP 状态码，同时作为统一结果的 code。
        message: 可以显示在页面上的错误说明。
        data: 可选错误详情，例如参数校验列表；默认返回 null。
        headers: 上游处理器需要保留的响应头，例如 405 的 Allow。

    Returns:
        带统一 JSON 结构和请求ID响应头的 HTTP 响应。
    """
    error_result = Result[Any](code=status_code, message=message, data=data)
    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = getattr(request.state, "request_id", "-")
    return JSONResponse(
        status_code=status_code,
        content=error_result.model_dump(mode="json"),
        headers=response_headers,
    )


# ---------- 处理业务异常
async def business_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """返回业务主动给出的公开说明，例如模型配置不存在。"""
    # 框架回调要求接收 Exception；明确判断后，类型检查器才能安全读取业务异常字段。
    if not isinstance(exception, BusinessError):
        raise exception
    return build_error_response(request, exception.status_code, exception.message)


# ---------- 处理请求参数解析异常
async def validation_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """返回字段校验原因，不回显原始输入，避免 API Key 等信息泄露。"""
    if not isinstance(exception, RequestValidationError):
        raise exception
    # type 是错误类型，loc 是字段位置，msg 是原因；不用原始 input，避免回显密钥。
    validation_errors = [
        {"type": field_error["type"], "loc": field_error["loc"], "msg": field_error["msg"]}
        for field_error in exception.errors()
    ]
    return build_error_response(request, HTTPStatus.UNPROCESSABLE_ENTITY, "参数校验失败", validation_errors)


# ---------- 处理 HTTP 异常
async def http_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """将找不到路由、请求方法不支持等 HTTP 错误转换为统一结构。"""
    if not isinstance(exception, HTTPException):
        raise exception
    error_message = exception.detail if isinstance(exception.detail, str) else "请求处理失败"
    error_details = None if isinstance(exception.detail, str) else exception.detail
    # 保留框架生成的响应头，例如 405 响应中的 Allow。
    return build_error_response(request, exception.status_code, error_message, error_details, exception.headers)


# ---------- 处理数据库异常
async def database_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """记录数据库异常堆栈，客户端只返回通用说明。"""

    logger.error("请求ID=%s 路径=%s 数据库操作失败", getattr(request.state, "request_id", "-"), request.url.path, exc_info=(type(exception), exception, exception.__traceback__))

    return build_error_response(
        request, HTTPStatus.INTERNAL_SERVER_ERROR, "数据库操作失败，请检查提交的数据或数据库状态"
    )


# ---------- 处理未预期异常
async def unexpected_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """未预期异常也返回统一结果，不把内部堆栈作为响应发送给客户端。"""

    logger.error("请求ID=%s 方法=%s 路径=%s 请求处理异常", getattr(request.state, "request_id", "-"), request.method, request.url.path, exc_info=(type(exception), exception, exception.__traceback__))

    return build_error_response(request, HTTPStatus.INTERNAL_SERVER_ERROR, "服务器内部错误")


# ---------- 注册公共异常处理器
def register_exception_handlers(application: FastAPI) -> None:
    """application 是 main.py 创建的 FastAPI 应用；向它注册处理器，无返回值。"""
    # 处理器的 request 和 exception 参数由框架提供，分别代表当前请求和捕获到的异常。
    application.add_exception_handler(BusinessError, business_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(SQLAlchemyError, database_error_handler)
    application.add_exception_handler(Exception, unexpected_error_handler)
