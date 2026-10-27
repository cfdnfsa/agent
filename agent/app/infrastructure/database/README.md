# 数据库公共能力

本包提供 ORM 公共字段、连接池、请求会话和同步事务装饰器。具体表的查询与写入放在各业务模块的 repository.py，例如模型配置和流程配置。

## 文件与阅读顺序

| 文件 | 作用 |
|---|---|
| `base.py` | ORM 基类，只声明公共自增主键 id |
| `db_connection.py` | 根据配置创建 Engine、会话工厂，提供 FastAPI 会话依赖和公共别名 DbSession |
| `transaction.py` | 提供 @transactional，复用 Service 的 db_session 管理同步方法事务 |

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
  → Service 的 @transactional 或局部 begin 块正常结束则提交，发生异常则回滚
  → 请求结束，get_db_session 关闭会话并归还连接
```

`get_db_session()` 的 `yield` 把会话交给接口，资源清理在依赖结束、退出 `with` 时进行。查询请求无需提交；关闭会话时会结束未提交的事务。

`DbSession = Annotated[Session, Depends(get_db_session)]` 是公共依赖别名。各业务模块导入 `DbSession`，在依赖函数中声明 `db_session: DbSession`，即可复用相同的会话提供规则。别名本身不创建对象、不缓存会话，也不改变每个请求独立使用会话的约定。

Repository 使用 `flush()` 把 SQL 发送到数据库，读取生成的主键等字段，但这还不代表提交成功。最终提交或回滚由 Service 决定，便于以后将多项写入合并成同一个事务。

## 事务装饰器怎么使用

新增、修改、删除等同步 Service 方法使用：

```python
# ---------- 新增模型配置
@transactional
def create(self, request_data: dict[str, Any]) -> ModelConfig:
    """保存配置，提交或回滚由装饰器统一管理。"""
    model_config = ModelConfig(**request_data)
    self.model_config_repository.save(model_config)
    return model_config
```

从 `app.infrastructure.database.transaction` 导入 `transactional`。它读取当前对象的 `self.db_session`，用 SQLAlchemy 的 `begin()` 包住整个方法：方法正常结束后提交，发生异常则回滚，提交失败也继续抛给公共异常处理；不创建或关闭会话。

装饰器保留原方法的名称、文档、签名和返回类型。业务方法中的日志表示执行动作，只有提交完成后，装饰器才记录“数据库事务提交”日志；两者通过请求ID关联。

当前只用于独立调用的同步 Service 方法，不支持异步方法、嵌套装饰器调用或加入已有事务；调用前也不要先用同一会话查询，否则可能已经开启隐式事务。Repository 不加装饰器，也不自行提交。

模型测试和问答只在查询配置时使用局部 `with self.db_session.begin()`；退出事务归还连接后再请求模型，不能给整个模型调用方法添加事务装饰器。

`pool_pre_ping=True` 在复用连接时检查连接是否有效；`hide_parameters=True` 隐藏 SQL 异常日志中的绑定参数。

## 表结构与初始化

业务实体继承 `Base` 后只获得公共 `id`，其余字段按各自表结构声明。流程配置只有 ID、名称、定义文本，不增加时间字段。

模型配置也不再声明 created_at、updated_at，接口不返回时间字段。旧表删除这两列的增量脚本为仓库根目录 sql/remove_model_config_time_columns.sql，兼容 MySQL 5.7+ 和 PostgreSQL 14+；新库直接执行最终版初始化脚本。

应用启动时不会自动建表。当前 PostgreSQL 初始化脚本在仓库根目录 `sql/pgsql.sql`；MySQL 初始化脚本保留在 `sql/mysql.sql`，当前后端尚未配置 MySQL 驱动。

## 维护约定

修改连接驱动、会话生命周期、事务规则或公共字段时，同步更新本文档。涉及表结构变更时，同时检查 ORM 实体与 SQL 脚本的一致性。
