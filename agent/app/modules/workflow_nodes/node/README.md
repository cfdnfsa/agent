# 具体节点实现

- start_node.py：开始节点，原样输出 inputs.text；预留用户ID保存在 inputs.user_id 中。
- llm_node.py：大模型节点，通过 resources 读取已加载的配置，公共文字函数转换上下文，ai/langchain/prompt_builder.py 使用 ChatPromptTemplate 组装消息，再创建模型并 invoke。提示词正文作为可选系统消息原样使用，用户消息由公共模板填入上下文。
- data/llm_node_resources.py：大模型节点的资源对象，集中保存模型和可选提示词，避免构造参数随资源增加而增长。由 factory 组装，节点只使用；每次运行的数据仍放在 WorkflowState 中。
- data/llm_node_output.py：LlmNodeOutput 继承 NodeOutput，value 保留正文，message 保存原始模型消息；message 不进入传递上下文、日志或 HTTP 响应。
- merge_node.py：收敛节点，合并各上游允许传递的上下文，共同祖先按节点ID去重。累计模式不额外插入重复的嵌套快照，仅当前结果模式以本节点ID包装收集结果；等待全部上游由 LangGraph 负责。
- return_node.py：返回节点，只读取一个上游的 value，作为接口返回内容，不自动返回其累计上下文。每个流程只能有一个，不能连接下游，其他分支仍正常执行。

节点继承 base/base_node.py 的 BaseNode，实现自己的 read_input、execute，复用公共 run。新增节点在这里添加文件，并更新外层 factory.py；不在节点内查询数据库或调用后续节点。

execute 接收 NodeContext、返回 NodeOutput，公共 run 再统一填充 context。LLM 的 build_model_input 调用 base/text.py 的 convert_input_to_text 和 AI 层的 build_chat_prompt；execute 只负责调用步骤并返回 LlmNodeOutput。默认累计传递，选择 result_only 后下游只看到当前结果；这些规则只针对本次流程，不读取或保存跨请求历史对话。

整体关系见 [节点包说明](../README.md)。
