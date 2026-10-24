# 模型配置接口

`modelConfigs.ts` 集中维护模型配置的 TypeScript 类型和 fetch 请求，路径前缀为 `/api/model-configs`。

| 方法 | 用途 |
|---|---|
| `listModelConfigs(page, pageSize)` | 分页读取列表 |
| `saveModelConfig(modelId, modelConfig)` | ID 为 null 时 POST 新增，否则 PUT 修改 |
| `deleteModelConfig(modelId)` | DELETE 删除指定记录 |

统一解析后端的 `code、message、data`，网络或接口失败时抛出可展示的错误消息，由页面决定展示位置，不在接口模块保存页面状态。

响应 `ModelConfig` 只有 `has_api_key`，没有密钥字段。提交时省略 `model_api_key` 表示保留原值，null 表示清除，非空字符串表示替换。不记录或持久化 API Key 到浏览器存储。

此处只管理模型连接配置，不发起模型调用。后端字段、枚举或响应结构变更时，同步修改类型、页面和本文档。
