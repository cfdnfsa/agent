"""流程配置业务：维护名称和定义文本，提供增删改查。"""

from http import HTTPStatus
from typing import Any

from sqlalchemy.orm import Session

from app.core.app_logging import logger, request_id_context
from app.core.errors.exceptions import BusinessError
from app.core.response.responses import Page
from app.infrastructure.database.transaction import transactional
from app.modules.workflow_config.entity import WorkflowConfig
from app.modules.workflow_config.repository import WorkflowConfigRepository


class WorkflowConfigService:
    """复用当前请求会话，写操作通过公共装饰器统一提交或回滚。"""

    # ---------- 初始化流程配置服务
    def __init__(self, db_session: Session):
        """db_session 由 FastAPI 依赖提供，Service 和 Repository 共用这个会话。"""
        self.db_session = db_session
        self.workflow_config_repository = WorkflowConfigRepository(db_session)

    # ---------- 新增流程配置
    @transactional
    def create(self, request_data: dict[str, Any]) -> WorkflowConfig:
        """request_data 包含流程名称和定义字符串，原样创建实体并返回，不解析其中的 JSON。"""
        workflow_config = WorkflowConfig(**request_data)
        self.workflow_config_repository.save(workflow_config)

        logger.info("请求ID=%s 操作=新增流程配置 流程ID=%s", request_id_context.get(), workflow_config.id)

        return workflow_config

    # ---------- 分页查询流程配置
    def list_page(self, page: int, page_size: int) -> Page[dict[str, Any]]:
        """page、page_size 为传入页码和数量，返回只含 ID、名称的分页概要。"""
        total_count = self.workflow_config_repository.count()
        workflow_summaries = self.workflow_config_repository.list_page(page, page_size)
        return Page(items=workflow_summaries, total=total_count, page=page, page_size=page_size)

    # ---------- 查询流程配置详情
    def get_detail(self, workflow_id: int) -> WorkflowConfig:
        """workflow_id 是流程主键；返回三个字段的实体，不存在时抛出公共业务异常。"""
        return self.require_workflow_config(workflow_id)

    # ---------- 修改流程配置
    @transactional
    def update(self, workflow_id: int, request_data: dict[str, Any]) -> WorkflowConfig:
        """按 workflow_id 找到实体，提交哪些字段就更新哪些，未提交字段保留原值。"""
        workflow_config = self.require_workflow_config(workflow_id)
        for field_name, field_value in request_data.items():
            setattr(workflow_config, field_name, field_value)
        self.workflow_config_repository.save(workflow_config)

        logger.info("请求ID=%s 操作=修改流程配置 流程ID=%s", request_id_context.get(), workflow_config.id)

        return workflow_config

    # ---------- 删除流程配置
    @transactional
    def delete(self, workflow_id: int) -> None:
        """workflow_id 是待删除流程主键，不存在时返回 404，成功删除后无业务数据。"""
        self.workflow_config_repository.delete(self.require_workflow_config(workflow_id))

        logger.info("请求ID=%s 操作=删除流程配置 流程ID=%s", request_id_context.get(), workflow_id)

    # ---------- 查询流程配置并处理不存在的情况
    def require_workflow_config(self, workflow_id: int) -> WorkflowConfig:
        """按流程主键取得完整实体，查不到时由统一异常处理返回 HTTP 404。"""
        workflow_config = self.workflow_config_repository.get_by_id(workflow_id)
        if workflow_config is None:
            raise BusinessError("流程配置不存在", HTTPStatus.NOT_FOUND)
        return workflow_config
