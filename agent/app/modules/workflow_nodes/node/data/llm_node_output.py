"""大模型节点输出：正文用于业务传递，完整模型消息留在本次运行内。"""

from dataclasses import dataclass

from langchain_core.messages import AIMessage

from app.modules.workflow_nodes.base.data.node_output import NodeOutput


@dataclass
class LlmNodeOutput(NodeOutput):
    """保留模型完整回复，便于后续工具调用等能力按需读取。

    Attributes:
        value: 继承的业务结果，当前为回复正文，默认传给下游和返回节点。
        message: LangChain 原始回复，含正文及模型返回的其他信息。
            不自动放入节点输入、不写日志或直接作为 HTTP 响应。
    """

    message: AIMessage
