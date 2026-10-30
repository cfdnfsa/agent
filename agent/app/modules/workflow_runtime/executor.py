"""流程运行组织：总入口按顺序调用小方法，具体步骤仍放在本文件中。

读取已保存的入口和返回ID → 整理关系并创建节点 → 找出全部业务末端 → 执行图 → 取出返回节点数据
"""

from app.core.errors.exceptions import BusinessError
from app.infrastructure.ai.langgraph.engine import run_graph
from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.node_output import NodeOutput
from app.modules.workflow_nodes.base.data.workflow_input import WorkflowInput
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState
from app.modules.workflow_nodes.factory import create_node
from app.modules.workflow_runtime.data.workflow_definition import WorkflowDefinition
from app.modules.workflow_runtime.data.workflow_result import WorkflowResult


# ---------- 组织本次流程运行
def run_workflow(workflow_definition: WorkflowDefinition, workflow_input: WorkflowInput) -> WorkflowResult:
    """准备节点对象、交给图引擎运行，只返回唯一返回节点的数据。

    Args:
        workflow_definition: 已加载的流程定义；节点准备时按需读取模型缓存，再执行图。
        workflow_input: 本次输入，.text 交给开始节点，.user_id 留在状态中供后续节点读取。

    Returns:
        返回节点的输出，其他独立末端只参与执行。
    """

    # 入口和返回位置由流程定义明确指定，不再遍历节点寻找它们。
    start_node_id = workflow_definition.start_node_id
    return_node_id = workflow_definition.return_node_id
    if start_node_id is None:
        raise BusinessError("流程需要指定开始节点")
    if return_node_id is None:
        raise BusinessError("流程需要指定返回节点")

    # 整理上游时一并检查ID引用、节点唯一性和返回节点连线，再创建对象。
    runtime_nodes = create_runtime_nodes(workflow_definition)
    # 其他分支也可能独立结束，所以仍根据连线识别全部末端。
    terminal_node_ids = find_terminal_node_ids(workflow_definition)

    # 每次运行创建独立状态，具体连线和执行交给 LangGraph 引擎。
    node_outputs = run_graph(
        nodes=runtime_nodes,
        start_node_id=start_node_id,
        terminal_node_ids=terminal_node_ids,
        initial_state=WorkflowState(inputs=workflow_input),
    )

    return build_workflow_result(node_outputs, return_node_id)


# ---------- 按流程配置创建业务节点
def create_runtime_nodes(workflow_definition: WorkflowDefinition) -> list[BaseNode]:
    """整理上游时确认开始、返回ID与实际节点一致，再创建业务节点对象。

    Args:
        workflow_definition: 已加载的节点与连线；大模型配置由 factory 通过缓存入口取得。

    Returns:
        配置就绪的节点对象；此时只创建对象，还未执行节点的 run 方法。
    """
    node_definitions = workflow_definition.nodes

    # 准备上游列表的同一轮循环中检查类型和唯一性，不再单独查找开始、返回节点。
    incoming: dict[str, list[str]] = {}
    start_node_count = 0
    return_node_count = 0
    for node in node_definitions:
        incoming[node.id] = []
        if node.type == "start":
            start_node_count += 1
            if node.id != workflow_definition.start_node_id:
                raise BusinessError("start_node_id 必须指向流程中唯一的开始节点")
        if node.type == "return":
            return_node_count += 1
            if node.id != workflow_definition.return_node_id:
                raise BusinessError("return_node_id 必须指向流程中唯一的返回节点")
    if start_node_count != 1:
        raise BusinessError("流程需要且只能有一个开始节点")
    if return_node_count != 1:
        raise BusinessError("流程需要且只能有一个返回节点")

    # target 接收 source 的输出；例如 A → B，会把 A 放入 incoming[B]。
    return_source_count = 0
    for edge in workflow_definition.edges:
        if edge.source == workflow_definition.return_node_id:
            raise BusinessError("返回节点不能连接下游节点")
        if edge.target == workflow_definition.return_node_id:
            return_source_count += 1
        incoming[edge.target].append(edge.source)
    if return_source_count != 1:
        raise BusinessError("返回节点需要连接一个上游，多路输入请先连接收敛节点")

    # 结构确认后再创建对象，避免无效流程提前加载模型配置。
    runtime_nodes: list[BaseNode] = []
    for definition in node_definitions:
        runtime_node = create_node(definition, incoming[definition.id])
        # 输入范围属于使用数据的节点，上游节点不会限制其他节点读取已保存的结果。
        if definition.type in ("llm", "merge") and definition.config.input_scope != "direct_upstream":
            runtime_node.input_ids = find_upstream_node_ids(definition.id, incoming)
        runtime_nodes.append(runtime_node)

    return runtime_nodes


# ---------- 找出当前节点的全部直接和间接上游
def find_upstream_node_ids(node_id: str, incoming: dict[str, list[str]]) -> list[str]:
    """准备节点时沿入边查找依赖，运行中只按得到的ID读取结果。

    Args:
        node_id: 当前节点ID，自身不加入输入范围。
        incoming: 全部节点的直接上游关系，由已保存的连线整理得到。

    Returns:
        去重后的上游ID，不包含无关分支；列表顺序不表示执行顺序。
    """
    upstream_ids: list[str] = []
    # 从直接上游往前找；先标记当前节点，保证输入列表不包含自身。
    pending_ids = incoming[node_id].copy()
    visited_ids = {node_id}
    while pending_ids:
        upstream_id = pending_ids.pop()
        if upstream_id in visited_ids:
            continue
        visited_ids.add(upstream_id)
        upstream_ids.append(upstream_id)
        # 继续检查这个上游的父节点，遇到共同祖先时由 visited_ids 去重。
        pending_ids.extend(incoming[upstream_id])
    return upstream_ids


# ---------- 查找没有下游的末端节点
def find_terminal_node_ids(workflow_definition: WorkflowDefinition) -> list[str]:
    """根据连线找出末端，节点在列表中的位置不决定它是不是末端。

    Args:
        workflow_definition: 已解析的节点和连线对象。

    Returns:
        所有没有下游的节点ID，保留定义中的节点顺序，可以有多个。
    """
    # 出现在 source 中，说明这个节点还有向外的连线。
    has_successor: set[str] = set()
    for edge in workflow_definition.edges:
        has_successor.add(edge.source)

    terminal_node_ids: list[str] = []
    for definition in workflow_definition.nodes:
        if definition.id not in has_successor:
            terminal_node_ids.append(definition.id)
    return terminal_node_ids


# ---------- 读取返回节点输出并包装运行结果
def build_workflow_result(node_outputs: dict[str, NodeOutput], return_node_id: str) -> WorkflowResult:
    """从全部节点输出中，只读取本次选定的返回节点。

    Args:
        node_outputs: 图引擎返回的各节点输出，按节点ID索引，业务内容允许变化。
        return_node_id: 唯一返回节点ID，不再自动聚合其他末端的输出。

    Returns:
        返回节点原样输出的业务内容；未执行到该节点时抛出业务异常。
    """
    if return_node_id not in node_outputs:
        raise BusinessError("返回节点未执行，请检查流程连线")
    return WorkflowResult(payload=node_outputs[return_node_id].value)
