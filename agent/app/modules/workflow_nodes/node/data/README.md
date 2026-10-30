# 具体节点的数据对象

本目录存放具体节点使用的数据对象，一个类一个文件；公共节点定义、输入和运行状态仍放在 base/data。

- llm_node_resources.py：LlmNodeResources 保存大模型节点使用的模型、可选提示词实体。factory 创建资源对象，再传给 LlmNode；后续新增资源时扩展此对象。
- llm_node_output.py：LlmNodeOutput 继承公共 NodeOutput，value 是回复正文，message 是 LangChain 原始回复。节点按输入范围读取 value，原始消息不自动进入模型输入或接口响应。

资源对象只保存准备好的配置，不持有数据库会话。输出对象只属于本次请求，保存在 WorkflowState.node_outputs 中，不写回资源对象。完整调用关系见 [具体节点说明](../README.md)。
