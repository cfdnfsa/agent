"""开始节点：把本次请求的输入作为流程起点。"""

from typing import Any

from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


class StartNode(BaseNode):
    """开始节点：把本次输入的 text 原样交给下游，用户ID留在运行状态中。"""

    # ---------- 读取本次请求的输入
    def read_input(self, state: WorkflowState) -> str:
        """读取本次文字；后续节点需要用户ID时，可从 state.inputs.user_id 取得。"""
        return state.inputs.text

    # ---------- 输出开始节点的数据
    def execute(self, node_input: Any) -> Any:
        """不改写输入内容，不携带其他请求的数据。"""
        return node_input
