"""节点配置对象：保存具体节点运行需要的配置字段。"""

from dataclasses import dataclass


@dataclass
class WorkflowNodeConfig:
    """节点自己的配置，按已有 JSON 字段读取。

    Attributes:
        model_config_id: 大模型节点选中的模型配置主键；其他节点无需填写。
    """

    model_config_id: int | None = None
