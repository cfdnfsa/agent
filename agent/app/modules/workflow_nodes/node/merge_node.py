"""收敛节点：收集所有直接上游的结果，等待上游由 LangGraph 连线负责。"""

from typing import Any

from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


class MergeNode(BaseNode):
    """收敛节点：收集所有直接上游的结果；等待上游由 LangGraph 负责。"""

    # ---------- 收集各个上游的输出
    def read_input(self, state: WorkflowState) -> dict[str, Any]:
        """按上游ID保留结果边界，节点改名不会影响数据定位。"""
        upstream_outputs: dict[str, Any] = {}
        for source_id in self.source_ids:
            upstream_outputs[source_id] = state.node_outputs[source_id]
        return upstream_outputs

    # ---------- 输出收敛后的数据
    def execute(self, node_input: Any) -> Any:
        """当前原样输出收集的对象，不拼接正文，不丢弃分支信息。"""
        return node_input
