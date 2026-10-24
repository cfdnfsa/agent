# 数据库公共能力

本包提供 ORM 公共字段、连接池和请求会话。具体模型表的查询与写入放在 `app/modules/model_config/repository.py`。

## 文件与阅读顺序

| 文件 | 作用 |
|---|---|
| `base.py` | ORM 基类，声明主键和两个时间字段 |
| `db_connection.py` | 根据配置创建 Engine、会话工厂，提供 FastAPI 会话依赖和公共别名 DbSession |

## 三个对象的区别

- `db_engine`：Engine 实例，进程内复用的数据库连接池入口，创建时不会立即连接数据库。
- `db_session_factory`：创建 Session 的工厂，每次调用产生一个独立会话。
- `db_session`：Session 实例，一次业务操作使用的工作会话，管理实体变化和事务；不在不同并发请求间共享。

当前使用 PostgreSQL 和 psycopg 驱动。`URL.create()` 分别接收主机、用户名和密码，能够处理密码中的特殊字符，无需手工拼接连接字符串。

## 请求会话和事务

```text
Router 的 DbSession 参数
  → get_db_session 创建会话
  → Service 与 Repository 共用该会话
  → Service 的 begin 块正常结束则提交，发生异常则回滚
  → 请求结束，get_db_session 关闭会话并归还连接
```

`get_db_session()` 的 `yield` 把会话交给接口，资源清理在依赖结束、退出 `with` 时进行。查询请求无需提交；关闭会话时会结束未提交的事务。

`DbSession = Annotated[Session, Depends(get_db_session)]` 是公共依赖别名。各业务模块导入 `DbSession`，在依赖函数中声明 `db_session: DbSession`，即可复用相同的会话提供规则。别名本身不创建对象、不缓存会话，也不改变每个请求独立使用会话的约定。

Repository 使用 `flush()` 把 SQL 发送到数据库，读取生成的主键等字段，但这还不代表提交成功。最终提交或回滚由 Service 决定，便于以后将多项写入合并成同一个事务。

`pool_pre_ping=True` 在复用连接时检查连接是否有效；`hide_parameters=True` 隐藏 SQL 异常日志中的绑定参数。

## 表结构与时间字段

业务实体继承 `Base` 后获得 `id`、`created_at`、`updated_at`。时间使用数据库时钟，`updated_at` 由 ORM 在实际更新时赋值，直接绕过 ORM 修改数据时需自行维护。

应用启动时不会自动建表。当前 PostgreSQL 初始化脚本在仓库根目录 `sql/pgsql.sql`；MySQL 初始化脚本保留在 `sql/mysql.sql`，当前后端尚未配置 MySQL 驱动。

## 维护约定

修改连接驱动、会话生命周期、事务规则或公共字段时，同步更新本文档。涉及表结构变更时，同时检查 ORM 实体与 SQL 脚本的一致性。
