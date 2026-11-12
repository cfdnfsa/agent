"""节点配置对象：保存具体节点运行需要的配置字段。"""

from dataclasses import dataclass, field
from typing import Any

from app.modules.workflow_nodes.base.data.prompt_variable import PromptVariable


@dataclass
class WorkflowNodeConfig:
    """节点自己的配置，按已有 JSON 字段读取。

    Attributes:
        model_config_id: 普通大模型、意图分析节点选中的模型配置主键。
        prompt_config_id: 可选提示词主键；普通 LLM 用作任务说明，意图分析用作业务补充。
        input_scope: 当前节点读取哪些结果；all_upstream 读取全部上游，
            direct_upstream 仅读取直接上游。开始、返回节点无需配置。
        prompt_variables: 提示词变量名与来源的对应关系，只保存配置，不保存实际结果。
    """

    model_config_id: int | None = None
    prompt_config_id: int | None = None
    input_scope: str = "all_upstream"
    prompt_variables: dict[str, PromptVariable] = field(default_factory=dict)

    # ---------- 从保存的字典创建节点配置
    @classmethod
    def from_dict(cls, config_data: dict[str, Any]) -> "WorkflowNodeConfig":
        """集中读取模型、提示词、输入范围和变量来源，保留已有默认值。"""
        variables: dict[str, PromptVariable] = {}
        for variable_name, binding_data in config_data.get("prompt_variables", {}).items():
            variables[variable_name] = PromptVariable(**binding_data)
        return cls(
            model_config_id=config_data.get("model_config_id"),
            prompt_config_id=config_data.get("prompt_config_id"),
            input_scope=config_data.get("input_scope", "all_upstream"),
            prompt_variables=variables,
        )
