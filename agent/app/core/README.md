# 公共能力

本包提供整个后端共用的配置、日志、异常处理和统一返回结构，不包含模型配置的增删改查业务。

## 文件与阅读顺序

| 文件 | 作用 |
|---|---|
| `config.py` | 声明数据库配置字段、读取位置、校验规则和缓存方式 |
| `app_logging.py` | 提供日志对象和当前请求ID，避免与标准库 logging 重名 |
| [errors](errors/README.md) | 公共业务异常和统一异常处理器 |
| [response](response/README.md) | 统一返回 Result 和通用分页 Page |

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

`SecretStr` 打印时隐藏密码，连接数据库时通过 `get_secret_value()` 获取原值；它不执行加密。

## 请求日志怎么关联

业务代码从 `app.core.app_logging` 导入 `logger` 和 `request_id_context`；该模块内部使用标准库 `logging.getLogger()`，文件名不与标准库重名。

`main.py` 给每次请求生成请求ID，写入 `request_id_context`。Service 从同一个上下文读取ID，因此可以关联接口耗时日志和业务操作日志。

`ContextVar` 隔离并发请求的值，请求结束时由中间件恢复上下文。响应头 `X-Request-ID` 会返回本次请求ID，便于前端协助排查。

中间件中的 `request_id_token` 用于恢复请求ID上下文，`request_started_at` 用于计算请求耗时；两者都不是数据库会话。

日志复用 `uvicorn.error`，直接显示在服务控制台。业务日志记录动作、配置ID、状态和耗时，不记录请求体或 API Key。

## 维护约定

调整环境变量、默认值、读取规则或日志关联方式时，同步修改本文件及相关示例。异常和返回结构的细节维护在对应子包文档中。文档不能写入真实凭证。
