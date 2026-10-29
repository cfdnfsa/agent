"""返回节点：原样输出上游数据，由运行模块选作接口返回内容。"""

from typing import Any

from app.modules.workflow_nodes.base.base_node import BaseNode


class ReturnNode(BaseNode):
    """一个流程只有一个返回节点，接收一个上游，不能连接下游。"""

    # ---------- 输出本次流程需要返回的数据
    def execute(self, node_input: Any) -> Any:
        """原样保留上游的数据类型和内容，其他分支的结果不混入此处。

        Args:
            node_input: 一个上游的输出；需要返回多路结果时，先使用收敛节点。

        Returns:
            本次接口返回的业务数据；图中其他分支仍按正常调度完成。
        """
        return node_input
