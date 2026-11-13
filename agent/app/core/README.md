# 公共能力

本包提供整个后端共用的配置、日志、异常处理和统一返回结构，不包含模型配置的增删改查业务。

## 文件与阅读顺序

| 文件 | 作用 |
|---|---|
| `config.py` | 声明数据库配置字段、读取位置、基础类型和缓存方式 |
| `app_logging.py` | 提供日志对象和当前请求ID，避免与标准库 logging 重名 |
| [errors/exceptions.py](errors/exceptions.py) | 公共业务异常 BusinessError |
| [errors/exception_handlers.py](errors/exception_handlers.py) | 统一异常处理器 |
| [response/responses.py](response/responses.py) | 统一返回 Result、通用分页 Page 与错误文档声明 |

## 数据库配置怎么读取

`Settings` 把配置转换为 Python 对象。读取优先级为系统环境变量、后端根目录的 `.env`、字段默认值。

| 环境变量 | 对象属性 | 含义 |
|---|---|---|
| `DB_HOST` | `db_host` | PostgreSQL 主机 |
| `DB_PORT` | `db_port` | 端口，默认 5432 |
| `DB_NAME` | `db_name` | 数据库名 |
| `DB_USER` | `db_user` | 数据库用户名 |
| `DB_PASSWORD` | `db_password` | 数据库密码 |

`.env` 根据代码文件位置定位，不依赖启动时所在的目录。连接信息示例见后端根目录的 `.env.example`；真实配置只放在已被 Git 忽略的 `.env` 或环境变量中。

`get_settings()` 使用 `lru_cache`：第一次调用读取并校验配置，后续复用对象。修改配置后需要重启后端。

`Settings` 显式提供无参初始化方法，配置值仍由 `BaseSettings` 从环境变量或 `.env` 读取并校验。调用方不必手动传入字段，静态检查器也不会将环境配置误判为缺失的构造参数。

当前极简版本去掉配置字符串最小长度、端口范围等额外规则，只保留读取必需配置和基础类型解析；连接是否可用交给数据库驱动处理。

`SecretStr` 打印时隐藏密码，连接数据库时通过 `get_secret_value()` 获取原值；它不执行加密。

## 请求日志怎么关联

业务代码从 `app.core.app_logging` 导入 `logger` 和 `request_id_context`；该模块内部使用标准库 `logging.getLogger()`，文件名不与标准库重名。

`main.py` 给每次请求生成请求ID，写入 `request_id_context`。Service 从同一个上下文读取ID，因此可以关联接口耗时日志和业务操作日志。

`ContextVar` 隔离并发请求的值，请求结束时由中间件恢复上下文。响应头 `X-Request-ID` 会返回本次请求ID，便于前端协助排查。

中间件中的 `request_id_token` 用于恢复请求ID上下文，`request_started_at` 用于计算请求耗时；两者都不是数据库会话。

日志复用 `uvicorn.error`，直接显示在服务控制台。业务日志记录动作、配置ID、状态和耗时，不记录请求体或 API Key。

日志调用统一使用单行写法，并在调用前后各留一个空行，方便阅读；参数之间正常保留空格。后续新增或修改日志继续遵循该规则。

## 公共异常

业务代码使用 `raise BusinessError("模型配置不存在", status_code=404)` 表达失败，由 main.py 调用 register_exception_handlers(app) 统一装配。业务消息应可向用户公开，不含数据库凭证、Key 或内部堆栈，不为每个模块重复定义“记录不存在”异常。

| 异常类型 | 返回行为 |
|---|---|
| BusinessError | 使用指定的状态码和公开说明，默认 HTTP 400 |
| FastAPI 基础解析错误 | HTTP 422，只返回错误类型、字段位置和说明，不回显输入值 |
| HTTP 异常 | 保留 404、405 等原状态码和框架响应头 |
| SQLAlchemy 异常 | HTTP 500，返回通用说明，服务端记录堆栈 |
| 其他异常 | HTTP 500，返回“服务器内部错误”，服务端记录堆栈 |

处理器使用异步 `(Request, Exception) -> JSONResponse` 签名，内部先用 isinstance 确认具体类型再读取字段，兼顾框架回调约束和类型检查。共用 build_error_response 构造 JSON 与 X-Request-ID，错误时也从 request.state 取得请求ID，便于关联中间件外层异常。

当前不增加业务字段校验，422 仍用于 JSON、路径整数等基础解析；数据库和 SDK 约束失败沿用公共处理。

## 统一返回与分页

Router 包装 Result[T]，Service 返回业务数据；T 是 data 的类型。配置响应直接读取实体字段并排除 Key，不建立重复响应对象。

| 字段 | 约定 |
|---|---|
| code | 成功为 0，失败为对应 HTTP 状态码 |
| message | 成功默认“成功”，失败为公开说明 |
| data | 业务数据，无数据时为 null |

删除成功返回 HTTP 200 与 `{"code":0,"message":"成功","data":null}`，新增成功为 HTTP 201。失败保留真实 HTTP 状态，不使用 HTTP 200 包装失败。

Page[T] 只有 items、total、page、page_size，不增加数值范围校验。ERROR_RESPONSES 为 Router 声明公共错误模型，使 /docs 中的 400、404、422、500 与实际格式一致。校验错误 data 可包含字段错误列表，其他公共错误通常为 null。

FastAPI 的 /docs、/openapi.json 等框架端点不包装 Result；文件下载或流式接口按各自格式定义。

## 维护约定

配置、日志、异常和返回结构统一维护本文件，子目录通过代码注释说明。调整环境变量、响应字段、状态码或日志行为时同步更新本文及相关示例，文档不能写入真实凭证。
