"""意图分析拆出的单个任务，后续任务分发使用此结构。"""

from typing import Literal

from pydantic import BaseModel, Field


class IntentTask(BaseModel):
    """模型识别出的一个待处理任务，不代表已经执行。

    使用 Pydantic 是为了直接交给 LangChain 输出解析器，避免手写 JSON 到对象的转换。

    Attributes:
        type: database 查询业务数据，knowledge 检索知识资料，chat 普通问答，
            unsupported 表示当前不支持的操作，例如新增、修改或删除业务数据。
        question: 这项任务的具体需求，保留用户给出的对象、时间等条件，不补造信息。
    """

    type: Literal["database", "knowledge", "chat", "unsupported"] = Field(description="任务类型")
    question: str = Field(description="当前任务要处理的具体问题，不是执行结果")
