"""节点配置对象：保存具体节点运行需要的配置字段。"""

from dataclasses import dataclass


@dataclass
class WorkflowNodeConfig:
    """节点自己的配置，按已有 JSON 字段读取。

    Attributes:
        model_config_id: 大模型节点选中的模型配置主键；其他节点无需填写。
        prompt_config_id: 可选提示词配置主键，未选择时不添加系统消息。
        input_scope: 当前节点读取哪些结果；all_upstream 读取全部上游，
            direct_upstream 仅读取直接上游。开始、返回节点无需配置。
    """

    model_config_id: int | None = None
    prompt_config_id: int | None = None
    input_scope: str = "all_upstream"
