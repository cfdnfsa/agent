"""应用装配入口：注册模型接口，管理请求日志、公共异常和应用资源释放。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from app.core.errors.exception_handlers import register_exception_handlers
from app.core.app_logging import logger, request_id_context
from app.infrastructure.database.db_connection import db_engine
from app.modules.model_config.router import router as model_config_router


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
    """应用退出时释放连接池；启动时不自动建表或修改数据库。"""
    # yield 之前用于启动准备，服务运行期间停在这里，关闭服务后执行后面的清理。
    yield
    db_engine.dispose()


app = FastAPI(title="AI Agent", lifespan=lifespan)
register_exception_handlers(app)
# 路由文件只声明接口；include_router 把这组接口正式挂到当前应用上。
app.include_router(model_config_router)


@app.middleware("http")
async def log_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """为请求和业务日志关联请求ID，仅记录路径、状态和耗时。"""
    # 每次请求生成独立ID；request_id_token 保存原上下文，方便请求结束时恢复。
    request_id = uuid4().hex
    # state 在当前请求期间保留ID，外层的系统异常处理器也能读取它。
    request.state.request_id = request_id
    request_id_token = request_id_context.set(request_id)
    request_started_at = perf_counter()
    try:
        # call_next 把请求交给后面的接口或异常处理器，await 等待它返回响应。
        response = await call_next(request)
        # 前端拿到这个响应头后，可以提供请求ID帮助定位对应的服务端日志。
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id=%s method=%s path=%s status=%s cost_ms=%.2f",
            request_id, request.method, request.url.path, response.status_code,
            (perf_counter() - request_started_at) * 1000,
        )
        return response
    finally:
        # 无论成功或失败都恢复上下文，避免后续处理误用当前请求ID。
        request_id_context.reset(request_id_token)
