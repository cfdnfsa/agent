# 具体节点实现

- start_node.py：开始节点，原样输出 inputs.text；预留用户ID保存在 inputs.user_id 中。
- llm_node.py：大模型节点，通过 resources.model_config、resources.prompt_config 读取已加载的实体，使用 ai/langchain/model_client.py 创建模型。无提示词时直接 invoke 上游文字，选中后以 SystemMessage 传任务说明、HumanMessage 传上游内容，返回文字；正文原样使用，不替换变量。
- data/llm_node_resources.py：大模型节点的资源对象，集中保存模型和可选提示词，避免构造参数随资源增加而增长。由 factory 组装，节点只使用；每次运行的数据仍放在 WorkflowState 中。
- merge_node.py：收敛节点，按上游ID收集结果；等待全部上游由 LangGraph 负责。
- return_node.py：返回节点，原样输出一个上游的数据。每个流程只能有一个，不能连接下游，其他分支仍正常执行。

节点继承 base/base_node.py 的 BaseNode，实现自己的 read_input、execute，复用公共 run。新增节点在这里添加文件，并更新外层 factory.py；不在节点内查询数据库或调用后续节点。

大模型节点的 execute 只串联调用步骤：普通函数 convert_input_to_text 将输入转成文字，节点方法 build_model_input 根据可选提示词组装模型输入，最后统一调用一次 model.invoke 并返回文字。这些辅助逻辑都放在 llm_node.py 中，便于顺着调用阅读。

整体关系见 [节点包说明](../README.md)。
