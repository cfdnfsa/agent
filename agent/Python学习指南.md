# Python 学习指南

只记录目前遇到的基础用法，结合当前项目和 Spring 理解。

## 名字怎样写才容易理解？

Python 的文件名、函数名、变量、参数和属性通常使用下划线连接单词，例如 `db_connection.py`、`get_db_session()`；Java 的 `dbSession` 在这里写成 `db_session`。名字表达用途，例如 `db_session` 是数据库会话，`model_config_service` 是模型配置服务，`model_config_repository` 是模型配置仓储，`create_request` 是新增请求数据。

类型和依赖别名使用首字母大写的写法，例如 `Session`、`DbSession`、`ModelConfigServiceDependency`。`self` 保留惯用名称，类似 Java 的 `this`。

常量通常使用全大写加下划线，例如 `ERROR_RESPONSES`。这些是命名约定，不是语法强制要求。

## 项目里的文件分别做什么？

| 文件 | 职责 | Spring 中类似的概念 |
|---|---|---|
| `router.py` | 接收请求、声明参数校验、调用 Service | Controller |
| `schemas.py` | 定义请求参数和响应数据 | DTO / VO |
| `service.py` | 处理业务、控制事务 | Service |
| `repository.py` | 查询、保存、删除数据库记录 | Repository / Mapper |
| `entity.py` | 定义数据库表与 Python 对象的映射 | Entity |

## `self`、`__init__()` 是什么？

```python
class ModelConfigService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.model_config_repository = ModelConfigRepository(db_session)
```

- `self`：当前对象，类似 Java 的 `this`。它不是关键字，但实例方法的第一个参数通常都叫 `self`。
- `__init__()`：创建对象时自动执行的初始化方法，可以类比 Java 构造方法。
- `self.db_session = db_session`：把传进来的数据库会话保存到当前对象，供其他方法使用。
- `self.model_config_repository`：模型配置仓储，与 Service 共用传入的数据库会话。

调用 `ModelConfigService(db_session)` 时，Python 会自动把新对象作为 `self` 传给 `__init__()`，自己只需要传 `db_session`。

`db_session` 只是有明确含义的参数名字，不代表自动读取当前上下文。这里传入数据库会话，是因为调用方提供的就是 SQLAlchemy Session，不是变量名让它变成数据库对象。

## 参数后面的 `:` 和方法后面的 `->` 是什么？

```python
def get_detail(self, model_id: int) -> ModelConfigResponse:
    ...
```

`model_id: int` 表示参数预期是整数；`-> ModelConfigResponse` 表示预期返回这个类型的对象；`-> None` 表示没有需要返回的结果。

这些是类型标注，方便 IDE 检查和阅读，Python 本身不会仅凭标注强制校验。FastAPI、Pydantic 会利用标注解析和校验请求。

## `ModelConfigId` 为什么带校验？

```python
ModelConfigId = Annotated[int, Path(gt=0, description="模型配置ID")]
```

可以理解成：**整数类型，附带路径参数规则，要求大于 0。**

接口参数写 `model_id: ModelConfigId` 后，FastAPI 会读取并校验路径中的 ID，不符合要求时返回 422。`Annotated` 用于附加信息，这里的校验由 FastAPI 执行。

## `Annotated[Session, Depends(get_db_session)]` 是什么意思？

读成一句话：**FastAPI，请调用 `get_db_session`，把它提供的数据库会话传给这个参数。**

| 部分 | 含义 |
|---|---|
| `Session` | 要什么类型：数据库会话 |
| `Depends(get_db_session)` | 找谁提供：调用 get_db_session |
| `Annotated[...]` | 把类型和附加说明放在一起 |

`Annotated` 本身不创建对象；FastAPI 读取依赖说明，真正创建会话的代码在 `get_db_session` 里面。

公共包 `app/infrastructure/database/db_connection.py` 把这段声明起了一个名字：

```python
DbSession = Annotated[Session, Depends(get_db_session)]
```

所以 `db_session: DbSession` 与原来的完整声明含义相同。它是类型别名，不是全局共享的数据库会话。

## `ModelConfigServiceDependency` 怎么把 Service 注入进来？

```python
def get_model_config_service(db_session: DbSession) -> ModelConfigService:
    return ModelConfigService(db_session)


ModelConfigServiceDependency = Annotated[ModelConfigService, Depends(get_model_config_service)]
```

接口参数写 `model_config_service: ModelConfigServiceDependency`，FastAPI 就会按下面的顺序准备对象：

`get_db_session 提供会话 → get_model_config_service 创建 Service → 把 Service 传给接口`

`Depends` 类似 Spring 的依赖注入。当前代码按请求创建 Service，与 Spring 常见的单例 Service 生命周期不同。`get_model_config_service` 必须定义在引用它的 `Depends(get_model_config_service)` 前面。

公共的 `DbSession` 放在数据库包，模型模块自己的 `get_model_config_service` 和 `ModelConfigServiceDependency` 目前留在 `router.py`，负责这个模块的依赖装配。这是 FastAPI 的用法，不是 Python 语法要求必须放在该文件。

## 每个请求一个 Session，为什么还需要连接池？

当前项目的 `db_engine` 通过 `create_engine(...)` 创建，作为连接池入口在进程内复用；`db_session_factory` 负责创建独立的数据库会话。

```text
请求 A → Session A ─┐
                   ├→ 按需从同一个连接池借连接，用完归还
请求 B → Session B ─┘
```

Session 管理当前请求的数据库操作和事务，连接池负责复用底层连接。每个请求独立创建 Session，不代表每次都新建数据库连接；没有数据库操作时，也可能不需要借连接。不同请求不能共用同一个 Session，以免事务和对象状态互相干扰。

## `db_session` 和 `with self.db_session.begin():` 是什么？

`Session` 是 SQLAlchemy 的数据库会话，负责执行查询、跟踪对象变化、管理事务。它不是用户登录的 Session，也不等于一条数据库连接。

当前项目每个请求使用自己的会话，Service 和 Repository 共用它；请求结束后关闭会话、归还连接。

```python
with self.db_session.begin():
    model_config = self._require_model_config(model_id)
    self.model_config_repository.delete(model_config)
```

- `self.db_session`：取出当前 Service 保存的数据库会话。
- `begin()`：开始一个事务范围，类似 Spring 的 `@Transactional`。
- 正常退出代码块：提交事务；代码块抛出异常：回滚事务。
- `with`：自动管理进入和退出时的操作。这里管理的是事务，会话的关闭由 `get_db_session` 负责。

当前写操作把查询、修改放在同一个 `begin()` 块里，不需要在 Repository 中再次提交事务。

## `_` 和 `__` 是什么意思？

| 写法 | 含义 | 例子 |
|---|---|---|
| `_名称` | 约定内部使用，外部仍能访问 | `_require_model_config()` |
| `__名称` | 类中会改写名称，减少子类命名冲突，并非完全私有 | `self.__password` |
| `__名称__` | Python 定义的特殊名称 | `__init__()`、`__file__` |
| 单独 `_` | 常用来表示不需要使用的变量 | `for _ in range(3)` |

当前代码中：

- `_require_model_config()`：内部辅助方法。
- `__init__()`：创建对象时自动调用的初始化方法。
- `__file__`：当前代码文件的路径。
