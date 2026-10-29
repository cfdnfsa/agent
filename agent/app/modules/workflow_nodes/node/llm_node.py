"""大模型节点：使用已经加载的模型实体调用 LangChain，不在节点中查询数据库。"""

import json
from typing import Any

from app.infrastructure.ai.langchain.model_client import create_chat_model
from app.modules.model_config.entity import ModelConfig
from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode


class LlmNode(BaseNode):
    """大模型节点：使用已加载的模型配置处理上游数据。

    Attributes:
        model_config: 数据库模型实体，含调用需要的 Key，仅供内部使用。
    """

    # ---------- 保存大模型节点需要的配置
    def __init__(self, definition: WorkflowNode, source_ids: list[str], model_config: ModelConfig):
        """复用公共节点配置；接收已查询的实体，不在节点内查询数据库。"""
        super().__init__(definition, source_ids)
        self.model_config = model_config

    # ---------- 调用大模型并返回文字
    def execute(self, node_input: Any) -> str:
        """文字直接传递；对象或列表转成 JSON 文字，供模型读取。

        Args:
            node_input: 一个上游的结果，可以是文字，也可以是收敛后的对象。

        Returns:
            模型回答正文；请求参数使用现有公共模型配置。
        """

        if isinstance(node_input, str):
            input_text = node_input
        else:
            input_text = json.dumps(node_input, ensure_ascii=False)

        # 创建模型对象后，invoke 才真正发送请求。
        model = create_chat_model(self.model_config)
        txt = model.invoke(input_text).text
        return str(txt)
