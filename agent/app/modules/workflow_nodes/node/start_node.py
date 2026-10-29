"""开始节点：把本次请求的输入作为流程起点。"""

from typing import Any

from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


class StartNode(BaseNode):
    """开始节点：读取本次 HTTP 输入，原样传给下游。"""

    # ---------- 读取本次请求的输入
    def read_input(self, state: WorkflowState) -> Any:
        """开始节点没有上游，输入来自本次请求的 payload。"""
        return state.inputs.payload

    # ---------- 输出开始节点的数据
    def execute(self, node_input: Any) -> Any:
        """不改写输入内容，不携带其他请求的数据。"""
        return node_input
