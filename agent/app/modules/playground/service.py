"""极简单轮问答：读取模型实体，调用框架并直接返回回答。"""

from http import HTTPStatus
from time import perf_counter
from typing import Any

from app.core.app_logging import logger, request_id_context
from app.core.errors.exceptions import BusinessError
from app.infrastructure.ai.langchain.model_client import create_chat_model
from app.modules.model_config.cache import get_model_config


class PlaygroundService:
    """不维护上下文，不保存问答记录，不增加请求字段校验。"""

    # ---------- 执行单轮模型问答
    def ask_model(self, request_data: dict[str, Any]) -> dict[str, str]:
        """按选择的模型进行一次问答，不保存历史。

        Args:
            request_data: 原始 JSON；model_config_id 是配置主键，question 是当前问题。

        Returns:
            包含 answer 文本的字典，模型调用失败交给公共异常处理。
        """
        model_id = request_data["model_config_id"]
        model_config = get_model_config(model_id)
        if model_config is None:
            raise BusinessError("模型配置不存在，请重新选择模型。", HTTPStatus.NOT_FOUND)
        # 缓存未命中时的查询已在读取入口结束，不把数据库会话带入模型调用。
        call_started_at = perf_counter()

        logger.info("请求ID=%s 操作=调试台问答开始 模型ID=%s", request_id_context.get(), model_id)

        model = create_chat_model(model_config)
        # invoke 是框架提供的方法；只传当前问题，text 取得回复中的文本。
        answer = str(model.invoke(request_data["question"]).text)

        logger.info("请求ID=%s 操作=调试台问答成功 模型ID=%s 耗时=%.0f毫秒", request_id_context.get(), model_id, (perf_counter() - call_started_at) * 1000)

        return {"answer": answer}
