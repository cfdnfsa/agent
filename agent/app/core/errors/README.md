# 公共异常处理

本包集中定义业务异常和 HTTP 异常处理方式，业务模块共用，不为每个模块重复创建“记录不存在”异常。

| 文件 | 职责 |
|---|---|
| `exceptions.py` | 定义 `BusinessError`，保存公开说明和 HTTP 状态码 |
| `exception_handlers.py` | 注册异常处理器，将错误转换为统一 JSON |

## 业务代码用法

```python
raise BusinessError("模型配置不存在", status_code=404)
```

Service 只表达失败原因，不直接构造 HTTP 响应；`main.py` 调用 `register_exception_handlers(app)` 完成统一装配。

注册给框架的处理器统一使用 `(Request, Exception) -> JSONResponse` 的异步签名。需要访问具体异常字段时，函数内部先通过 `isinstance` 确认类型，兼顾框架回调契约与静态类型检查，不使用忽略类型警告的注释。

当前个人极简版已移除业务字段校验和 DTO。这里的 422 处理仍保留，用于 JSON 对象、路径整数等 FastAPI 基础解析错误；数据库约束或 SDK 调用失败直接沿用对应错误处理，不提前再写一套检查。

处理器内部用 `error_result` 表示统一错误结果，`validation_errors` 表示字段校验错误列表，`error_message` 和 `error_details` 表示 HTTP 错误的公开说明与详细数据。

`build_error_response(request, status_code, message, data, headers)` 是共用的普通函数，集中构造 JSON 和请求ID响应头；参数含义写在函数文档中。处理器本身保留框架要求的回调签名。

## 错误约定

| 异常类型 | 返回行为 |
|---|---|
| `BusinessError` | 使用异常指定的状态码和公开说明，默认 HTTP 400 |
| 参数校验异常 | HTTP 422，`data` 返回错误类型、字段位置和说明，不回显输入值 |
| HTTP 异常 | 保留 404、405 等原状态码和框架响应头 |
| SQLAlchemy 异常 | HTTP 500，客户端返回通用说明，服务端记录异常堆栈 |
| 其他未预期异常 | HTTP 500，返回“服务器内部错误”，服务端记录堆栈 |

所有错误都使用 `code、message、data`，格式定义见 [统一返回文档](../response/README.md)。状态码保持真实含义，不用 HTTP 200 包装失败。

请求ID从 `request.state` 获取并写入 `X-Request-ID` 响应头，便于系统异常发生在中间件外层时仍能关联日志。业务异常消息应当可以向用户公开，不放数据库凭证、API Key 或内部堆栈。

修改异常类型、状态码、响应格式或日志行为时，同步更新本文档。
