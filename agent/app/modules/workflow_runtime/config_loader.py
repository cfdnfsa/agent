"""运行模块的配置加载入口：读取已有流程与模型，准备好后再交给执行器。"""

import json
from http import HTTPStatus

from sqlalchemy.orm import Session

from app.core.errors.exceptions import BusinessError
from app.modules.model_config.repository import ModelConfigRepository
from app.modules.workflow_config.repository import WorkflowConfigRepository
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_runtime.data.workflow_definition import WorkflowDefinition
from app.modules.workflow_runtime.data.workflow_edge import WorkflowEdge
from app.modules.workflow_runtime.data.workflow_runtime_config import WorkflowRuntimeConfig


# ---------- 将保存的流程文本读取为明确的数据对象
def parse_workflow_definition(definition_text: str) -> WorkflowDefinition:
    """只在加载入口解析 JSON，固定字段转成对象，不增加业务校验或改写数据库原文。

    Args:
        definition_text: workflow_definition 中保存的 JSON 文本。

    Returns:
        包含节点对象和连线对象的流程；坐标和暂未使用的扩展字段保留在数据库原文中。
    """
    definition_data = json.loads(definition_text)

    nodes: list[WorkflowNode] = []
    for node_data in definition_data["nodes"]:
        nodes.append(WorkflowNode.from_dict(node_data))

    edges: list[WorkflowEdge] = []
    for edge_data in definition_data["edges"]:
        edges.append(WorkflowEdge.from_dict(edge_data))

    return WorkflowDefinition(nodes=nodes, edges=edges)


# ---------- 加载本次流程运行需要的配置
def load_runtime_config(db_session: Session, workflow_id: int) -> WorkflowRuntimeConfig:
    """统一读取流程定义和模型实体，返回前结束查询事务。

    Args:
        db_session: 当前请求注入的数据库会话，沿用已有连接池，不创建新会话。
        workflow_id: 要运行的流程主键，不存在时抛出公共业务异常。

    Returns:
        一个运行配置对象，通过 .workflow 和 .model_configs 查看明确的字段。
        模型包含调用需要的 Key，仅交给执行器使用，不作为接口配置响应返回。
    """
    with db_session.begin():
        workflow_config = WorkflowConfigRepository(db_session).get_by_id(workflow_id)
        if workflow_config is None:
            raise BusinessError("流程配置不存在", HTTPStatus.NOT_FOUND)

        # 数据库存的是普通文本；只在运行前解析，不改写已保存的定义。
        workflow_definition = parse_workflow_definition(workflow_config.workflow_definition)

        model_id_set: set[int] = set()
        for node in workflow_definition.nodes:
            # 先保存到局部变量，排除 None 后，IDE 能明确识别这里是 int。
            model_id = node.config.model_config_id
            if node.type == "llm" and model_id is not None:
                model_id_set.add(model_id)

        # 引用相同模型的多个节点只查一次，保留原实体，不额外转换 DTO。
        models = ModelConfigRepository(db_session).list_by_ids(list(model_id_set), include_api_key=True)
        model_configs = {
            model.id: model for model in models
        }

    # expire_on_commit=False 保留已加载字段；等待模型时不持续占用数据库连接。
    # 后续需要缓存时，在这个入口集中处理配置读取；当前直接查询数据库。
    return WorkflowRuntimeConfig(workflow=workflow_definition, model_configs=model_configs)
