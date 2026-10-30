# 具体节点实现

- start_node.py：开始节点，原样输出 inputs.text；预留用户ID保存在 inputs.user_id 中。
- llm_node.py：大模型节点，通过 resources 读取已加载的配置，公共文字函数转换上下文，ai/langchain/prompt_builder.py 使用 ChatPromptTemplate 组装消息，再创建模型并 invoke。提示词正文作为可选系统消息原样使用，用户消息由公共模板填入上下文。
- data/llm_node_resources.py：大模型节点的资源对象，集中保存模型和可选提示词，避免构造参数随资源增加而增长。由 factory 组装，节点只使用；每次运行的数据仍放在 WorkflowState 中。
- data/llm_node_output.py：LlmNodeOutput 继承 NodeOutput，value 保留正文，message 保存原始模型消息；message 不自动进入模型输入、日志或 HTTP 响应。
- merge_node.py：收敛节点，等待全部直接上游后按本节点的输入范围收集结果，按节点ID组织为一个对象；等待由 LangGraph 负责。
- return_node.py：返回节点，只读取一个直接上游的 value，作为接口返回内容。每个流程只能有一个，不能连接下游，其他分支仍正常执行。

节点继承 base/base_node.py 的 BaseNode，实现自己的 read_input、execute，复用公共 run。新增节点在这里添加文件，并更新外层 factory.py；不在节点内查询数据库或调用后续节点。

execute 接收 NodeContext、返回 NodeOutput，公共 run 只保存当前结果。LLM 的 build_model_input 调用 base/text.py 的 convert_input_to_text 和 AI 层的 build_chat_prompt；execute 只负责调用步骤并返回 LlmNodeOutput。LLM、收敛的 input_scope 默认 all_upstream，可改 direct_upstream。每个节点独立选择，不影响后续节点重新读取原始数据；不读取或保存跨请求历史对话。

LLM 可以直接连接多个上游。例如 a、c 都指向总结节点 b，b 选择 direct_upstream 就读取 a、c 两份结果，由 LangGraph 等待双方完成。LLM 与收敛共用公共 read_input，只有需要把多份结果打包为一个对象时才使用收敛节点。

整体关系见 [节点包说明](../README.md)。
