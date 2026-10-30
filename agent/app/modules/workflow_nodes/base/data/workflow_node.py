"""保存的节点定义：描述节点身份、类型、配置和显示名称。"""

from dataclasses import dataclass
from typing import Any

from app.modules.workflow_nodes.base.data.workflow_node_config import WorkflowNodeConfig


@dataclass
class WorkflowNode:
    """流程中的一个节点。

    Attributes:
        id: 流程内唯一的节点ID，连线和执行定位使用它。
        type: 节点类型，当前为 start、llm、merge 或 return。
        config: 当前节点的模型、可选提示词和输入范围。
        name: 用户填写的显示名称，未填写时日志使用 ID。

    Examples:
        一个选择了模型配置的大模型节点，其原始 JSON 数据如下：

        {
            "id": "llm_1",
            "type": "llm",
            "config": {"model_config_id": 1, "prompt_config_id": 2, "input_scope": "all_upstream"},
            "name": "生成回答"
        }

        from_dict 读取后，通过 node.config.model_config_id、prompt_config_id 取得所选配置ID。
        提示词可省略或为 null；input_scope 默认读取全部上游，direct_upstream 表示直接上游。
        开始、收敛、返回节点的 config 可以是空对象 {}。
    """

    id: str
    type: str
    config: WorkflowNodeConfig
    name: str | None = None

    # ---------- 从字典创建节点定义
    @classmethod
    def from_dict(cls, node_data: dict[str, Any]) -> "WorkflowNode":
        """集中读取节点字段，创建定义及配置对象，不额外校验或改写输入。

        Args:
            node_data: 原始节点 JSON 字典，包含 id、type、config，可选 name。

        Returns:
            节点定义对象，分别读取所选模型和可选提示词，未配置字段为 None。
        """
        # cls 代表当前类，cls(...) 创建实例；这里只组装定义，不执行业务节点。
        return cls(
            id=node_data["id"],
            type=node_data["type"],
            config=WorkflowNodeConfig(
                model_config_id=node_data["config"].get("model_config_id"),
                prompt_config_id=node_data["config"].get("prompt_config_id"),
                input_scope=node_data["config"].get("input_scope", "all_upstream"),
            ),
            name=node_data.get("name"),
        )
