# 模型配置接口

公共 `request.ts` 负责 fetch 和统一响应解析，`modelConfigs.ts` 与 `playground.ts` 共同复用，避免重复处理网络错误。

`playground.ts` 的 `askModel(modelConfigId, question)` 调用 `POST /api/playground/chat`，只提交 `{model_config_id, question}` 并返回回答字符串，不接收或发送历史消息。

`modelConfigs.ts` 集中维护模型配置的 TypeScript 类型和 fetch 请求，路径前缀为 `/api/model-configs`。

| 方法 | 用途 |
|---|---|
| `listModelConfigs(page, pageSize)` | 分页读取列表 |
| `saveModelConfig(modelId, modelConfig)` | ID 为 null 时 POST 新增，否则 PUT 修改 |
| `deleteModelConfig(modelId)` | DELETE 删除指定记录 |
| `testModelConfig(modelId)` | POST `/api/model-configs/{id}/test`，无请求体；成功返回 elapsed_ms |

统一解析后端的 `code、message、data`，网络或接口失败时抛出可展示的错误消息，由页面决定展示位置，不在接口模块保存页面状态。

响应 `ModelConfig` 只有 `has_api_key`，没有密钥字段。提交时省略 `model_api_key` 表示保留原值，null 表示清除，非空字符串表示替换。不记录或持久化 API Key 到浏览器存储。

TypeScript 接口只帮助编辑器提示，不做运行时字段校验。配置值和问题原样提交，接入方式类型为 string，不加枚举限制。后端接收 JSON 字典直接操作实体；空字符串也可以原样保存，JSON/ORM/数据库/SDK 的基础要求仍然有效。

测试接口由后端读取配置并发起真实文本调用，前端只提交配置 ID。结果只包含耗时；失败沿用统一错误结构，不返回密钥或模型原始内容。后端字段、枚举或响应结构变更时，同步修改类型、页面和本文档。
