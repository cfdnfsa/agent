"""节点输出：统一保存当前节点的处理结果，输入范围由使用它的节点决定。"""

from dataclasses import dataclass
from typing import Any


@dataclass
class NodeOutput:
    """一次节点执行产生的输出，仅保存在本次运行状态中。

    Attributes:
        value: 本节点的业务结果；其他节点按各自的输入范围读取，返回节点也只取此字段。
    """

    value: Any
