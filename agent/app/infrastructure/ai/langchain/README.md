# LangChain 模型创建

本包位于 infrastructure/ai/langchain，使用 LangChain 的模型集成，model_client.py 只负责创建模型对象。模型测试和问答在各自 Service 中直接调用框架的 invoke，流程模型节点也复用这个创建入口。

## 普通函数

| 函数 | 职责 |
|---|---|
| create_chat_model(model_config) | 判断接入方式，调用对应的创建函数 |
| create_openai_model(model_config) | 创建 OpenAI 兼容模型 |
| create_anthropic_model(model_config) | 创建 Anthropic 模型 |
| create_ollama_model(model_config) | 创建 Ollama 模型 |
| create_google_genai_model(model_config) | 创建 Google Gemini 模型 |

model_config 直接使用数据库查询出的 ModelConfig 实体，包含 Key，不拆开传递连接参数。读取后结束事务，expire_on_commit=False 保留已加载字段。

Service 中的问答调用：

```python
model = create_chat_model(model_config)
answer = str(model.invoke(question).text)
```

invoke 由框架提供，text 取得回复中的文本。问题原样传入，不校验或去空格，不增加历史消息。每种接入方式的创建参数放在自己的普通函数中，不新增类、工厂或协议层。

## 依赖与地址

使用 langchain-core、langchain-openai、langchain-anthropic、langchain-ollama、langchain-google-genai。流程图的构建和执行集中在同级 [langgraph](../langgraph/README.md)，本包只处理模型创建；当前不增加 Agent 循环或记忆。

URL 原样传给对应集成的 base_url，不自动补路径、删除后缀或解析版本；按 SDK 要求填写后，通过页面测试确认能否调用。请求路径、鉴权和响应解析由对应 SDK 负责。

当前只传模型标识、地址和鉴权等接入必需参数；输出长度、停止条件、超时和重试沿用 SDK 默认值，不单独配置。Ollama 有 Key 时通过 client_kwargs 附加鉴权头；Google 使用 API Key 接入方式，API 版本沿用 SDK 默认值。

不需要密钥的兼容接口使用 EMPTY 占位满足 SDK 构造要求。业务代码不输出 Key 或问答正文。

## 异常处理

暂不封装各家的模型异常，也不推断超时或转换成 502/504。SDK 异常向外抛出，由现有公共异常处理返回 HTTP 500 和“服务器内部错误”，排查时查看对应请求ID的服务端日志。不支持的接入方式仍返回现有业务错误。

这是个人极简版本，不提前增加错误分类、参数校验或备用实现；后续有明确需求再讨论。修改集成或调用方式时同步维护本文件。
