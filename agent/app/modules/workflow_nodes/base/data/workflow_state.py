"""图运行状态：保存原始输入、当前任务和结果，合并规则与状态对象一起维护。"""

from dataclasses import Field, dataclass, field
from typing import TYPE_CHECKING, Annotated, Any, ClassVar

from app.modules.workflow_nodes.base.data.node_output import NodeOutput
from app.modules.workflow_nodes.base.data.task_result import TaskResult
from app.modules.workflow_nodes.base.data.workflow_input import WorkflowInput
from app.modules.workflow_nodes.base.data.workflow_task import WorkflowTask


# ---------- 合并各节点独立产生的输出
def merge_node_outputs(current: dict[str, NodeOutput], updates: dict[str, NodeOutput]) -> dict[str, NodeOutput]:
    """按节点ID合并本次更新，避免同一步执行的分支相互覆盖。

    这是图状态的存储规则；收敛节点另行收集上游数据，等待由 LangGraph 连线负责。

    Args:
        current: 图状态中已经保存的节点输出。
        updates: 当前节点新产生的输出，只包含它自己的节点ID。
    """
    return {**current, **updates}


# ---------- 按任务ID汇总各任务的最终结果
def merge_task_results(current: dict[str, TaskResult], updates: dict[str, TaskResult]) -> dict[str, TaskResult]:
    """合并并行任务提交的结果；任务内部的 node_outputs 不合并到主流程。

    Args:
        current: 主流程已经收到的任务结果。
        updates: 本次完成的任务结果，以 task_id 为键；相同ID再次提交时使用新结果。

    Returns:
        新的结果字典，不修改传入字典，也不负责调度或等待任务。
    """
    return {**current, **updates}


@dataclass
class WorkflowState:
    """主流程和每项任务分别创建的图状态，不写回配置或数据库。

    Attributes:
        inputs: 原始请求输入；任务执行时仍保留原问题和用户ID，不改成任务问题。
        node_outputs: 按节点ID保存全部已执行的 NodeOutput，value 为本节点结果。
            只属于当前这次图运行，不与其他任务或主流程共享。
        task: 当前任务；主流程为 None，任务开始节点输出 task.question。
        task_results: 主流程按任务ID汇总的最终结果；不保存各任务内部节点记录。
    """

    if TYPE_CHECKING:
        # dataclass 会自动生成此属性；显式声明，帮助 PyCharm 匹配 LangGraph 的类型约束。
        # 仅供类型检查，运行时不加入注解，避免 LangGraph 将它误当成新的状态字段。
        __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

    inputs: WorkflowInput

    # Annotated 告诉 LangGraph：并行更新此字段时，调用上面的合并函数。
    node_outputs: Annotated[dict[str, NodeOutput], merge_node_outputs] = field(default_factory=dict)
    task: WorkflowTask | None = None
    task_results: Annotated[dict[str, TaskResult], merge_task_results] = field(default_factory=dict)
