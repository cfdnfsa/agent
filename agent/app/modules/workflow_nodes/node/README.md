# 具体节点实现

- start_node.py：开始节点，原样输出 inputs.text；预留用户ID保存在 inputs.user_id 中。
- llm_node.py：大模型节点，通过 resources 读取已加载的配置，公共文字函数转换上下文，ai/langchain/prompt_builder.py 使用 ChatPromptTemplate 组装消息，再创建模型并 invoke。提示词先按节点选择的变量来源渲染，再作为系统消息使用，用户消息由公共模板填入上下文。
- intent_analysis_node.py：独立意图分析节点，内置分类说明，可选提示词作为补充；普通 invoke 后使用 PydanticOutputParser 解析 tasks 列表，不要求模型支持工具调用，不分发或执行任务。
- data/intent_task.py、data/intent_analysis_result.py：固定的任务与分析结果，使用 Pydantic BaseModel 供框架直接解析，通过 result.tasks、task.type、task.question 读取。
- data/llm_node_resources.py：大模型节点的资源对象，集中保存模型和可选提示词，避免构造参数随资源增加而增长。由 factory 组装，节点只使用；每次运行的数据仍放在 WorkflowState 中。
- data/llm_node_output.py：普通 LLM 和意图分析共用的输出，value 分别是正文或任务结果对象，message 保存原始模型消息；message 不自动进入模型输入、日志或 HTTP 响应。
- merge_node.py：收敛节点，等待全部直接上游后按本节点的输入范围收集结果，按节点ID组织为一个对象；等待由 LangGraph 负责。
- return_node.py：返回节点，只读取一个直接上游的 value，作为接口返回内容。每个流程只能有一个，不能连接下游，其他分支仍正常执行。

节点继承 base/base_node.py 的 BaseNode，实现自己的 read_input、execute，复用公共 run。新增节点在这里添加文件，并更新外层 factory.py；不在节点内查询数据库或调用后续节点。

execute 接收 NodeContext、返回 NodeOutput，公共 run 只保存当前结果。普通 LLM 和意图分析通过 build_model_input 复用 base/text.py 与公共消息模板。它们和收敛的 input_scope 默认 all_upstream，可改 direct_upstream。每个节点独立选择，不影响后续节点重新读取原始数据；不读取或保存跨请求历史对话。

意图任务包含 database（查询数据）、knowledge（检索资料）、chat（普通问答或待澄清问题）、unsupported（当前不支持的操作）。输出格式解析失败时抛出不含模型原文的 BusinessError，不增加自动重试。先配置“开始 → 意图分析 → 返回”查看任务对象，实际分类质量取决于选中的模型与提示词。

LLM 可以直接连接多个上游。例如 a、c 都指向总结节点 b，b 选择 direct_upstream 就读取 a、c 两份结果，由 LangGraph 等待双方完成。LLM 与收敛共用公共 read_input，只有需要把多份结果打包为一个对象时才使用收敛节点。

整体关系见 [节点包说明](../README.md)。

普通 LLM 和意图分析共用 base/prompt_variables.py。意图分析只渲染用户选中的补充提示词，内置分类与框架 JSON 说明保持原文。当前多个节点结果仍进入一条用户上下文消息，完整角色消息列表暂未开放。
