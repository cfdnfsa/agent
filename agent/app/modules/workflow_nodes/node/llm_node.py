"""大模型节点：使用已加载的模型和可选提示词调用 LangChain，不在节点中查库。"""

import json
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.infrastructure.ai.langchain.model_client import create_chat_model
from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_nodes.node.data.llm_node_resources import LlmNodeResources


class LlmNode(BaseNode):
    """大模型节点：使用已加载的模型配置处理上游数据。

    Attributes:
        resources: 本节点需要的模型、可选提示词等资源，实体仅供内部只读使用。
    """

    # ---------- 保存大模型节点需要的配置
    def __init__(self, definition: WorkflowNode, source_ids: list[str], resources: LlmNodeResources):
        """接收 factory 准备的资源对象，新增资源时集中扩展此对象。

        Args:
            definition: 当前节点的ID、类型和配置定义。
            source_ids: 当前节点直接上游的ID列表。
            resources: 已加载的模型和可选提示词实体，节点内不再查询数据库。
        """
        super().__init__(definition, source_ids)
        self.resources = resources

    # ---------- 调用大模型并返回文字
    def execute(self, node_input: Any) -> str:
        """依次转换输入、创建模型、组装消息并调用，具体准备逻辑交给小方法。

        Args:
            node_input: 一个上游的结果，可以是文字，也可以是收敛后的对象。

        Returns:
            模型回答正文；请求参数使用现有公共模型配置。
        """

        input_text = convert_input_to_text(node_input)
        model_input = self.build_model_input(input_text)

        # 创建模型对象后，invoke 才真正发送请求。
        model = create_chat_model(self.resources.model_config)
        response = model.invoke(model_input)

        return str(response.text)

    # ---------- 组装交给模型的文字或消息
    def build_model_input(self, input_text: str) -> str | list[BaseMessage]:
        """根据是否选择提示词，决定直接传文字还是提供系统、用户两条消息。

        Args:
            input_text: 已转换成文字的上游结果。

        Returns:
            未选提示词时返回原文字；选中时返回框架消息列表，正文原样使用。
        """
        if self.resources.prompt_config is None:
            return input_text

        # 使用框架的消息对象区分角色：系统消息说明任务，用户消息承载上游数据。
        return [
            SystemMessage(content=self.resources.prompt_config.prompt_content),
            HumanMessage(content=input_text),
        ]


# ---------- 将节点输入转换成模型可读的文字
def convert_input_to_text(node_input: Any) -> str:
    """文字原样保留，对象或列表转成 JSON 文字，保留中文以便模型阅读。

    Args:
        node_input: 一个上游的结果，可以是文字，也可以是收敛后的对象。

    Returns:
        交给模型的输入文字；JSON 无法序列化时沿用原有异常处理。
    """
    if isinstance(node_input, str):
        return node_input
    return json.dumps(node_input, ensure_ascii=False)
