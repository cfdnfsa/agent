# Python 学习指南

结合当前个人极简版本，只保留已经讨论过的基础用法。

## 命名

文件、函数、变量使用下划线连接单词，例如 db_connection.py、create_chat_model、db_session。类和类型别名使用大驼峰，例如 ModelConfig、DbSession；常量使用全大写，例如 ERROR_RESPONSES。

辅助函数默认使用直白名称，减少前导 _ 和额外抽象。已有 Service、Repository 继续保留，简单组装逻辑使用普通函数。

## self 和 __init__

```python
class ModelConfigService:
    # ---------- 初始化模型配置服务
    def __init__(self, db_session: Session):
        self.db_session = db_session
```

self 类似 Java 的 this；__init__ 是创建对象时执行的初始化方法；右侧 db_session 由外部传入，左侧 self.db_session 保存到当前对象。变量名本身不会自动创建数据库会话。

## 类型标注

```python
# ---------- 根据接入方式创建模型
def create_chat_model(model_config: ModelConfig) -> BaseChatModel:
    ...
```

冒号后说明参数预期类型，箭头后说明返回类型。Python 本身不会仅凭标注强制检查。FastAPI 仍会进行 JSON、路径整数等基本解析；这一版已移除业务字段的额外校验和 DTO 转换。

`ModelConfig` 表示实体对象，`type[ModelConfig]` 表示类本身。查询得到的是对象，返回类型写 `ModelConfig`；可能查不到则写 `ModelConfig | None`，不要套 `type[...]`。

`cast(ModelConfig | None, model_config)` 只告诉类型检查器“这里是实体或 None”，不转换、不复制或校验对象。当前用于兼容部分 PyCharm 版本对 SQLAlchemy 查询结果的误判。

## Annotated 和 Depends

```python
DbSession = Annotated[Session, Depends(get_db_session)]
```

Session 表示需要的类型；Depends(get_db_session) 告诉 FastAPI 找谁提供对象；Annotated 把类型和额外信息放在一起。参数写 db_session: DbSession 后，框架取得会话并传进来。

Service 的依赖同理：Depends(get_model_config_service) 告诉框架创建并提供模型配置服务。

## Session、连接池和事务

连接池通过 db_engine 复用连接；每个请求的 db_session 独立使用。真正操作数据库时借连接，事务结束后归还。

```python
with self.db_session.begin():
    model_config = self.require_model_config(model_id)
    self.model_config_repository.delete(model_config)
```

正常退出 begin 块时提交，抛出异常则回滚。项目把这段重复逻辑封装成了装饰器，新增、修改、删除现在这样写，作用类似 Spring 的 @Transactional：

```python
# ---------- 删除模型配置
@transactional
def delete(self, model_id: int) -> None:
    """删除记录，事务由装饰器统一管理。"""
    self.model_config_repository.delete(self.require_model_config(model_id))
```

`@transactional` 来自数据库公共包的 transaction.py，复用 self.db_session，不创建新会话；方法正常执行后提交，异常回滚。当前只用于同步方法，不支持嵌套调用或加入已有事务。请求结束后关闭会话。

测试和问答继续使用上面的局部 with：先查询实体、结束事务，再等待模型，已加载属性由 expire_on_commit=False 保留。

## _、__、* 与方法文档

| 写法 | 含义 |
|---|---|
| _name | 内部使用的命名约定，不是安全机制；当前优先用普通名称 |
| __name | 类中会改写名称以减少命名冲突，并非完全私有 |
| __name__ | Python 特殊名称，例如 __init__、__file__ |
| 单独 _ | 常表示不使用的变量 |
| 参数列表中单独 * | 后面的参数必须写成参数名=值；当前模型创建函数直接接收实体参数 |

方法中的三引号字符串是文档：Args 说明参数，Returns 说明返回值，不是 Python 语法关键字。

项目统一在每个函数和类方法上方添加 `# ---------- 中文用途`，不加尾部横线；包括 `__init__` 和异步函数。有装饰器时，分隔注释放在第一条装饰器上方。分隔注释便于定位，方法内的文档字符串继续解释具体行为：

```python
# ---------- 查询模型配置详情
def get_detail(self, model_id: int) -> ModelConfig:
    """根据配置ID查询模型，找不到时抛出业务异常。"""
    return self.require_model_config(model_id)
```

## 当前模型调用

```python
model = create_chat_model(model_config)
answer = str(model.invoke(question).text)
```

model_config 就是查询出来的数据库实体。model_client 根据它创建 LangChain 模型；Service 直接调用框架提供的 invoke 提问，text 取得回复文本。URL 原样传给 SDK，不自动调整。
