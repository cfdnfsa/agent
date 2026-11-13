"""流程连线对象：说明数据从哪个节点传到哪个节点。"""

from dataclasses import dataclass
from typing import Any


@dataclass
class WorkflowEdge:
    """两个节点之间的连线。

    Attributes:
        source: 起点节点ID，表示数据从哪里来。
        target: 终点节点ID，表示接下来执行哪个节点。
        id: 画布连线ID，仅用于区分连线，不决定执行顺序。

    Examples:
        一条从开始节点连到大模型节点的原始 JSON 数据：

        {"id": "edge_1", "source": "start_1", "target": "llm_1"}

        表示 start_1 → llm_1；edge_1 是箭头的编号，不是中间节点。
    """

    source: str
    target: str
    id: str = ""

    # ---------- 从字典创建流程连线
    @classmethod
    def from_dict(cls, edge_data: dict[str, Any]) -> "WorkflowEdge":
        """集中读取连线字段，不额外校验或改写输入。

        Args:
            edge_data: 原始连线 JSON 字典，包含 source、target，可选 id。

        Returns:
            连线对象；缺少 id 键时用空字符串，键存在时保留原值。
        """
        # get("id", "") 仅在没有 id 键时返回 ""；已有值即使是 None 也不会被替换。
        return cls(
            source=edge_data["source"],
            target=edge_data["target"],
            id=edge_data.get("id", ""),
        )
