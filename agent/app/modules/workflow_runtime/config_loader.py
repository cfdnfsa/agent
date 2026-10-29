"""流程定义加载入口：读取保存的流程文本，结束查询事务后解析成对象。"""

import json
from http import HTTPStatus

from sqlalchemy.orm import Session

from app.core.errors.exceptions import BusinessError
from app.modules.workflow_config.repository import WorkflowConfigRepository
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_runtime.data.workflow_definition import WorkflowDefinition
from app.modules.workflow_runtime.data.workflow_edge import WorkflowEdge


# ---------- 将保存的流程文本读取为明确的数据对象
def parse_workflow_definition(definition_text: str) -> WorkflowDefinition:
    """只在加载入口解析 JSON，固定字段转成对象，不增加业务校验或改写数据库原文。

    Args:
        definition_text: workflow_definition 中保存的 JSON 文本。

    Returns:
        包含开始、返回节点ID及节点和连线的流程；扩展字段保留在数据库原文中。
    """
    definition_data = json.loads(definition_text)

    nodes: list[WorkflowNode] = []
    for node_data in definition_data["nodes"]:
        nodes.append(WorkflowNode.from_dict(node_data))

    edges: list[WorkflowEdge] = []
    for edge_data in definition_data["edges"]:
        edges.append(WorkflowEdge.from_dict(edge_data))

    return WorkflowDefinition(
        start_node_id=definition_data["start_node_id"],
        return_node_id=definition_data["return_node_id"],
        nodes=nodes,
        edges=edges,
    )


# ---------- 加载本次运行的流程定义
def load_workflow_definition(db_session: Session, workflow_id: int) -> WorkflowDefinition:
    """读取流程文本并结束查询事务，直接返回流程定义对象。

    Args:
        db_session: 当前请求注入的数据库会话，沿用已有连接池，不创建新会话。
        workflow_id: 要运行的流程主键，不存在时抛出公共业务异常。

    Returns:
        包含节点与连线的流程定义；模型配置由节点创建阶段通过统一缓存入口读取。
    """
    with db_session.begin():
        workflow_config = WorkflowConfigRepository(db_session).get_by_id(workflow_id)
        if workflow_config is None:
            raise BusinessError("流程配置不存在", HTTPStatus.NOT_FOUND)

        definition_text = workflow_config.workflow_definition

    # 先归还查询连接，再解析文本；不改写数据库中的定义，也不在这里组装模型 Map。
    return parse_workflow_definition(definition_text)
