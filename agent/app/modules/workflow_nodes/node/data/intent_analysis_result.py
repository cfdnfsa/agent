"""意图分析的固定结果：一个对象中包含多项待处理任务。"""

from pydantic import BaseModel, Field

from app.modules.workflow_nodes.node.data.intent_task import IntentTask


class IntentAnalysisResult(BaseModel):
    """意图分析节点的业务结果，保存在 NodeOutput.value 中。

    Attributes:
        tasks: 拆分后的任务列表，通过 result.tasks、task.type、task.question 读取。
            列表可以为空；后续是否执行、执行什么由任务分发能力决定。
    """

    tasks: list[IntentTask] = Field(description="本次需求拆分出的待处理任务列表")
