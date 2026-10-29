"""本次流程输入：由接口创建，交给开始节点读取。"""

from dataclasses import dataclass
from typing import Any


@dataclass
class WorkflowInput:
    """本次运行输入，运行之间互不共享。

    Attributes:
        payload: 入口收到的实际业务数据，最小示例是一段文字。
    """

    payload: Any
