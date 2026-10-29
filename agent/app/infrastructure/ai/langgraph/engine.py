"""LangGraph 执行入口：注册节点、连接图并执行。

run_workflow 准备业务节点
    ↓
run_graph 创建空图
    ↓
register_nodes 登记执行方法 → connect_edges 建立依赖 → execute_graph 编译并执行
    ↓
run_workflow 从所有节点输出中选择接口返回的数据
"""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_state import WorkflowState


# ---------- 使用 LangGraph 构建并执行流程图
def run_graph(
        nodes: list[BaseNode],
        start_node_id: str,
        terminal_node_ids: list[str],
        initial_state: WorkflowState,
) -> dict[str, Any]:
    """接收已准备的节点对象和状态，返回各节点的输出。

    Args:
        nodes: 已加载配置的节点对象，每个对象保存自身定义和直接上游ID。
        start_node_id: 业务层确认唯一的入口节点ID，由框架 START 触发。
        terminal_node_ids: 业务层识别的末端节点ID，连接框架 END。
        initial_state: 本次请求独立的初始状态，不在引擎中读取数据库。

    Returns:
        按节点ID索引的输出，业务层再选择哪些数据作为接口返回。
    """
    graph = StateGraph(WorkflowState)
    register_nodes(graph, nodes)
    connect_edges(graph, nodes, start_node_id, terminal_node_ids)
    return execute_graph(graph, initial_state)


# ---------- 登记节点及其执行方法
def register_nodes(graph: StateGraph[WorkflowState], nodes: list[BaseNode]) -> None:
    """把节点ID与 run 方法交给框架，此时不执行节点。

    Args:
        graph: 正在组装的图，所有节点和连线都添加到同一个图对象中。
        nodes: 业务层已经创建的节点对象，运行配置已准备好。
    """
    for node in nodes:
        # 交给框架的是方法本身；调度到该节点时才调用 node.run(state)。
        graph.add_node(node.definition.id, node.run)


# ---------- 连接入口、节点依赖和末端
def connect_edges(
        graph: StateGraph[WorkflowState],
        nodes: list[BaseNode],
        start_node_id: str,
        terminal_node_ids: list[str],
) -> None:
    """根据已保存的上游关系连线，执行顺序由连线决定。

    Args:
        graph: 已登记节点的图；先登记节点，再连接它们。
        nodes: 每个节点的 source_ids 保存全部直接上游ID。
        start_node_id: 唯一的开始节点ID，连接框架 START。
        terminal_node_ids: 没有下游的节点ID，可以有多个，分别连接框架 END。
    """
    # 入口：START → 业务开始节点。
    graph.add_edge(START, start_node_id)

    # 业务连线：上游节点 → 当前节点；开始节点没有上游，跳过这一步。
    for node in nodes:
        if node.source_ids:
            # 列表形式表示等待全部上游，固定并行分支的收敛依赖这个规则。
            graph.add_edge(node.source_ids, node.definition.id)

    # 出口：每个业务末端 → END，仍保留多个末端的能力。
    for node_id in terminal_node_ids:
        graph.add_edge(node_id, END)


# ---------- 编译并执行已经连好的图
def execute_graph(graph: StateGraph[WorkflowState], initial_state: WorkflowState) -> dict[str, Any]:
    """把构建好的图准备为可执行对象，再使用本次输入运行。

    Args:
        graph: 已完成节点登记和连线的图。
        initial_state: 本次请求独立的初始状态，包含入口收到的业务数据。

    Returns:
        所有已执行节点的输出，按节点ID索引；接口返回选择仍由业务层决定。
    """
    # compile 准备图；invoke 才真正执行，并等待本次图运行完成。
    compiled_graph = graph.compile()
    completed_state = compiled_graph.invoke(initial_state)
    return completed_state["node_outputs"]
