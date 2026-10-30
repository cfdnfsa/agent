"""节点输入上下文：按当前节点的配置，从运行状态中选出的上游数据。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeContext:
    """本次节点实际使用的数据，不修改统一保存的原始结果。

    Attributes:
        results: 节点ID到业务结果的映射，结果允许文字、对象或列表。
            只包含选中的直接或全部上游，不包含无关分支或跨请求历史。
    """

    results: dict[str, Any] = field(default_factory=dict)
