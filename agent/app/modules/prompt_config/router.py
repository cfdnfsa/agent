"""提示词配置接口：接收 JSON 字典，注入 Service，复用公共返回结构。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.core.response.responses import ERROR_RESPONSES, Page, Result
from app.infrastructure.database.db_connection import DbSession
from app.modules.prompt_config.service import PromptConfigService


router = APIRouter(prefix="/api/prompt-configs", tags=["提示词配置"], responses=ERROR_RESPONSES)


# ---------- 提供提示词配置服务
def get_prompt_config_service(db_session: DbSession) -> PromptConfigService:
    """把当前请求的数据库会话交给提示词服务，统一装配 Service 和 Repository。"""
    return PromptConfigService(db_session)


PromptConfigServiceDependency = Annotated[PromptConfigService, Depends(get_prompt_config_service)]


# ---------- 新增提示词配置接口
@router.post("", status_code=status.HTTP_201_CREATED, summary="新增提示词配置")
def create_prompt(
    request_data: dict[str, Any], prompt_config_service: PromptConfigServiceDependency,
) -> Result[dict[str, Any]]:
    """request_data 使用 prompt_name、prompt_content，成功返回包含主键的完整配置。"""
    return Result(data=prompt_config_service.create(request_data).to_dict())


# ---------- 分页查询提示词配置接口
@router.get("", summary="分页查询提示词配置")
def list_prompts(
    prompt_config_service: PromptConfigServiceDependency, page: int = 1, page_size: int = 20,
) -> Result[Page[dict[str, Any]]]:
    """page、page_size 来自 URL 查询参数，返回 ID、名称和分页信息，不读取正文。"""
    return Result(data=prompt_config_service.list_page(page, page_size))


# ---------- 查询提示词配置详情接口
@router.get("/{prompt_id}", summary="查询提示词配置详情")
def get_prompt(
    prompt_id: int, prompt_config_service: PromptConfigServiceDependency,
) -> Result[dict[str, Any]]:
    """prompt_id 来自 URL 路径，返回完整三个字段，正文保持原文。"""
    return Result(data=prompt_config_service.get_detail(prompt_id).to_dict())


# ---------- 修改提示词配置接口
@router.put("/{prompt_id}", summary="修改提示词配置")
def update_prompt(
    prompt_id: int, request_data: dict[str, Any], prompt_config_service: PromptConfigServiceDependency,
) -> Result[dict[str, Any]]:
    """按 prompt_id 更新 request_data 中提交的字段，支持只修改名称或正文。"""
    return Result(data=prompt_config_service.update(prompt_id, request_data).to_dict())


# ---------- 删除提示词配置接口
@router.delete("/{prompt_id}", summary="删除提示词配置")
def delete_prompt(
    prompt_id: int, prompt_config_service: PromptConfigServiceDependency,
) -> Result[None]:
    """prompt_id 为待删除主键，成功返回 data=null，记录不存在返回 HTTP 404。"""
    prompt_config_service.delete(prompt_id)
    return Result()
