"""模型配置业务入口：接收已校验入参，组织数据库操作，返回不含 Key 的结果。"""

from http import HTTPStatus

from sqlalchemy.orm import Session

from app.core.errors.exceptions import BusinessError
from app.core.app_logging import logger, request_id_context
from app.core.response.responses import Page
from app.modules.model_config.entity import ModelConfig
from app.modules.model_config.repository import ModelConfigRepository
from app.modules.model_config.schemas import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigUpdate,
)


class ModelConfigService:
    """模型配置业务服务，负责密钥修改语义和写入事务。"""

    def __init__(self, db_session: Session):
        """Repository 与 Service 使用同一个请求会话，保证写入处于同一事务。"""
        self.db_session = db_session
        self.model_config_repository = ModelConfigRepository(db_session)

    def create(self, create_request: ModelConfigCreate) -> ModelConfigResponse:
        """创建模型配置，成功提交后才返回结果。"""
        # create_request 是 Pydantic 入参，不是数据库实体，需要明确转换允许保存的字段。
        model_api_key = create_request.model_api_key
        model_config = ModelConfig(
            model_name=create_request.model_name,
            model_code=create_request.model_code,
            # 枚举取出用于数据库保存的字符串，URL 对象也转换为字符串。
            model_provider=create_request.model_provider.value,
            model_base_url=str(create_request.model_base_url),
            # get_secret_value 只是取出原始字符串，不执行加密；空 Key 统一存为 NULL。
            model_api_key=(model_api_key.get_secret_value() or None) if model_api_key is not None else None,
        )
        # 正常离开 begin 块会提交；块内抛出异常则自动回滚，避免只保存一部分改动。
        with self.db_session.begin():
            self.model_config_repository.save(model_config)
            # 转换为只含公开字段的响应对象，Key 不会进入这个对象。
            model_config_response = ModelConfigResponse.model_validate(model_config)

        # 放在事务块之后：只有提交成功才记录成功日志，不记录请求体或原 Key。
        logger.info(
            "request_id=%s operation=model_config.create model_id=%s",
            request_id_context.get(), model_config.id,
        )
        return model_config_response

    def list_page(self, page: int, page_size: int) -> Page[ModelConfigResponse]:
        """返回有数量边界的列表，所有记录通过不含 Key 的出参转换。"""
        # 总条数用于分页，本页查询只读取当前页，不把全部数据取出后再分页。
        total_count = self.model_config_repository.count()
        model_configs = self.model_config_repository.list_page(page, page_size)
        return Page[ModelConfigResponse](
            items=[ModelConfigResponse.model_validate(model_config) for model_config in model_configs],
            total=total_count,
            page=page,
            page_size=page_size,
        )

    def get_detail(self, model_id: int) -> ModelConfigResponse:
        """获取单条配置的公开信息。"""
        # _require_model_config 统一处理找不到记录的情况，存在时才转换为响应。
        model_config = self._require_model_config(model_id)
        return ModelConfigResponse.model_validate(model_config)

    def update(self, model_id: int, update_request: ModelConfigUpdate) -> ModelConfigResponse:
        """整体更新模型配置，省略密钥字段时保留原值。"""
        with self.db_session.begin():
            # 先确认目标存在；这些对象属性的变化会被 ORM 跟踪，不需要手写 UPDATE。
            model_config = self._require_model_config(model_id)
            model_config.model_name = update_request.model_name
            model_config.model_code = update_request.model_code
            model_config.model_provider = update_request.model_provider.value
            model_config.model_base_url = str(update_request.model_base_url)
            # 依据字段是否实际提交区分“保留 Key”和“清除 Key”。
            # 不能只判断 update_request.model_api_key，因为“没传”和“传 null”读取后都是 None。
            if "model_api_key" in update_request.model_fields_set:
                model_api_key = update_request.model_api_key
                model_config.model_api_key = (
                    (model_api_key.get_secret_value() or None) if model_api_key is not None else None
                )
            self.model_config_repository.save(model_config)
            model_config_response = ModelConfigResponse.model_validate(model_config)

        logger.info(
            "request_id=%s operation=model_config.update model_id=%s",
            request_id_context.get(), model_id,
        )
        return model_config_response

    def delete(self, model_id: int) -> None:
        """删除指定模型配置；不存在时交由接口层返回 404。"""
        with self.db_session.begin():
            # 只删除按主键查到的这一条，不会执行整表删除或清库。
            model_config = self._require_model_config(model_id)
            self.model_config_repository.delete(model_config)

        logger.info(
            "request_id=%s operation=model_config.delete model_id=%s",
            request_id_context.get(), model_id,
        )

    def _require_model_config(self, model_id: int) -> ModelConfig:
        """定位配置并统一处理不存在的分支。"""
        model_config = self.model_config_repository.get_by_id(model_id)
        if model_config is None:
            logger.warning(
                "request_id=%s operation=model_config.not_found model_id=%s",
                request_id_context.get(), model_id,
            )
            # 这里表达业务结果，不直接依赖 HTTP；由统一异常处理器决定状态码。
            raise BusinessError("模型配置不存在", status_code=HTTPStatus.NOT_FOUND)
        return model_config
