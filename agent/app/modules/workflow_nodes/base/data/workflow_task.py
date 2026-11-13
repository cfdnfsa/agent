"""运行时任务：由服务端为意图分析结果分配ID，不要求模型生成标识。"""

from dataclasses import dataclass


@dataclass
class WorkflowTask:
    """本次请求中要独立执行的一项任务，不保存到流程定义或数据库。

    Attributes:
        task_id: 服务端生成的唯一标识；同类型、同问题的任务也有不同ID。
        type: 意图分析给出的 database、knowledge、chat 或 unsupported，供后续分发选路。
        question: 当前任务的具体问题，与原始用户问题分开保存。
    """

    task_id: str
    type: str
    question: str
