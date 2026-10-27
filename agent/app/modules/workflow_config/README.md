# 流程配置管理（个人极简版）

本包只做流程配置的新增、分页列表、详情、修改和删除。流程定义作为文本原样保存，当前不解析 JSON、不校验节点或连线，也不执行流程。

## 文件职责

| 文件 | 职责 |
|---|---|
| entity.py | 映射流程表三个字段，提供完整实体的 to_dict |
| repository.py | ORM 查询、保存和删除；列表只查询 ID、名称 |
| service.py | 编排增删改查，写操作使用公共 @transactional |
| router.py | 注入当前请求的 Service，包装 Result 和 Page |

Service 和 Repository 共用同一个请求 Session。get_by_id 返回实体或 None，使用 typing.cast 兼容部分 PyCharm 的查询结果类型推断，不做数据转换。

## 表结构

表名为 workflow_config，一条记录代表一个流程，只有三个字段：

| 字段 | 类型与用途 |
|---|---|
| id | BIGINT 自增主键，继承公共 Base |
| workflow_name | VARCHAR(100)，流程名称 |
| workflow_definition | MySQL LONGTEXT、PostgreSQL TEXT，流程定义字符串 |

没有创建时间、更新时间、状态或版本字段。模型配置也不再维护时间字段。流程定义不使用数据库 JSON/JSONB 类型，不拆成节点表和连线表。

初始化 SQL 见仓库根目录 sql/mysql.sql、sql/pgsql.sql；应用启动不自动建表。当前服务使用 PostgreSQL，MySQL 脚本兼容 5.7，ORM 文本类型也保留对应的 LONGTEXT 映射。

## 接口

统一前缀为 /api/workflow-configs，所有接口使用公共 Result，缺失记录返回 HTTP 404。

| 方法 | 路径 | 行为 |
|---|---|---|
| POST | /api/workflow-configs | 新增，成功 HTTP 201，返回完整实体字段 |
| GET | /api/workflow-configs?page=1&page_size=20 | 按主键倒序分页，只返回 id、workflow_name |
| GET | /api/workflow-configs/{id} | 详情，返回完整三个字段 |
| PUT | /api/workflow-configs/{id} | 提交哪些字段就更新哪些，返回完整实体字段 |
| DELETE | /api/workflow-configs/{id} | 删除，成功 HTTP 200、data=null |

新增请求示例：

```json
{
  "workflow_name": "文章总结",
  "workflow_definition": "{\"nodes\":[],\"edges\":[]}"
}
```

workflow_definition 在请求和响应中都是字符串，示例里的转义符用于在 HTTP JSON 中表达字符串；后端不进行第二次解析，不自动添加节点、去空格或重写内容。空字符串也按原值保存。数据库已有的非空、类型、长度约束和 FastAPI 基础解析仍生效。

列表使用只选择两列的 SQL，流程定义不会从数据库取出。SQLAlchemy RowMapping 同时支持列名和列对象作索引键，当前结果按列名转成普通字典，并用 typing.cast 明确 dict[str, Any]，避免 IDE 将键推断成宽泛联合类型；数据不转换或校验。结果放在 data.items 中，data 还包含 total、page、page_size。详情、新增和修改通过实体 to_dict 返回三个字段，不建立重复 DTO。

## 事务与日志

新增、修改、删除由 @transactional 管理，正常结束后提交，异常时回滚。Repository 只执行 add、flush、delete；flush 可以回填自增主键，表中没有需要 refresh 回读的时间字段。

业务日志记录请求ID、流程ID和操作，公共装饰器另记事务提交日志，日志不输出流程定义正文。修改接口、字段或保存规则时同步维护本文件。
