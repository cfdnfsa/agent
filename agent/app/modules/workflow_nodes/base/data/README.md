# 节点基础数据

一个对象类型一个文件，使用 dataclass 和中文 Attributes 说明固定字段，字段与运行行为保持原样。

| 文件 | 对象 | 用途 |
|---|---|---|
| workflow_input.py | WorkflowInput | 本次流程输入，payload 为动态业务内容 |
| workflow_node_config.py | WorkflowNodeConfig | 节点配置，例如模型配置ID |
| workflow_node.py | WorkflowNode | 保存的节点ID、类型、配置和名称 |
| workflow_state.py | WorkflowState | 本次输入与各节点输出，运行之间互不共享 |

各处直接从对应文件导入类，不通过 __init__.py 转发。workflow_state.py 同时维护 merge_node_outputs，它只合并状态存储增量，不负责分支等待。

WorkflowNode.from_dict(node_data) 是类自己的创建入口，集中读取单个节点字典并创建 WorkflowNodeConfig，保留已有字段和默认值，不增加校验或改写输入。解析流程时只遍历并调用该方法；它创建的是配置定义，外层 factory.py 的 create_node 才创建实际执行的业务节点。

WorkflowState 保留 TYPE_CHECKING 下的 dataclass 元信息声明，帮助 PyCharm 匹配 LangGraph 类型约束；运行时状态字段仍只有 inputs、node_outputs。

节点公共执行入口见 [base_node.py](../base_node.py)，整体关系见 [节点包说明](../../README.md)。
