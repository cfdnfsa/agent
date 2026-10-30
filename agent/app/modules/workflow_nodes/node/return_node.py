"""返回节点：原样输出上游数据，由运行模块选作接口返回内容。"""

from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.node_context import NodeContext
from app.modules.workflow_nodes.base.data.node_output import NodeOutput
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


class ReturnNode(BaseNode):
    """一个流程只有一个返回节点，接收一个上游，不能连接下游。"""

    # ---------- 读取上游最终处理结果
    def read_input(self, state: WorkflowState) -> NodeContext:
        """运行模块已确认恰好一个上游；接口只取其 value，不自动返回其他节点记录。"""
        source_id = self.source_ids[0]
        return NodeContext(results={source_id: state.node_outputs[source_id].value})

    # ---------- 输出本次流程需要返回的数据
    def execute(self, node_input: NodeContext) -> NodeOutput:
        """原样保留上游的数据类型和内容，其他分支的结果不混入此处。

        Args:
            node_input: 以直接上游ID保存的最终结果；返回多路数据时先使用收敛节点。

        Returns:
            本次接口返回的业务数据；图中其他分支仍按正常调度完成。
        """
        return NodeOutput(value=node_input.results[self.source_ids[0]])
