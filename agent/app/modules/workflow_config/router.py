"""流程配置接口：接收普通 JSON 字典，注入业务服务，使用公共 Result 返回。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.core.response.responses import ERROR_RESPONSES, Page, Result
from app.infrastructure.database.db_connection import DbSession
from app.modules.workflow_config.service import WorkflowConfigService


router = APIRouter(prefix="/api/workflow-configs", tags=["流程配置"], responses=ERROR_RESPONSES)


# ---------- 提供流程配置服务
def get_workflow_config_service(db_session: DbSession) -> WorkflowConfigService:
    """把当前请求的 db_session 传给流程服务，避免每个接口重复创建。"""
    return WorkflowConfigService(db_session)


WorkflowConfigServiceDependency = Annotated[WorkflowConfigService, Depends(get_workflow_config_service)]


# ---------- 新增流程配置接口
@router.post("", status_code=status.HTTP_201_CREATED, summary="新增流程配置")
def create_workflow(
    request_data: dict[str, Any], workflow_config_service: WorkflowConfigServiceDependency,
) -> Result[dict[str, Any]]:
    """request_data 使用 workflow_name、workflow_definition，定义字段提交字符串。"""
    return Result(data=workflow_config_service.create(request_data).to_dict())


# ---------- 分页查询流程配置接口
@router.get("", summary="分页查询流程配置")
def list_workflows(
    workflow_config_service: WorkflowConfigServiceDependency, page: int = 1, page_size: int = 20,
) -> Result[Page[dict[str, Any]]]:
    """page、page_size 来自 URL 查询参数，返回 ID、名称和分页信息，不加载定义文本。"""
    return Result(data=workflow_config_service.list_page(page, page_size))


# ---------- 查询流程配置详情接口
@router.get("/{workflow_id}", summary="查询流程配置详情")
def get_workflow(
    workflow_id: int, workflow_config_service: WorkflowConfigServiceDependency,
) -> Result[dict[str, Any]]:
    """workflow_id 来自路径，返回实体三个字段，定义内容保持字符串。"""
    return Result(data=workflow_config_service.get_detail(workflow_id).to_dict())


# ---------- 修改流程配置接口
@router.put("/{workflow_id}", summary="修改流程配置")
def update_workflow(
    workflow_id: int, request_data: dict[str, Any], workflow_config_service: WorkflowConfigServiceDependency,
) -> Result[dict[str, Any]]:
    """按 workflow_id 更新 request_data 中实际提交的字段，不要求重新提交全部字段。"""
    return Result(data=workflow_config_service.update(workflow_id, request_data).to_dict())


# ---------- 删除流程配置接口
@router.delete("/{workflow_id}", summary="删除流程配置")
def delete_workflow(
    workflow_id: int, workflow_config_service: WorkflowConfigServiceDependency,
) -> Result[None]:
    """workflow_id 是待删除记录主键，成功返回 data=null，记录不存在返回 404。"""
    workflow_config_service.delete(workflow_id)
    return Result()
