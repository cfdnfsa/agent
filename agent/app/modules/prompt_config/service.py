"""提示词配置业务：维护提示词名称和正文，沿用极简配置增删改查。"""

from http import HTTPStatus
from typing import Any

from sqlalchemy.orm import Session

from app.core.app_logging import logger, request_id_context
from app.core.errors.exceptions import BusinessError
from app.core.response.responses import Page
from app.infrastructure.database.transaction import transactional
from app.modules.prompt_config.entity import PromptConfig
from app.modules.prompt_config.repository import PromptConfigRepository


class PromptConfigService:
    """Service 与 Repository 共用请求会话，写操作由公共装饰器提交或回滚。"""

    # ---------- 初始化提示词配置服务
    def __init__(self, db_session: Session):
        """db_session 由 FastAPI 依赖提供，只在当前请求中使用。"""
        self.db_session = db_session
        self.prompt_config_repository = PromptConfigRepository(db_session)

    # ---------- 新增提示词配置
    @transactional
    def create(self, request_data: dict[str, Any]) -> PromptConfig:
        """request_data 包含 prompt_name、prompt_content，直接创建实体，不改写正文。"""
        prompt_config = PromptConfig(**request_data)
        self.prompt_config_repository.save(prompt_config)

        logger.info("请求ID=%s 操作=新增提示词配置 提示词ID=%s", request_id_context.get(), prompt_config.id)

        return prompt_config

    # ---------- 分页查询提示词配置
    def list_page(self, page: int, page_size: int) -> Page[dict[str, Any]]:
        """page、page_size 为请求传入的页码和数量，返回 ID、名称及分页信息。"""
        total_count = self.prompt_config_repository.count()
        prompt_summaries = self.prompt_config_repository.list_page(page, page_size)
        return Page(items=prompt_summaries, total=total_count, page=page, page_size=page_size)

    # ---------- 查询提示词配置详情
    def get_detail(self, prompt_id: int) -> PromptConfig:
        """prompt_id 为提示词主键，返回完整实体；不存在时抛出统一 404 业务异常。"""
        return self.require_prompt_config(prompt_id)

    # ---------- 修改提示词配置
    @transactional
    def update(self, prompt_id: int, request_data: dict[str, Any]) -> PromptConfig:
        """按 prompt_id 查询实体，提交哪些字段就更新哪些字段，未提交字段保持原值。"""
        prompt_config = self.require_prompt_config(prompt_id)
        for field_name, field_value in request_data.items():
            setattr(prompt_config, field_name, field_value)
        self.prompt_config_repository.save(prompt_config)

        logger.info("请求ID=%s 操作=修改提示词配置 提示词ID=%s", request_id_context.get(), prompt_config.id)

        return prompt_config

    # ---------- 删除提示词配置
    @transactional
    def delete(self, prompt_id: int) -> None:
        """prompt_id 为待删除主键，按记录删除；不存在时抛出统一 404 业务异常。"""
        self.prompt_config_repository.delete(self.require_prompt_config(prompt_id))

        logger.info("请求ID=%s 操作=删除提示词配置 提示词ID=%s", request_id_context.get(), prompt_id)

    # ---------- 查询提示词配置并处理不存在的情况
    def require_prompt_config(self, prompt_id: int) -> PromptConfig:
        """按主键取得完整实体，找不到时由公共异常处理器生成 HTTP 404 响应。"""
        prompt_config = self.prompt_config_repository.get_by_id(prompt_id)
        if prompt_config is None:
            raise BusinessError("提示词配置不存在", HTTPStatus.NOT_FOUND)
        return prompt_config
