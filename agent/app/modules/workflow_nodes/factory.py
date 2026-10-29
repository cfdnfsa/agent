"""节点创建入口：按定义选择具体节点，大模型配置通过统一缓存入口读取。"""

from http import HTTPStatus

from app.core.errors.exceptions import BusinessError
from app.modules.model_config.cache import get_model_config
from app.modules.workflow_nodes.base.base_node import BaseNode
from app.modules.workflow_nodes.base.data.workflow_node import WorkflowNode
from app.modules.workflow_nodes.node.llm_node import LlmNode
from app.modules.workflow_nodes.node.merge_node import MergeNode
from app.modules.workflow_nodes.node.return_node import ReturnNode
from app.modules.workflow_nodes.node.start_node import StartNode


# ---------- 按配置创建对应的节点对象
def create_node(definition: WorkflowNode, source_ids: list[str]) -> BaseNode:
    """一个普通函数完成类型选择，不增加工厂类或注册体系。

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
        model_id = definition.config.model_config_id
        if model_id is None:
            model_config = None
        else:
            model_config = get_model_config(model_id)
        if model_config is None:
            raise BusinessError("流程引用的模型配置不存在", HTTPStatus.NOT_FOUND)
        return LlmNode(definition, source_ids, model_config)
    raise BusinessError(f"尚不支持的流程节点类型：{definition.type}")
