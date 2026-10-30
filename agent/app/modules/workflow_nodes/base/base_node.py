"""节点公共执行入口：读取输入、记录日志、调用具体业务，再提交本节点输出。"""

from app.core.app_logging import logger, request_id_context
from app.modules.workflow_nodes.base.data.node_context import NodeContext
from app.modules.workflow_nodes.base.data.node_output import NodeOutput
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


class BaseNode:
    """节点公共入口，LangGraph 调用 run，各子类实现 execute。

    Attributes:
        definition: 已保存的节点定义，ID 用于定位输出，名称用于日志。
        source_ids: 连线指向本节点的上游ID，不依赖节点列表顺序。
        input_ids: 本节点实际读取的结果ID，由运行模块根据输入范围提前准备。
    """

    # ---------- 保存当前节点的配置
    def __init__(self, definition: WorkflowNode, source_ids: list[str]):
        """只保存配置；输入、输出等每次运行的数据都放在 WorkflowState 中。"""
        self.definition = definition
        self.source_ids = source_ids
        self.input_ids = source_ids

    # ---------- 统一执行节点并记录输入输出
    def run(self, state: WorkflowState) -> dict[str, dict[str, NodeOutput]]:
        """读取输入、调用子类业务，再把当前节点的输出交给 LangGraph。

        Args:
            state: 本次请求独立的运行状态；不保存到节点对象上。

        Returns:
            仅含当前节点输出的状态增量，不覆盖其他分支结果。
        """
        node = self.definition

        logger.info("请求ID=%s 操作=执行节点开始 节点ID=%s 节点名称=%s 节点类型=%s", request_id_context.get(), node.id, node.name or node.id, node.type)

        node_input = self.read_input(state)

        logger.debug("请求ID=%s 节点ID=%s 输入=%r", request_id_context.get(), node.id, node_input.results)

        # self.execute 会调用实际子类的方法，例如 LlmNode.execute。
        node_output = self.execute(node_input)

        logger.debug("请求ID=%s 节点ID=%s 输出=%r", request_id_context.get(), node.id, node_output.value)

        logger.info("请求ID=%s 操作=执行节点完成 节点ID=%s 节点名称=%s", request_id_context.get(), node.id, node.name or node.id)

        return {"node_outputs": {node.id: node_output}}

    # ---------- 从统一结果中选出本节点需要的数据
    def read_input(self, state: WorkflowState) -> NodeContext:
        """input_ids 已按上游依赖确定，运行时只按ID取值，不重新遍历流程图。

        允许一个或多个直接上游，LangGraph 会先等待它们全部完成再调用本节点。

        Args:
            state: 本次运行统一保存的全部节点结果。

        Returns:
            当前节点的输入上下文；不修改其他节点已经保存的结果。
        """
        node_input = NodeContext()
        for input_id in self.input_ids:
            node_input.results[input_id] = state.node_outputs[input_id].value
        return node_input

    # ---------- 由具体节点实现业务
    def execute(self, node_input: NodeContext) -> NodeOutput:
        """子类负责处理 node_input 并返回 NodeOutput，不在这里调用后续节点。"""
        raise NotImplementedError("具体节点需要实现 execute 方法")
