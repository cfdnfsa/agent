"""HTTP 接口层：定义路径、请求校验和依赖关系，具体业务交给 Service。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.response.responses import ERROR_RESPONSES, Page, Result
from app.infrastructure.database.db_connection import DbSession
from app.modules.model_config.schemas import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigUpdate,
)
from app.modules.model_config.service import ModelConfigService

# 所有接口共用这个前缀；tags 决定它们在 /docs 中归属哪个分组。
router = APIRouter(prefix="/api/model-configs", tags=["模型配置"], responses=ERROR_RESPONSES)
# Annotated 给 int 附加路径校验信息，非法ID会在进入业务方法前返回 422。
ModelConfigId = Annotated[int, Path(gt=0, description="模型配置ID")]


def get_model_config_service(db_session: DbSession) -> ModelConfigService:
    """把请求会话交给业务服务，避免在每个接口中重复装配。"""
    # DbSession 复用公共会话依赖；这里只负责把会话传给当前模块的 Service。
    return ModelConfigService(db_session)


# 接口声明 model_config_service: ModelConfigServiceDependency 后，FastAPI 会提供模型配置服务。
ModelConfigServiceDependency = Annotated[ModelConfigService, Depends(get_model_config_service)]


@router.post("", response_model=Result[ModelConfigResponse], status_code=status.HTTP_201_CREATED,
             summary="新增模型配置")
def create_model(
        create_request: ModelConfigCreate,
        model_config_service: ModelConfigServiceDependency,
) -> Result[ModelConfigResponse]:
    """新增配置；响应不包含 API Key。"""
    # create_request 从 JSON 请求体读取并自动校验；response_model 明确限制返回字段。
    return Result[ModelConfigResponse](data=model_config_service.create(create_request))


@router.get("", response_model=Result[Page[ModelConfigResponse]], summary="分页查询模型配置")
def list_models(
        model_config_service: ModelConfigServiceDependency,
        page: Annotated[int, Query(ge=1, description="页码")] = 1,
        page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
) -> Result[Page[ModelConfigResponse]]:
    """按配置ID倒序查询，单页最多返回 100 条。"""
    # Query 参数来自 URL，如 ?page=1&page_size=20；ge/le 是最小值/最大值约束。
    return Result[Page[ModelConfigResponse]](data=model_config_service.list_page(page, page_size))


@router.get("/{model_id}", response_model=Result[ModelConfigResponse], summary="查询模型配置详情")
def get_model(
        model_id: ModelConfigId,
        model_config_service: ModelConfigServiceDependency,
) -> Result[ModelConfigResponse]:
    """读取单条配置，不返回 API Key。"""
    # model_id 来自 /api/model-configs/{model_id}，不存在时统一返回 404。
    return Result[ModelConfigResponse](data=model_config_service.get_detail(model_id))


@router.put("/{model_id}", response_model=Result[ModelConfigResponse], summary="修改模型配置")
def update_model(
        model_id: ModelConfigId,
        update_request: ModelConfigUpdate,
        model_config_service: ModelConfigServiceDependency,
) -> Result[ModelConfigResponse]:
    """修改配置；Key 不传保留，null 或空字符串清除，其他值替换。"""
    # 使用 PUT 整体修改四个普通配置项，Key 的保留与清除由 Service 判断。
    return Result[ModelConfigResponse](data=model_config_service.update(model_id, update_request))


@router.delete("/{model_id}", response_model=Result[None], summary="删除模型配置")
def delete_model(model_id: ModelConfigId, model_config_service: ModelConfigServiceDependency) -> Result[None]:
    """按ID删除配置，成功后返回 HTTP 200 和统一 JSON。"""
    model_config_service.delete(model_id)
    # 统一返回格式需要响应体，因此使用 200，data 为 null。
    return Result[None]()
