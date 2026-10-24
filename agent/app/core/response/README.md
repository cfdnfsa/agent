# 统一返回与分页

`responses.py` 提供业务接口共用的 `Result[T]`、`Page[T]` 和错误文档声明，不包含具体模型业务。

## Result

| 字段 | 约定 |
|---|---|
| `code` | 成功为 0；失败使用对应的 HTTP 状态码 |
| `message` | 成功默认“成功”；失败为公开错误说明 |
| `data` | 业务数据；没有数据时为 null |

`T` 表示业务数据的类型，例如 `Result[ModelConfigResponse]` 表示 `data` 为模型详情。Router 包装 Result，Service 继续返回业务数据，避免层层重复包装。

删除成功返回 HTTP 200：

```json
{
  "code": 0,
  "message": "成功",
  "data": null
}
```

新增成功仍为 HTTP 201。失败保留真实 HTTP 状态，例如模型不存在使用 HTTP 404，同时 JSON 中 `code` 为 404。

## Page

`Page[T]` 只包含 `items、total、page、page_size`。模型分页接口类型为 `Result[Page[ModelConfigResponse]]`：分页字段位于 `data` 内，`items` 里的每条记录为不含 Key 的模型详情。

## 接口文档

Router 使用 `ERROR_RESPONSES` 声明公共错误模型，确保 `/docs` 中的 400、404、422、500 响应与实际统一格式一致。参数校验错误的 `data` 可包含字段错误列表，其余当前公共错误一般为 null。

FastAPI 的 `/docs`、`/openapi.json` 等框架端点不包装为 Result；以后文件下载或 SSE 接口也应按各自格式定义，不强制包装 JSON。

修改字段、结果码、分页约定或公共错误文档时，同步更新本文档。
