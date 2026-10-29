"""流程运行接口：注入运行服务，沿用现有 URL 和公共 Result 返回结构。"""

from typing import Annotated, Any

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
        request_data: dict[str, Any],
        workflow_runtime_service: WorkflowRuntimeServiceDependency,
) -> Result[WorkflowResult]:
    """JSON 提交本次 payload，返回唯一返回节点的数据；异常交给公共处理器并记录后端日志。"""
    # HTTP 边界读取当前协议的 payload，内部统一传明确的输入对象。
    workflow_input = WorkflowInput(request_data["payload"])

    return Result(
        data=workflow_runtime_service.run(workflow_id, workflow_input)
    )
