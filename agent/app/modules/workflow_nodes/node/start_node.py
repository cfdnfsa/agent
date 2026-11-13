"""开始节点：把本次请求的输入作为流程起点。"""

from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.node_context import NodeContext
from app.modules.workflow_nodes.base.data.node_output import NodeOutput
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


class StartNode(BaseNode):
    """开始节点：主流程输出原问题，任务流程输出当前任务问题。"""

    # ---------- 读取本次请求的输入
    def read_input(self, state: WorkflowState) -> NodeContext:
        """开始节点没有上游，将当前要处理的文字放在自己的ID下。

        原始问题与用户ID仍在 state.inputs 中；任务不覆盖它们，{question} 仍取原问题。
        """
        if state.task is None:
            input_text = state.inputs.text
        else:
            input_text = state.task.question
        return NodeContext(results={self.definition.id: input_text}, question=state.inputs.text)

    # ---------- 输出开始节点的数据
    def execute(self, node_input: NodeContext) -> NodeOutput:
        """不改写输入内容，不携带其他请求的数据。"""
        return NodeOutput(value=node_input.results[self.definition.id])
