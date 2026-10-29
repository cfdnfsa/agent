"""本次流程输入：固定为用户文字与可选用户ID，供流程中的节点按属性读取。"""

from dataclasses import dataclass


@dataclass
class WorkflowInput:
    """本次运行输入，运行之间互不共享。

    Attributes:
        text: 本次用户输入的文字，开始节点将它原样交给下游。
        user_id: 可选用户ID，先保留在运行状态中，后续记忆等节点需要时读取。
    """

    text: str
    user_id: str | None = None
