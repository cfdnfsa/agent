# AI 公共能力

集中维护 AI 框架的接入与执行代码，业务配置和 HTTP 接口仍放在 modules。

| 目录 | 当前职责 |
|---|---|
| [langgraph](langgraph/README.md) | 使用 LangGraph 注册节点、连接流程图、编译和执行 |
| [langchain](langchain/README.md) | 使用模型实体创建模型，使用 ChatPromptTemplate 组装已准备好的消息 |

运行关系：workflow_runtime 准备节点 → langgraph/engine.py 执行 → workflow_nodes 中的节点处理业务；大模型节点、模型测试和调试台复用 langchain/model_client.py。

LangGraph 引擎直接接收现有 BaseNode、WorkflowState，不依赖运行模块的 Service、Repository、HTTP 或返回策略。模型创建仍直接使用 ModelConfig 实体，不增加重复配置对象。

MCP、Skills 和工具能力按实际需求再接入，本次不创建空目录。通用接入、消息模板和调用代码放这里，对应的配置管理留在 modules。
