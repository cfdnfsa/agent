"""大模型节点资源：集中保存准备阶段读取的配置实体。"""

from dataclasses import dataclass

from app.modules.model_config.entity import ModelConfig
from app.modules.prompt_config.entity import PromptConfig


@dataclass
class LlmNodeResources:
    """一个大模型节点需要的资源，由 factory 组装后交给节点。

    直接保存已有实体，内部只读；每次运行的输入和输出仍放在 WorkflowState 中。

    Attributes:
        model_config: 必需的模型配置实体，含调用凭证，仅供内部使用。
        prompt_config: 可选提示词实体，未选择时为 None，正文原样使用。
    """

    model_config: ModelConfig
    prompt_config: PromptConfig | None = None
