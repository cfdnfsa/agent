"""流程运行接口：注入运行服务，沿用现有 URL 和公共 Result 返回结构。"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.response.responses import ERROR_RESPONSES, Result
from app.infrastructure.database.db_connection import DbSession
from app.modules.workflow_nodes.base.data.workflow_input import WorkflowInput
from app.modules.workflow_runtime.data.workflow_result import WorkflowResult
from app.modules.workflow_runtime.service import WorkflowRuntimeService

# URL 沿用原地址，业务职责通过独立模块和接口文档分组区分。
router = APIRouter(prefix="/api/workflow-configs", tags=["流程运行"], responses=ERROR_RESPONSES)


# ---------- 提供流程运行服务
def get_workflow_runtime_service(db_session: DbSession) -> WorkflowRuntimeService:
    """将当前请求的数据库会话传给运行服务，由加载器读取所需配置。"""
    return WorkflowRuntimeService(db_session)


WorkflowRuntimeServiceDependency = Annotated[WorkflowRuntimeService, Depends(get_workflow_runtime_service)]


# ---------- 运行流程接口
@router.post("/{workflow_id}/run", summary="运行流程")
def run_workflow_config(
        workflow_id: int,
        workflow_input: WorkflowInput,
        workflow_runtime_service: WorkflowRuntimeServiceDependency,
) -> Result[WorkflowResult]:
    """接收固定输入对象，返回唯一返回节点的数据；异常由公共处理器记录与返回。

    Args:
        workflow_id: 要运行的流程配置ID。
        workflow_input: FastAPI 按 JSON 中的 text、user_id 解析；user_id 不传时为 None。
        workflow_runtime_service: 当前请求注入的流程运行服务。

    Returns:
        统一响应，data.payload 是返回节点产生的文字、对象或列表。
    """
    # 框架完成基础字段解析后，直接把同一个输入对象交给 Service，不手工转换字典。
    return Result(
        data=workflow_runtime_service.run(workflow_id, workflow_input)
    )
