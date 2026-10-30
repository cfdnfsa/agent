# 前端接口

公共 `request.ts` 负责 fetch 和统一响应解析，`modelConfigs.ts`、`promptConfigs.ts`、`workflowConfigs.ts` 与 `playground.ts` 共同复用，避免重复处理网络错误。

`playground.ts` 的 `askModel(modelConfigId, question)` 调用 `POST /api/playground/chat`，只提交 `{model_config_id, question}` 并返回回答字符串，不接收或发送历史消息。

`modelConfigs.ts` 集中维护模型配置的 TypeScript 类型和 fetch 请求，路径前缀为 `/api/model-configs`。

| 方法 | 用途 |
|---|---|
| `listModelConfigs(page, pageSize)` | 分页读取列表 |
| `saveModelConfig(modelId, modelConfig)` | ID 为 null 时 POST 新增，否则 PUT 修改 |
| `deleteModelConfig(modelId)` | DELETE 删除指定记录 |
| `testModelConfig(modelId)` | POST `/api/model-configs/{id}/test`，无请求体；成功返回 elapsed_ms |

## 提示词配置接口

promptConfigs.ts 使用 /api/prompt-configs，字段与后端提示词配置保持一致：

| 方法 | 用途 |
|---|---|
| listPromptConfigs(page, pageSize) | GET 分页概要，仅含 id、prompt_name |
| getPromptConfig(promptId) | GET 完整详情，包含 prompt_content |
| savePromptConfig(promptId, promptConfig) | ID 为 null 时 POST 新增，否则 PUT 修改 |
| deletePromptConfig(promptId) | DELETE 指定记录，成功返回 null |

PromptConfigSummary 通过 Pick 明确列表只有 ID、名称，PromptConfigRequest 通过 Omit 排除自增 ID。编辑和详情必须单独请求正文；提交时直接序列化名称、正文，保留空白与换行，不创建额外运行时转换对象。节点引用和执行不在本接口文件中处理。

## 流程配置接口

workflowConfigs.ts 使用 /api/workflow-configs，复用相同的 request 函数：

| 方法 | 用途 |
|---|---|
| listWorkflowConfigs(page, pageSize) | GET 分页概要，只含 id、workflow_name |
| getWorkflowConfig(workflowId) | GET 详情，包含完整定义字符串 |
| saveWorkflowConfig(workflowId, workflowConfig) | ID 为 null 时 POST 新增，否则 PUT 修改 |
| deleteWorkflowConfig(workflowId) | DELETE 指定流程 |
| runWorkflowConfig(workflowId, workflowInput) | POST /{id}/run，提交固定输入 text、可选 user_id，返回最终 payload |

WorkflowInput 对应后端同名对象，text 为本次文字，user_id 为可选字符串或 null，直接作为运行请求体序列化，不额外包一层字段。WorkflowResult 只包含 payload，支持文字、对象或列表，不维护步骤列表、调试结果和 debug 查询参数。失败沿用 request 的公共错误处理，由页面展示公开说明，详细排查信息留在后端日志。

WorkflowConfigSummary 通过 Pick 表示列表实际返回的两个字段，WorkflowConfigRequest 通过 Omit 排除自增 ID；这些仅是 TypeScript 类型，不创建运行时 DTO。接口中的 workflow_definition 始终为字符串；画布页解析、编辑后序列化流程结构，接口模块只负责序列化外层 HTTP 请求体，不再改写定义。

统一解析后端的 `code、message、data`，网络或接口失败时抛出可展示的错误消息，由页面决定展示位置，不在接口模块保存页面状态。

响应 `ModelConfig` 通过 `has_api_key` 表示密钥状态，没有密钥字段，也没有 created_at、updated_at。提交时省略 `model_api_key` 表示保留原值，null 表示清除，非空字符串表示替换。不记录或持久化 API Key 到浏览器存储。

TypeScript 接口只帮助编辑器提示，不做运行时字段校验。配置值和问题原样提交，接入方式类型为 string，不加枚举限制。后端接收 JSON 字典直接操作实体；空字符串也可以原样保存，JSON/ORM/数据库/SDK 的基础要求仍然有效。

测试接口由后端读取配置并发起真实文本调用，前端只提交配置 ID。结果只包含耗时；失败沿用统一错误结构，不返回密钥或模型原始内容。后端字段、枚举或响应结构变更时，同步修改类型、页面和本文档。
