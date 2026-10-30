# 节点基础数据

一个对象类型一个文件，使用 dataclass 和中文 Attributes 说明固定字段。

| 文件 | 对象 | 用途 |
|---|---|---|
| workflow_input.py | WorkflowInput | 固定输入 text 与可选 user_id，可通过属性补全读取 |
| workflow_node_config.py | WorkflowNodeConfig | model_config_id、可选 prompt_config_id、input_scope |
| workflow_node.py | WorkflowNode | 保存的节点ID、类型、配置和名称 |
| workflow_state.py | WorkflowState | 本次输入与各节点输出，运行之间互不共享 |
| node_context.py | NodeContext | results 按节点ID保存当前节点选中的输入 |
| node_output.py | NodeOutput | value 为当前节点的业务结果，统一保存在运行状态中 |

各处直接从对应文件导入类，不通过 __init__.py 转发。workflow_state.py 同时维护 merge_node_outputs，它只合并状态存储增量，不负责分支等待。

WorkflowInput(text="你好", user_id="user_001") 表示本次文字和预留用户ID；user_id 不传时为 None。开始节点将 inputs.text 放在自己的ID下，作为最初的上下文，用户ID留在 inputs.user_id 中供后续节点读取，不自动拼进模型问题。NodeOutput.value 允许文字、对象或列表。

默认 input_scope 为 all_upstream，读取整条上游依赖链的结果；direct_upstream 仅读取直接上游。WorkflowState.node_outputs 统一保存全部 NodeOutput，NodeContext 只是本次节点按配置选出的输入，不写回其他节点结果。无关分支不会因为已经执行就被读入，后续节点也能独立选择重新读取更早的结果。

节点只创建 NodeOutput(value=业务结果)，不再维护下游上下文；大模型输出在 node/data/llm_node_output.py 继承它，额外保存完整模型消息。运行模块提前根据连线准备 input_ids，读取逻辑不遍历全部已执行结果。

WorkflowNode.from_dict(node_data) 是类自己的创建入口，集中读取单个节点字典并创建 WorkflowNodeConfig，保留已有字段和默认值，不增加校验或改写输入。解析流程时只遍历并调用该方法；它创建的是配置定义，外层 factory.py 的 create_node 才创建实际执行的业务节点。

LLM 节点可保存 config.prompt_config_id，未选择时省略或为 null；这里只保存引用ID，完整提示词实体在 factory 创建节点时从缓存读取，正文不写入流程定义。各节点独立保存自己的选择。

WorkflowState 保留 TYPE_CHECKING 下的 dataclass 元信息声明，帮助 PyCharm 匹配 LangGraph 类型约束；运行时状态字段仍只有 inputs、node_outputs。

节点公共执行入口见 [base_node.py](../base_node.py)，整体关系见 [节点包说明](../../README.md)。
