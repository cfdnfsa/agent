# 具体节点实现

- start_node.py：开始节点，原样输出 inputs.text；预留用户ID保存在 inputs.user_id 中。
- llm_node.py：大模型节点，使用已加载的模型和可选提示词实体，通过 ai/langchain/model_client.py 创建模型。无提示词时直接 invoke 上游文字，选中后以 SystemMessage 传任务说明、HumanMessage 传上游内容，返回文字；正文原样使用，不替换变量。
- merge_node.py：收敛节点，按上游ID收集结果；等待全部上游由 LangGraph 负责。
- return_node.py：返回节点，原样输出一个上游的数据。每个流程只能有一个，不能连接下游，其他分支仍正常执行。

节点继承 base/base_node.py 的 BaseNode，实现自己的 read_input、execute，复用公共 run。新增节点在这里添加文件，并更新外层 factory.py；不在节点内查询数据库或调用后续节点。

整体关系见 [节点包说明](../README.md)。
