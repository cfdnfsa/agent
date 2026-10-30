"""流程运行状态：保存本次输入和各节点输出，合并规则与状态对象一起维护。"""

from dataclasses import Field, dataclass, field
from typing import TYPE_CHECKING, Annotated, Any, ClassVar

from app.modules.workflow_nodes.base.data.node_output import NodeOutput
from app.modules.workflow_nodes.base.data.workflow_input import WorkflowInput


# ---------- 合并各节点独立产生的输出
def merge_node_outputs(current: dict[str, NodeOutput], updates: dict[str, NodeOutput]) -> dict[str, NodeOutput]:
    """按节点ID合并本次更新，避免同一步执行的分支相互覆盖。

    这是图状态的存储规则；收敛节点另行收集上游数据，等待由 LangGraph 连线负责。

    Args:
        current: 图状态中已经保存的节点输出。
        updates: 当前节点新产生的输出，只包含它自己的节点ID。
    """
    return {**current, **updates}


@dataclass
class WorkflowState:
    """每次请求独立创建的图运行状态，不写回配置或数据库。

    Attributes:
        inputs: 本次运行输入，通过 inputs.text 读取文字、inputs.user_id 读取预留用户ID。
        node_outputs: 按节点ID保存全部已执行的 NodeOutput，value 为本节点结果。
            节点按 input_scope 读取自己的上游结果，不直接使用整个 Map。
    """

    if TYPE_CHECKING:
        # dataclass 会自动生成此属性；显式声明，帮助 PyCharm 匹配 LangGraph 的类型约束。
        # 仅供类型检查，运行时不加入注解，避免 LangGraph 将它误当成新的状态字段。
        __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

    inputs: WorkflowInput

    # Annotated 告诉 LangGraph：并行更新此字段时，调用上面的合并函数。
    node_outputs: Annotated[dict[str, NodeOutput], merge_node_outputs] = field(default_factory=dict)
