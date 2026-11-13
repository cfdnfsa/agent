"""单项任务结果：主流程只汇总最终数据，不混入任务内部节点的运行记录。"""

from dataclasses import dataclass
from typing import Any


@dataclass
class TaskResult:
    """一项任务成功完成后的业务结果，允许文字、对象或列表。

    Attributes:
        task_id: 对应 WorkflowTask.task_id，不能用节点ID代替。
        value: 任务返回节点的业务数据；不包含完整图状态或原始模型消息。
    """

    task_id: str
    value: Any
