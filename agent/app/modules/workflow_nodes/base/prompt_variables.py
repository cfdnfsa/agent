"""公共提示词变量处理：只替换命名占位符，保留普通 JSON 花括号和其他正文。"""

import re

from app.core.errors.exceptions import BusinessError
from app.modules.workflow_nodes.base.data.node_context import NodeContext
from app.modules.workflow_nodes.base.data.prompt_variable import PromptVariable
from app.modules.workflow_nodes.base.text import convert_input_to_text


PROMPT_VARIABLE_PATTERN = re.compile(r"(?<!\{)\{([^\W\d]\w*)\}(?!\})")


# ---------- 读取正文中出现的变量名
def get_prompt_variable_names(prompt_text: str) -> list[str]:
    """只识别 {变量名}，相同变量保留一次；JSON 对象和双花括号正文保持原样。"""
    variable_names: list[str] = []
    for match in PROMPT_VARIABLE_PATTERN.finditer(prompt_text):
        variable_name = match.group(1)
        if variable_name not in variable_names:
            variable_names.append(variable_name)
    return variable_names


# ---------- 按当前节点的来源配置替换提示词变量
def render_prompt_variables(
    prompt_text: str, variables: dict[str, PromptVariable], node_input: NodeContext,
) -> str:
    """单次替换所选提示词，不再次解释替换值中的花括号。

    Args:
        prompt_text: 提示词库中的原始正文，不改写数据库内容。
        variables: 当前节点配置的变量来源；内置 question、upstream 无需额外绑定。
        node_input: 本次问题与已经按 input_scope 选出的上游结果。

    Returns:
        替换后的文字；缺少绑定或来源不在输入范围时明确报错。
    """
    values: dict[str, str] = {}
    for variable_name in get_prompt_variable_names(prompt_text):
        if variable_name == "question":
            values[variable_name] = node_input.question
            continue
        if variable_name == "upstream":
            values[variable_name] = convert_input_to_text(node_input.results)
            continue

        binding = variables.get(variable_name)
        if binding is None:
            raise BusinessError(f"提示词变量 {variable_name} 尚未选择来源")
        if binding.source == "question":
            values[variable_name] = node_input.question
        elif binding.source == "upstream":
            values[variable_name] = convert_input_to_text(node_input.results)
        elif binding.source == "node":
            node_id = binding.node_id
            if node_id is None or node_id not in node_input.results:
                raise BusinessError(f"提示词变量 {variable_name} 引用的节点不在当前输入范围")
            values[variable_name] = convert_input_to_text(node_input.results[node_id])
        else:
            raise BusinessError(f"提示词变量 {variable_name} 的来源不支持")

    # ---------- 替换当前匹配到的占位符
    def replace_variable(match: re.Match[str]) -> str:
        """回调只读取已经准备好的值，不递归处理替换内容。"""
        return values[match.group(1)]

    return PROMPT_VARIABLE_PATTERN.sub(replace_variable, prompt_text)
