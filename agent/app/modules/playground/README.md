# 调试台（个人极简版）

最基础的无上下文模型问答，不保存聊天记录。接口直接接收 JSON、直接返回回答，不再使用 schemas.py 或独立请求/响应类。

- router.py：接收 JSON，注入服务，包装 Result。
- service.py：按ID读取含 Key 的 ModelConfig 实体，直接传给公共模型客户端。

## 接口

POST /api/playground/chat

```json
{"model_config_id":1,"question":"你好"}
```

成功返回：

```json
{"code":0,"message":"成功","data":{"answer":"你好！"}}
```

服务使用 model_config_id 和 question 这两个字段，不额外检查必填、空字符串、长度或去除空格。JSON 的基础解析、数据库约束、LangChain/SDK 自身要求仍生效；缺字段、模型配置不存在或调用失败时，直接沿用统一错误处理。

读取配置后结束数据库事务，通过 [ai/langchain/model_client.py](../../infrastructure/ai/langchain/model_client.py) 中的 create_chat_model(model_config) 创建模型，再直接调用 model.invoke(question)，用 str(response.text) 取得回答。内部传递数据库实体，不拆散地址和 Key，也不创建重复配置对象。每次 invoke 只包含当前问题，没有历史上下文或会话ID。

业务日志只记录请求ID、模型ID和耗时，不记录问答正文或 Key。SDK 异常沿用公共异常处理，返回 HTTP 500 和“服务器内部错误”，暂不增加模型错误分类。修改接口或调用行为时同步维护本文件。
