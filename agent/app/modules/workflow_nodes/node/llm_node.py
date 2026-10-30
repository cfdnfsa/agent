"""大模型节点：使用已加载的模型和可选提示词调用 LangChain，不在节点中查库。"""

from langchain_core.prompt_values import ChatPromptValue

from app.infrastructure.ai.langchain.model_client import create_chat_model
from app.infrastructure.ai.langchain.prompt_builder import build_chat_prompt
from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.node_context import NodeContext
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_nodes.base.text import convert_input_to_text
from app.modules.workflow_nodes.node.data.llm_node_output import LlmNodeOutput
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

    # ---------- 调用大模型并保存回复
    def execute(self, node_input: NodeContext) -> LlmNodeOutput:
        """用公共模板准备消息，调用模型后同时保留正文和原始回复。

        Args:
            node_input: 按当前节点 input_scope 选出的直接或全部上游结果。

        Returns:
            value 为回答正文，message 为完整模型消息，供后续工具能力使用。
        """

        model_input = self.build_model_input(node_input)

        # 创建模型对象后，invoke 才真正发送请求。
        model = create_chat_model(self.resources.model_config)
        response = model.invoke(model_input)

        return LlmNodeOutput(value=str(response.text), message=response)

    # ---------- 组装交给模型的文字或消息
    def build_model_input(self, node_input: NodeContext) -> ChatPromptValue:
        """将已选择的上游数据转成文字，再由 LangChain 模板统一组装消息。

        Args:
            node_input: 当前节点实际收到的数据，不直接读取全局状态中的其他输出。

        Returns:
            LangChain 模型输入；选择提示词时增加原文系统消息，未选择时只有用户消息。
        """
        input_text = convert_input_to_text(node_input.results)
        system_prompt = None
        if self.resources.prompt_config is not None:
            system_prompt = self.resources.prompt_config.prompt_content
        return build_chat_prompt(input_text, system_prompt)
