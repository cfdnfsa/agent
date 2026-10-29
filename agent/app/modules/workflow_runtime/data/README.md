# 流程运行数据对象

每个 dataclass 单独一个文件，固定字段有类型和中文 Attributes 文档，支持属性补全。对象不增加业务校验，不复制数据库实体。

| 文件 | 对象 | 用途 |
|---|---|---|
| workflow_edge.py | WorkflowEdge | 节点之间的连线 |
| workflow_definition.py | WorkflowDefinition | 流程的节点和连线列表 |
| workflow_runtime_config.py | WorkflowRuntimeConfig | 已加载的流程与模型实体，仅内部使用 |
| workflow_result.py | WorkflowResult | 唯一返回节点的输出，其他末端结果不自动混入响应 |

直接从对应文件导入类型，不通过 __init__.py 转发。WorkflowRuntimeConfig 的 repr 不展开模型配置，避免展示 Key；WorkflowResult.payload 是动态业务内容，因此保留 Any。

WorkflowEdge.from_dict(edge_data) 集中读取 source、target、id，缺少 id 时沿用空字符串默认值，不增加校验或改写输入。解析入口使用普通 for 循环调用并 append，与 WorkflowNode.from_dict 的创建方式一致。

节点定义、节点配置、本次输入和状态在 workflow_nodes/base/data/ 中，同样一个对象一个文件，运行关系见 [运行模块说明](../README.md)。
