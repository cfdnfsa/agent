# LangChain 模型与消息模板

本包位于 infrastructure/ai/langchain。model_client.py 只创建模型对象，prompt_builder.py 使用框架消息模板组装流程节点输入；两者均不查询数据库或决定上下游数据范围。模型测试和问答继续在各自 Service 中直接调用 invoke。

## 普通函数

| 函数 | 职责 |
|---|---|
| create_chat_model(model_config) | 判断接入方式，调用对应的创建函数 |
| create_openai_model(model_config) | 创建 OpenAI 兼容模型 |
| create_anthropic_model(model_config) | 创建 Anthropic 模型 |
| create_ollama_model(model_config) | 创建 Ollama 模型 |
| create_google_genai_model(model_config) | 创建 Google Gemini 模型 |
| build_chat_prompt(context_text, system_prompt) | 使用公共 ChatPromptTemplate 组装上下文与可选系统消息 |

model_config 直接使用 ModelConfig 实体，包含 Key，不拆开传递连接参数。流程节点创建、模型测试和调试台通过 [模型配置缓存](../../../modules/model_config/README.md#模型配置缓存) 取得实体，未命中时的查询会话在调用模型前已关闭，expire_on_commit=False 保留已加载字段。本包不读取缓存或查询数据库，只使用传入的实体。

Service 中的问答调用：

```python
model = create_chat_model(model_config)
answer = str(model.invoke(question).text)
```

invoke 由框架提供，text 取得回复中的文本。问题原样传入，不校验或去空格，不增加历史消息。每种接入方式的创建参数放在自己的普通函数中，不新增类、工厂或协议层。

流程 LLM 节点先通过公共文字函数转换已经选好的上下文，再调用 build_chat_prompt。公共模板只包含“以下是本次流程传入的数据：”和 context 变量，由 ChatPromptTemplate.format_prompt 自动填充并生成 ChatPromptValue，可直接交给 model.invoke。节点选中的提示词正文直接创建 SystemMessage，不作为模板解析，JSON 花括号、空白和换行原样保留；未选提示词时只有用户消息。框架用法见 [ChatPromptTemplate](https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate)。

累计或仅当前结果的传递规则位于节点公共层。本包只接收准备好的文字，不读取 WorkflowState，也不加载配置实体。流程节点的完整模型回复留在内部 LlmNodeOutput.message 中，默认业务结果仍是正文。

## 依赖与地址

使用 langchain-core、langchain-openai、langchain-anthropic、langchain-ollama、langchain-google-genai。流程图的构建和执行集中在同级 [langgraph](../langgraph/README.md)，本包处理模型创建和消息模板；当前不增加 Agent 循环或记忆。

URL 原样传给对应集成的 base_url，不自动补路径、删除后缀或解析版本；按 SDK 要求填写后，通过页面测试确认能否调用。请求路径、鉴权和响应解析由对应 SDK 负责。

当前只传模型标识、地址和鉴权等接入必需参数；输出长度、停止条件、超时和重试沿用 SDK 默认值，不单独配置。Ollama 有 Key 时通过 client_kwargs 附加鉴权头；Google 使用 API Key 接入方式，API 版本沿用 SDK 默认值。

不需要密钥的兼容接口使用 EMPTY 占位满足 SDK 构造要求。业务代码不输出 Key 或问答正文。

## 异常处理

暂不封装各家的模型异常，也不推断超时或转换成 502/504。SDK 异常向外抛出，由现有公共异常处理返回 HTTP 500 和“服务器内部错误”，排查时查看对应请求ID的服务端日志。不支持的接入方式仍返回现有业务错误。

这是个人极简版本，不提前增加错误分类、参数校验或备用实现；后续有明确需求再讨论。修改集成或调用方式时同步维护本文件。
