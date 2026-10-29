"""节点公共执行入口：读取输入、记录日志、调用具体业务，再提交本节点输出。"""

from typing import Any

from app.core.app_logging import logger, request_id_context
from app.core.errors.exceptions import BusinessError
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


class BaseNode:
    """节点公共入口，LangGraph 调用 run，各子类实现 execute。

    Attributes:
        definition: 已保存的节点定义，ID 用于定位输出，名称用于日志。
        source_ids: 连线指向本节点的上游ID，不依赖节点列表顺序。
    """

    # ---------- 保存当前节点的配置
    def __init__(self, definition: WorkflowNode, source_ids: list[str]):
        """只保存配置；输入、输出等每次运行的数据都放在 WorkflowState 中。"""
        self.definition = definition
        self.source_ids = source_ids

    # ---------- 统一执行节点并记录输入输出
    def run(self, state: WorkflowState) -> dict[str, dict[str, Any]]:
        """读取输入、调用子类业务，再把当前节点的输出交给 LangGraph。

        Args:
            state: 本次请求独立的运行状态；不保存到节点对象上。

        Returns:
            仅含当前节点输出的状态增量，不覆盖其他分支结果。
        """
        node = self.definition

        logger.info("请求ID=%s 操作=执行节点开始 节点ID=%s 节点名称=%s 节点类型=%s", request_id_context.get(), node.id, node.name or node.id, node.type)

        node_input = self.read_input(state)

        logger.debug("请求ID=%s 节点ID=%s 输入=%r", request_id_context.get(), node.id, node_input)

        # self.execute 会调用实际子类的方法，例如 LlmNode.execute。
        node_output = self.execute(node_input)

        logger.debug("请求ID=%s 节点ID=%s 输出=%r", request_id_context.get(), node.id, node_output)

        logger.info("请求ID=%s 操作=执行节点完成 节点ID=%s 节点名称=%s", request_id_context.get(), node.id, node.name or node.id)

        return {"node_outputs": {node.id: node_output}}

    # ---------- 读取一个上游的输出
    def read_input(self, state: WorkflowState) -> Any:
        """普通节点接收一个上游；多路数据先经过收敛节点。"""
        if len(self.source_ids) != 1:
            raise BusinessError("当前节点需要一个上游，多路输入请先连接收敛节点")
        return state.node_outputs[self.source_ids[0]]

    # ---------- 由具体节点实现业务
    def execute(self, node_input: Any) -> Any:
        """子类负责处理 node_input 并返回输出，不在这里调用后续节点。"""
        raise NotImplementedError("具体节点需要实现 execute 方法")
