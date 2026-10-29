"""流程运行结果：只保存选定的最终业务数据。"""

from dataclasses import dataclass
from typing import Any


@dataclass
class WorkflowResult:
    """普通运行返回的数据。

    Attributes:
        payload: 唯一返回节点的输出，其他分支的末端结果不自动混入响应。
    """

    payload: Any
