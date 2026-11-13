"""模型调用输出：保存业务结果与完整模型消息，供调用模型的节点共用。"""

from dataclasses import dataclass

from langchain_core.messages import AIMessage

from app.workflow.data.execution.node_output import NodeOutput


@dataclass
class LlmNodeOutput(NodeOutput):
    """保留模型完整回复，便于后续工具调用等能力按需读取。

    Attributes:
        value: 继承的业务结果，普通 LLM 为回复正文，意图分析为固定任务结果对象。
        message: LangChain 原始回复，含正文及模型返回的其他信息。
            不自动放入节点输入、不写日志或直接作为 HTTP 响应。
    """

    message: AIMessage
