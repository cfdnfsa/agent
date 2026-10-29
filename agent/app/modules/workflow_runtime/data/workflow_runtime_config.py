"""运行配置对象：保存已经加载的流程定义和模型实体。"""

from dataclasses import dataclass, field

from app.modules.model_config.entity import ModelConfig
from app.modules.workflow_runtime.data.workflow_definition import WorkflowDefinition


@dataclass
class WorkflowRuntimeConfig:
    """执行前准备好的配置，供执行器直接使用，不作为接口响应返回。

    Attributes:
        workflow: 已解析的流程对象，可通过 workflow.nodes 查看节点。
        model_configs: 按模型ID索引的数据库实体，包含调用需要的 Key，仅供内部使用。
    """

    workflow: WorkflowDefinition
    # 不让自动生成的 repr 展开模型配置；模型实体本身不转换成另一套对象。
    model_configs: dict[int, ModelConfig] = field(repr=False)
