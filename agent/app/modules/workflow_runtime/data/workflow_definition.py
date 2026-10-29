"""解析后的流程定义：通过节点与连线描述流程结构。"""

from dataclasses import dataclass

from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_runtime.data.workflow_edge import WorkflowEdge


@dataclass
class WorkflowDefinition:
    """已解析的流程结构，画布坐标等原文信息仍由配置模块原样保存。

    这是本项目前后端约定的流程保存格式。数据库 workflow_definition 字段保存
    JSON 文本；运行时先用 json.loads 读取为字典，再由 parse_workflow_definition
    创建当前对象以及其中的节点、连线对象。

    Attributes:
        start_node_id: 唯一开始节点ID；草稿未添加开始节点时为 None，运行时必须有值。
        return_node_id: 唯一返回节点ID；草稿未添加返回节点时为 None，运行时必须有值。
        nodes: 节点列表，每个节点包含 id、type、config，可用 name 指定显示名称。
        edges: 连线列表，source 为起点ID，target 为终点ID，执行顺序由连线决定。

    Examples:
        最小流程“开始 → 返回”对应的 JSON 文本：

        {
            "start_node_id": "start_1",
            "return_node_id": "return_1",
            "nodes": [
                {"id": "start_1", "type": "start", "config": {}},
                {"id": "return_1", "type": "return", "config": {}}
            ],
            "edges": [
                {"id": "edge_1", "source": "start_1", "target": "return_1"}
            ]
        }

    节点还可保存 position（画布坐标）等扩展字段；当前运行对象不读取坐标，
    这些信息保留在数据库原始 JSON 中。本次测试输入和运行结果不属于流程定义。
    """

    start_node_id: str | None
    return_node_id: str | None
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
