"""流程运行组织：总入口按顺序调用小方法，具体步骤仍放在本文件中。

查找唯一入口和返回节点 → 创建业务节点 → 找出全部业务末端 → 执行图 → 取出返回节点数据
"""

from typing import Any

from app.core.errors.exceptions import BusinessError
from app.infrastructure.ai.langgraph.engine import run_graph
from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_input import WorkflowInput
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState
from app.modules.workflow_nodes.factory import create_node
from app.modules.workflow_runtime.data.workflow_definition import WorkflowDefinition
from app.modules.workflow_runtime.data.workflow_result import WorkflowResult
from app.modules.workflow_runtime.data.workflow_runtime_config import WorkflowRuntimeConfig


# ---------- 组织本次流程运行
def run_workflow(runtime_config: WorkflowRuntimeConfig, workflow_input: WorkflowInput) -> WorkflowResult:
    """准备节点对象、交给图引擎运行，只返回唯一返回节点的数据。

    Args:
        runtime_config: 准备好的流程和模型配置，执行时不再查库。
        workflow_input: 本次输入，通过 .payload 取得实际业务内容。

    Returns:
        返回节点的输出，其他独立末端只参与执行。
    """

    # 先检查唯一入口，非法配置不会进入节点创建和图执行。

    # 开始节点
    start_node_id = find_start_node_id(runtime_config.workflow.nodes)
    # 返回节点
    return_node_id = find_return_node_id(runtime_config.workflow)

    runtime_nodes = create_runtime_nodes(runtime_config)
    terminal_node_ids = find_terminal_node_ids(runtime_config.workflow)

    # 每次运行创建独立状态，具体连线和执行交给 LangGraph 引擎。
    node_outputs = run_graph(
        nodes=runtime_nodes,
        start_node_id=start_node_id,
        terminal_node_ids=terminal_node_ids,
        initial_state=WorkflowState(inputs=workflow_input),
    )
    return build_workflow_result(node_outputs, return_node_id)


# ---------- 查找唯一的开始节点
def find_start_node_id(node_definitions: list[WorkflowNode]) -> str:
    """找到业务入口，缺少或存在多个开始节点时抛出公共业务异常。

    Args:
        node_definitions: 已从保存的流程中解析出的节点定义，当前只遍历内存数据。

    Returns:
        唯一开始节点的ID，用于连接 LangGraph 的 START。
    """
    start_node_id: str | None = None
    for definition in node_definitions:
        if definition.type == "start":
            if start_node_id is not None:
                raise BusinessError("流程只能有一个开始节点")
            start_node_id = definition.id
    if start_node_id is None:
        raise BusinessError("流程需要一个开始节点")
    return start_node_id


# ---------- 查找唯一且没有下游的返回节点
def find_return_node_id(workflow_definition: WorkflowDefinition) -> str:
    """确认响应来自一个明确的返回节点，该节点只能作为分支终点。

    Args:
        workflow_definition: 已解析的流程，用节点查找返回类型，用连线检查下游。

    Returns:
        唯一返回节点的ID；缺少、重复、上游不是一个或连接下游时抛出业务异常。
    """
    return_node_id: str | None = None

    for definition in workflow_definition.nodes:
        if definition.type == "return":
            if return_node_id is not None:
                raise BusinessError("流程只能有一个返回节点")
            return_node_id = definition.id

    if return_node_id is None:
        raise BusinessError("流程需要一个返回节点")

    source_count = 0
    for edge in workflow_definition.edges:
        if edge.source == return_node_id:
            raise BusinessError("返回节点不能连接下游节点")
        if edge.target == return_node_id:
            source_count += 1
    if source_count != 1:
        raise BusinessError("返回节点需要连接一个上游，多路输入请先连接收敛节点")
    return return_node_id


# ---------- 按流程配置创建业务节点
def create_runtime_nodes(runtime_config: WorkflowRuntimeConfig) -> list[BaseNode]:
    """整理上游关系，并为每份节点定义创建对应的业务节点对象。

    Args:
        runtime_config: 已加载的流程和模型实体，不在这里查询数据库。

    Returns:
        配置就绪的节点对象；此时只创建对象，还未执行节点的 run 方法。
    """
    node_definitions = runtime_config.workflow.nodes

    # 每条连线的 target 是接收方，source 是它需要读取结果的上游。
    # 先给所有节点准备空列表
    incoming: dict[str, list[str]] = {node.id: [] for node in node_definitions}

    for edge in runtime_config.workflow.edges:
        incoming[edge.target].append(edge.source)

    runtime_nodes: list[BaseNode] = []
    for definition in node_definitions:
        runtime_nodes.append(create_node(definition, incoming[definition.id], runtime_config.model_configs))
    return runtime_nodes


# ---------- 查找没有下游的末端节点
def find_terminal_node_ids(workflow_definition: WorkflowDefinition) -> list[str]:
    """根据连线找出末端，节点在列表中的位置不决定它是不是末端。

    Args:
        workflow_definition: 已解析的节点和连线对象。

    Returns:
        所有没有下游的节点ID，保留定义中的节点顺序，可以有多个。
    """
    # 出现在 source 中，说明这个节点还有向外的连线。
    has_successor = {edge.source for edge in workflow_definition.edges}
    terminal_node_ids: list[str] = []
    for definition in workflow_definition.nodes:
        if definition.id not in has_successor:
            terminal_node_ids.append(definition.id)
    return terminal_node_ids


# ---------- 读取返回节点输出并包装运行结果
def build_workflow_result(node_outputs: dict[str, Any], return_node_id: str) -> WorkflowResult:
    """从全部节点输出中，只读取本次选定的返回节点。

    Args:
        node_outputs: 图引擎返回的各节点输出，按节点ID索引，业务内容允许变化。
        return_node_id: 唯一返回节点ID，不再自动聚合其他末端的输出。

    Returns:
        返回节点原样输出的业务内容；未执行到该节点时抛出业务异常。
    """
    if return_node_id not in node_outputs:
        raise BusinessError("返回节点未执行，请检查流程连线")
    return WorkflowResult(payload=node_outputs[return_node_id])
