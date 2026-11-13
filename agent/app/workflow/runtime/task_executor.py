"""任务运行基础：分配任务ID，用独立状态复用现有节点和 LangGraph 引擎。

这里不决定任务走哪个分支。后续分发节点选定节点组后调用 run_task，
只把 TaskResult 按任务ID交回主流程，不合并任务内部的 node_outputs。
"""

from uuid import uuid4

from app.core.app_logging import logger, request_id_context
from app.workflow.data.task.task_result import TaskResult
from app.workflow.data.io.workflow_input import WorkflowInput
from app.workflow.data.execution.workflow_state import WorkflowState
from app.workflow.data.task.workflow_task import WorkflowTask
from app.workflow.nodes.node.llm.data.intent_analysis_result import IntentAnalysisResult
from app.workflow.data.definition.workflow_definition import WorkflowDefinition
from app.workflow.runtime.executor import execute_workflow


# ---------- 为意图分析拆出的任务分配运行标识
def create_workflow_tasks(intent_result: IntentAnalysisResult) -> list[WorkflowTask]:
    """保留模型识别的类型与问题，由程序补充唯一任务ID。

    Args:
        intent_result: 已经由框架解析的意图结果，不修改其中的 IntentTask。

    Returns:
        按分析结果顺序创建的任务列表；重复类型或问题也保留，空列表仍返回空列表。
    """
    workflow_tasks: list[WorkflowTask] = []
    for intent_task in intent_result.tasks:
        workflow_task = WorkflowTask(task_id=uuid4().hex, type=intent_task.type, question=intent_task.question)
        workflow_tasks.append(workflow_task)
    return workflow_tasks


# ---------- 使用独立图状态执行单项任务
def run_task(
        workflow_definition: WorkflowDefinition,
        workflow_input: WorkflowInput,
        task: WorkflowTask,
) -> TaskResult:
    """用独立状态执行节点组，配置读取仍走现有缓存入口。

    Args:
        workflow_definition: 调用方选定的任务节点组，仍含一个开始和一个返回节点。
        workflow_input: 原始用户问题与用户ID；复制后保存，不能用任务问题覆盖原问题。
        task: 当前任务及其唯一ID，开始节点使用 task.question 作为本任务输入。

    Returns:
        任务ID与最终数据。失败继续抛出异常，不伪装成 None 或成功结果。

    不修改调用方的输入和结果。模型、提示词缓存未命中时仍会用短会话查询，
    查询在任务图执行前结束，节点运行时不持有数据库会话。
    """
    # 每次都创建输入与状态对象，node_outputs、task_results 由 default_factory 各自创建。
    # 相同节点ID可以在多个任务里重复使用，因为它们不向同一个字典写入。
    task_input = WorkflowInput(text=workflow_input.text, user_id=workflow_input.user_id)
    task_state = WorkflowState(inputs=task_input, task=task)

    logger.info("请求ID=%s 操作=执行任务开始 任务ID=%s 任务类型=%s", request_id_context.get(), task.task_id, task.type)

    try:
        # 在主图节点中调用时，这次 LangGraph 执行就是任务子图；仍由框架调度内部节点。
        workflow_result = execute_workflow(workflow_definition, task_state)
    except Exception:

        logger.error("请求ID=%s 操作=执行任务失败 任务ID=%s 任务类型=%s", request_id_context.get(), task.task_id, task.type)

        raise

    logger.info("请求ID=%s 操作=执行任务完成 任务ID=%s 任务类型=%s", request_id_context.get(), task.task_id, task.type)

    return TaskResult(task_id=task.task_id, value=workflow_result.payload)
