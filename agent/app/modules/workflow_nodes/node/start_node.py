"""开始节点：把本次请求的输入作为流程起点。"""

from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.node_context import NodeContext
from app.modules.workflow_nodes.base.data.node_output import NodeOutput
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


class StartNode(BaseNode):
    """开始节点：把本次输入的 text 原样交给下游，用户ID留在运行状态中。"""

    # ---------- 读取本次请求的输入
    def read_input(self, state: WorkflowState) -> NodeContext:
        """开始节点没有上游，将本次文字放在自己的ID下，作为最初的数据。

        用户ID继续保留在 state.inputs.user_id 中，不自动传入模型。
        """
        return NodeContext(results={self.definition.id: state.inputs.text})

    # ---------- 输出开始节点的数据
    def execute(self, node_input: NodeContext) -> NodeOutput:
        """不改写输入内容，不携带其他请求的数据。"""
        return NodeOutput(value=node_input.results[self.definition.id])
