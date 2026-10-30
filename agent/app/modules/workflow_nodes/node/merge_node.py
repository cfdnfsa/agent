"""收敛节点：收集所有直接上游的结果，等待上游由 LangGraph 连线负责。"""

from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.node_context import NodeContext
from app.modules.workflow_nodes.base.data.node_output import NodeOutput


class MergeNode(BaseNode):
    """收敛节点：收集所有直接上游的结果；等待上游由 LangGraph 负责。"""

    # ---------- 输出收敛后的数据
    def execute(self, node_input: NodeContext) -> NodeOutput:
        """所选输入作为本节点的收集结果，下游可以只读此结果或重新读取全部上游。"""
        return NodeOutput(value=node_input.results.copy())
