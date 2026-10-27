"""模型配置接口：直接接收 JSON，不增加字段、长度、格式和范围校验。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.core.response.responses import ERROR_RESPONSES, Page, Result
from app.infrastructure.database.db_connection import DbSession
from app.modules.model_config.service import ModelConfigService


router = APIRouter(prefix="/api/model-configs", tags=["模型配置"], responses=ERROR_RESPONSES)


# ---------- 提供模型配置服务
def get_model_config_service(db_session: DbSession) -> ModelConfigService:
    """为当前请求创建业务服务。"""
    return ModelConfigService(db_session)


ModelConfigServiceDependency = Annotated[ModelConfigService, Depends(get_model_config_service)]


# ---------- 新增模型配置接口
@router.post("", status_code=status.HTTP_201_CREATED, summary="新增模型配置")
def create_model(request_data: dict[str, Any], model_config_service: ModelConfigServiceDependency) -> Result[dict[str, Any]]:
    """request_data 为提交的 JSON 字段；直接保存实体，返回时统一排除 Key。"""
    return Result(data=model_config_service.create(request_data).to_dict())



# ---------- 分页查询模型配置接口
@router.get("", summary="分页查询模型配置")
def list_models(
    model_config_service: ModelConfigServiceDependency, page: int = 1, page_size: int = 20,
) -> Result[Page[dict[str, Any]]]:
    """page 和 page_size 来自 URL，仅保留框架的整数解析，不限制数值范围。"""
    return Result(data=model_config_service.list_page(page, page_size))


# ---------- 查询模型配置详情接口
@router.get("/{model_id}", summary="查询模型配置详情")
def get_model(model_id: int, model_config_service: ModelConfigServiceDependency) -> Result[dict[str, Any]]:
    """路径ID直接用于查询，不增加大于零等校验规则。"""
    return Result(data=model_config_service.get_detail(model_id).to_dict())


# ---------- 修改模型配置接口
@router.put("/{model_id}", summary="修改模型配置")
def update_model(
    model_id: int, request_data: dict[str, Any], model_config_service: ModelConfigServiceDependency,
) -> Result[dict[str, Any]]:
    """按原始 JSON 字段更新实体，不再要求整体提交所有字段。"""
    return Result(data=model_config_service.update(model_id, request_data).to_dict())


# ---------- 删除模型配置接口
@router.delete("/{model_id}", summary="删除模型配置")
def delete_model(model_id: int, model_config_service: ModelConfigServiceDependency) -> Result[None]:
    """删除成功返回统一 JSON。"""
    model_config_service.delete(model_id)
    return Result()


# ---------- 测试模型连接接口
@router.post("/{model_id}/test", summary="测试模型配置")
def test_model_connection(model_id: int, model_config_service: ModelConfigServiceDependency) -> Result[dict[str, int]]:
    """无需请求体，直接使用已保存配置进行一次真实模型调用。"""
    return Result(data=model_config_service.test_connection(model_id))
