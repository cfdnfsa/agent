"""调试台接口：直接接收 JSON 对象，不再声明独立入参、出参类。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.response.responses import ERROR_RESPONSES, Result
from app.modules.playground.service import PlaygroundService


router = APIRouter(prefix="/api/playground", tags=["调试台"], responses=ERROR_RESPONSES)


# ---------- 提供调试台服务
def get_playground_service() -> PlaygroundService:
    """提供当前请求的服务，配置缓存入口按需管理自己的短查询会话。"""
    return PlaygroundService()


PlaygroundServiceDependency = Annotated[PlaygroundService, Depends(get_playground_service)]


# ---------- 执行单轮模型问答
@router.post("/chat", summary="模型单轮问答")
def ask_model(request_data: dict[str, Any], playground_service: PlaygroundServiceDependency) -> Result[dict[str, str]]:
    """JSON 使用 model_config_id 和 question；不增加必填、长度或内容校验。"""
    return Result(data=playground_service.ask_model(request_data))
