"""提示词变量的来源配置，随当前节点保存在流程定义中。"""

from dataclasses import dataclass


@dataclass
class PromptVariable:
    """模板中的一个变量从哪里取值，不保存本次运行的实际数据。

    Attributes:
        source: question 为本次问题，upstream 为当前输入范围的全部结果，node 为指定上游结果。
        node_id: source 为 node 时使用的上游节点ID，其他来源无需填写。
    """

    source: str
    node_id: str | None = None
