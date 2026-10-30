"""节点公共文字处理：需要文字输入的节点按需调用，其他节点保留原数据类型。"""

import json
from typing import Any


# ---------- 将业务数据转换成可读文字
def convert_input_to_text(node_input: Any) -> str:
    """文字原样保留，对象或列表转成 JSON 文字，保留中文便于模型阅读和排查。

    Args:
        node_input: 需要转换的业务内容，例如 NodeContext.results。

    Returns:
        输入文字；JSON 无法序列化时沿用现有公共异常处理。
    """
    if isinstance(node_input, str):
        return node_input
    return json.dumps(node_input, ensure_ascii=False)
