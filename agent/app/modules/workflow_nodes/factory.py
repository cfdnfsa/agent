"""节点创建入口：按定义选择具体节点，模型和提示词配置通过各自缓存读取。"""

from http import HTTPStatus

from app.core.errors.exceptions import BusinessError
from app.modules.model_config.cache import get_model_config
from app.modules.model_config.entity import ModelConfig
from app.modules.prompt_config.cache import get_prompt_config
from app.modules.prompt_config.entity import PromptConfig
from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_nodes.node.data.llm_node_resources import LlmNodeResources
from app.modules.workflow_nodes.node.llm_node import LlmNode
from app.modules.workflow_nodes.node.merge_node import MergeNode
from app.modules.workflow_nodes.node.return_node import ReturnNode
from app.modules.workflow_nodes.node.start_node import StartNode


# ---------- 按配置创建对应的节点对象
def create_node(definition: WorkflowNode, source_ids: list[str]) -> BaseNode:
    """只选择节点类型，需要准备配置的节点交给对应创建方法。

    Args:
        definition: 已保存的节点定义，运行时保留其原ID。
        source_ids: 由流程连线整理出的直接上游ID。

    Returns:
        配置就绪的节点对象；缓存未命中时的查询在这里完成，执行 run 前会话已关闭。
    """
    if definition.type == "start":
        return StartNode(definition, source_ids)
    if definition.type == "merge":
        return MergeNode(definition, source_ids)
    if definition.type == "return":
        return ReturnNode(definition, source_ids)
    if definition.type == "llm":
        return create_llm_node(definition, source_ids)
    raise BusinessError(f"尚不支持的流程节点类型：{definition.type}")


# ---------- 准备配置并创建大模型节点
def create_llm_node(definition: WorkflowNode, source_ids: list[str]) -> LlmNode:
    """先读取模型和可选提示词，再通过资源对象交给节点，执行时不再查库。

    Args:
        definition: 大模型节点定义，config 保存所选配置的ID。
        source_ids: 当前节点直接上游的ID列表。

    Returns:
        已准备好调用配置的大模型节点。
    """
    model_config = load_model_config(definition.config.model_config_id)
    prompt_config = load_prompt_config(definition.config.prompt_config_id)
    resources = LlmNodeResources(model_config=model_config, prompt_config=prompt_config)
    return LlmNode(definition, source_ids, resources)


# ---------- 读取节点必需的模型配置
def load_model_config(model_id: int | None) -> ModelConfig:
    """通过缓存读取模型；未选择或记录不存在时，沿用原来的 404 错误。

    Args:
        model_id: 节点选择的模型配置ID，未选择时为 None。

    Returns:
        含调用凭证的模型实体，仅供内部只读使用。
    """
    if model_id is None:
        raise BusinessError("流程引用的模型配置不存在", HTTPStatus.NOT_FOUND)

    model_config = get_model_config(model_id)
    if model_config is None:
        raise BusinessError("流程引用的模型配置不存在", HTTPStatus.NOT_FOUND)
    return model_config


# ---------- 读取节点可选的提示词配置
def load_prompt_config(prompt_id: int | None) -> PromptConfig | None:
    """未选择时不读取缓存；选择后找不到记录时，沿用原来的 404 错误。

    Args:
        prompt_id: 节点选择的提示词配置ID，未选择时为 None。

    Returns:
        完整提示词实体；未选择时返回 None。
    """
    if prompt_id is None:
        return None

    prompt_config = get_prompt_config(prompt_id)
    if prompt_config is None:
        raise BusinessError("流程引用的提示词配置不存在", HTTPStatus.NOT_FOUND)
    return prompt_config
