# 提示词配置管理

本包提供提示词名称和正文的基础增删改查。正文原样保存，名称允许重复；流程节点选择和使用提示词后续接入。

| 文件 | 职责 |
|---|---|
| entity.py | 映射 prompt_config 表的三个字段，提供 to_dict |
| repository.py | ORM 查询、保存、删除，列表只查 ID 和名称 |
| service.py | 配置增删改查，写入使用公共 @transactional |
| router.py | 注入当前请求的服务，包装公共 Result、Page |

调用关系：main.py 注册 router → Service → Repository。Service 和 Repository 共用当前请求的 db_session，Repository 不提交事务；@transactional 在写方法正常结束后提交，异常时回滚。

## 表与接口

表名 prompt_config，仅包含 id、prompt_name、prompt_content；正文使用 PostgreSQL TEXT、MySQL LONGTEXT，无时间、状态或版本字段。先执行 [SQL 初始化脚本](../../../../sql/README.md) 创建表，应用启动不会自动建表。

| 方法 | 路径 | 行为 |
|---|---|---|
| POST | /api/prompt-configs | 新增，成功 HTTP 201，返回完整配置 |
| GET | /api/prompt-configs?page=1&page_size=20 | 按 ID 倒序分页，仅返回 ID、名称 |
| GET | /api/prompt-configs/{id} | 详情，包含正文 |
| PUT | /api/prompt-configs/{id} | 更新实际提交的字段，未提交字段保持原值 |
| DELETE | /api/prompt-configs/{id} | 删除，成功 HTTP 200、data=null |

新增或修改示例：

```json
{
  "prompt_name": "问题分析助手",
  "prompt_content": "你是问题分析助手，负责理解用户需求并提取关键信息。"
}
```

写接口直接接收 JSON 字典并维护实体，不增加重复 DTO、名称去重、额外格式校验或自动 trim。正文中的换行、变量占位文字原样保存，当前不解析模板变量。数据库非空、长度约束和 FastAPI 的基础 JSON、整数解析仍生效。

列表返回 data.items、total、page、page_size，不查询正文；新增、详情和修改通过实体 to_dict 返回三个字段。找不到记录时使用公共 BusinessError，返回 HTTP 404 和“提示词配置不存在”。

写操作日志包含请求ID、提示词ID和动作，不输出正文；事务提交日志由公共装饰器记录。修改接口或行为时同步维护本文档。
