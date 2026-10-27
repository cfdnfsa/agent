"""个人使用的极简模型配置业务：JSON 直接交给实体，不添加字段校验或 DTO 转换。"""

from http import HTTPStatus
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.core.app_logging import logger, request_id_context
from app.core.errors.exceptions import BusinessError
from app.core.response.responses import Page
from app.infrastructure.database.transaction import transactional
from app.infrastructure.llm.model_client import create_chat_model
from app.modules.model_config.entity import ModelConfig
from app.modules.model_config.repository import ModelConfigRepository


class ModelConfigService:
    """直接维护数据库实体，事务仍由 Service 控制。"""

    # ---------- 初始化模型配置服务
    def __init__(self, db_session: Session):
        """db_session 是当前请求的数据库会话。"""
        self.db_session = db_session
        self.model_config_repository = ModelConfigRepository(db_session)

    # ---------- 新增模型配置
    @transactional
    def create(self, request_data: dict[str, Any]) -> ModelConfig:
        """request_data 为原始 JSON 对象，直接创建实体；表字段和数据库约束仍生效。"""
        model_config = ModelConfig(**request_data)
        self.model_config_repository.save(model_config)

        logger.info("请求ID=%s 操作=新增模型配置 模型ID=%s", request_id_context.get(), model_config.id)

        return model_config

    # ---------- 分页查询模型配置
    def list_page(self, page: int, page_size: int) -> Page[dict[str, Any]]:
        """按传入页码和数量查询，不做范围校验；JSON 输出只排除 Key。"""
        total_count = self.model_config_repository.count()
        model_configs = self.model_config_repository.list_page(page, page_size)
        return Page(
            items=[model_config.to_dict() for model_config in model_configs],
            total=total_count, page=page, page_size=page_size,
        )

    # ---------- 查询模型配置详情
    def get_detail(self, model_id: int) -> ModelConfig:
        """返回查询到的实体，不额外创建响应对象。"""
        return self.require_model_config(model_id)

    # ---------- 修改模型配置
    @transactional
    def update(self, model_id: int, request_data: dict[str, Any]) -> ModelConfig:
        """提交哪些字段就更新哪些字段；未提交的字段保留，不转换空串或自动去空格。"""
        model_config = self.require_model_config(model_id)

        for field_name, field_value in request_data.items():
            setattr(model_config, field_name, field_value)

        self.model_config_repository.save(model_config)

        logger.info("请求ID=%s 操作=修改模型配置 模型ID=%s", request_id_context.get(), model_config.id)

        return model_config

    # ---------- 删除模型配置
    @transactional
    def delete(self, model_id: int) -> None:
        """按配置表主键删除实体。"""
        self.model_config_repository.delete(self.require_model_config(model_id))

        logger.info("请求ID=%s 操作=删除模型配置 模型ID=%s", request_id_context.get(), model_id)

    # ---------- 测试模型连接
    def test_connection(self, model_id: int) -> dict[str, int]:
        """读取含 Key 的实体进行真实调用；事务结束后直接把实体传给模型客户端。"""
        with self.db_session.begin():
            model_config = self.require_model_config(model_id, include_api_key=True)
        call_started_at = perf_counter()

        logger.info("请求ID=%s 操作=测试模型连接开始 模型ID=%s", request_id_context.get(), model_id)

        model = create_chat_model(model_config)
        # 测试只确认本次请求能完成，不检查回复内容；失败交给公共异常处理。
        model.invoke("Reply with OK only.")
        elapsed_ms = round((perf_counter() - call_started_at) * 1000)

        logger.info("请求ID=%s 操作=测试模型连接成功 模型ID=%s 耗时=%s毫秒", request_id_context.get(), model_id, elapsed_ms)

        return {"elapsed_ms": elapsed_ms}

    # ---------- 查询模型配置并处理不存在的情况
    def require_model_config(self, model_id: int, include_api_key: bool = False) -> ModelConfig:
        """按ID取得实体，找不到时返回统一业务错误；默认查询不读取 Key。"""
        model_config = self.model_config_repository.get_by_id(model_id, include_api_key)
        if model_config is None:
            raise BusinessError("模型配置不存在", HTTPStatus.NOT_FOUND)
        return model_config
