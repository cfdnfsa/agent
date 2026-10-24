# 模型配置管理

本包实现模型配置的新增、分页列表、详情、修改和删除。当前只保存连接配置，不调用模型，不做连接测试，也不加密 API Key。

## 文件职责与阅读顺序

| 文件 | 职责 |
|---|---|
| `router.py` | HTTP 路径、参数校验、Service 依赖装配和 Result 包装 |
| `schemas.py` | 接口入参、出参和接入方式枚举 |
| `service.py` | 组织业务流程、处理 Key 修改规则、控制写入事务 |
| `repository.py` | 使用 SQLAlchemy ORM 访问模型表 |
| `entity.py` | 映射 `model_config` 数据表及计算属性 |

建议沿着一次新增请求阅读：`router.create_model → service.create → repository.save → entity.ModelConfig`，同时对照 `schemas.ModelConfigCreate` 和 `ModelConfigResponse`。

依赖装配保留在 `router.py`：`get_model_config_service(db_session: DbSession)` 使用数据库公共包提供的会话别名创建 Service，`ModelConfigServiceDependency` 再把 Service 注入接口参数 `model_config_service`。公共数据库依赖在 `app/infrastructure/database/db_connection.py` 中维护，模块不重复声明。

Service 和 Repository 的会话属性统一叫 `db_session`；Service 持有的仓储叫 `model_config_repository`。新增和修改入参分别叫 `create_request`、`update_request`，响应对象叫 `model_config_response`，避免仅凭类型才能判断变量用途。路径 ID 校验别名叫 `ModelConfigId`，内部查询方法叫 `_require_model_config`。

## 接口

| 方法 | 路径 | 功能 |
|---|---|---|
| POST | `/api/model-configs` | 新增，成功返回 201 |
| GET | `/api/model-configs?page=1&page_size=20` | 按ID倒序分页，单页最多 100 条 |
| GET | `/api/model-configs/{id}` | 详情 |
| PUT | `/api/model-configs/{id}` | 修改 |
| DELETE | `/api/model-configs/{id}` | 删除，成功返回 200 和统一 JSON，data 为 null |

ID 必须大于 0。详情、修改和删除找不到记录时返回 404，入参校验失败返回 422。业务不存在统一抛出公共 `BusinessError`，不再单独定义模型异常类。

## 新增与修改入参

```json
{
  "model_name": "本地问答模型",
  "model_code": "你的模型标识",
  "model_provider": "ollama",
  "model_base_url": "http://127.0.0.1:11434",
  "model_api_key": null
}
```

显示名称、模型标识、接入方式和服务地址必填；新增时可以省略 Key。`model_provider` 可选 `openai`、`ollama`、`anthropic`、`google_genai`，这里只校验和保存类型，不代表已经实现对应模型调用。

修改使用 PUT，四个普通配置项都要提交。Key 的行为单独约定：

| 提交方式 | 处理结果 |
|---|---|
| 不传 `model_api_key` | 保留原 Key |
| 传 `null` 或空字符串 | 清除原 Key，数据库保存 NULL |
| 传非空字符串 | 替换原 Key |

Service 使用 `model_fields_set` 判断字段是否实际提交，避免把“不传”和“传 null”混淆。

## 响应与保存约定

成功和失败都使用公共 `Result`：`code、message、data`。成功 `code=0`；失败 `code` 与实际 HTTP 状态码一致。详情位于 `data`，分页字段 `items、total、page、page_size` 也位于 `data`，复用公共 `Page[ModelConfigResponse]`。

Service 返回业务数据，Router 包装一次 Result；错误响应由公共异常处理器生成。公共约定见 [统一返回](../../core/response/README.md) 和 [异常处理](../../core/errors/README.md)。

Key 当前明文保存在 `model_api_key` 列中。响应结构没有这个字段，只返回 `has_api_key` 表示是否配置；参数校验错误也不回显请求原值。

新增和修改通过 `flush + refresh` 得到数据库主键、时间，再转换为响应对象；只有事务提交成功才返回成功结果。删除只按给定主键定位一条记录。

## 维护约定

新增字段时检查入参、实体、Service 映射、响应和 SQL 脚本是否需要同步调整。修改接口、分页、Key 行为或接入方式枚举时，同步更新本文档及 `/docs` 字段说明。
