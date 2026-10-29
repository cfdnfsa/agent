"""应用装配入口：注册业务接口，管理请求日志、公共异常和应用资源释放。"""

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
from app.modules.playground.router import router as playground_router
from app.modules.workflow_config.router import router as workflow_config_router
from app.modules.workflow_runtime.router import router as workflow_runtime_router


# ---------- 管理应用生命周期
@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
    """框架传入应用对象；本方法仅在应用退出时释放连接池，不自动建表。"""
    # yield 之前用于启动准备，服务运行期间停在这里，关闭服务后执行后面的清理。
    yield
    db_engine.dispose()


app = FastAPI(title="AI Agent", lifespan=lifespan)
register_exception_handlers(app)
# 路由文件只声明接口；include_router 把这组接口正式挂到当前应用上。
app.include_router(model_config_router)
app.include_router(playground_router)
app.include_router(workflow_config_router)
app.include_router(workflow_runtime_router)


# ---------- 记录请求日志和耗时
@app.middleware("http")
async def log_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """为接口和业务日志关联请求ID。

    Args:
        request: 当前 HTTP 请求，可以读取方法、路径和请求状态。
        call_next: FastAPI 提供的后续处理函数，调用后才能继续执行接口。

    Returns:
        后续处理产生的响应，附加 X-Request-ID 响应头。
    """
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

        logger.info("请求ID=%s 方法=%s 路径=%s 状态码=%s 耗时=%.2f毫秒", request_id, request.method, request.url.path, response.status_code, (perf_counter() - request_started_at) * 1000)

        return response
    finally:
        # 无论成功或失败都恢复上下文，避免后续处理误用当前请求ID。
        request_id_context.reset(request_id_token)
