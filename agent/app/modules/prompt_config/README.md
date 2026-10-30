# 提示词配置管理

本包提供提示词名称和正文的基础增删改查。正文原样保存，名称允许重复；LLM 节点通过 config.prompt_config_id 选择提示词，运行准备阶段从本包缓存读取完整实体。

前端通过导航“提示词配置”或 `/#/prompt-configs` 维护，提供分页、新增、编辑、只读详情和删除确认；编辑和详情单独读取正文。页面实现见 [前端页面说明](../../../../web/src/views/README.md)。

| 文件 | 职责 |
|---|---|
| entity.py | 映射 prompt_config 表的三个字段，提供 to_dict |
| repository.py | ORM 查询、保存、删除，列表只查 ID 和名称 |
| service.py | 配置增删改查，事务提交成功后清除对应缓存 |
| cache.py | 按ID读取完整实体，优先命中内存，未命中用短会话查库 |
| router.py | 注入当前请求的服务，包装公共 Result、Page |

调用关系：main.py 注册 router → Service → Repository。Service 和 Repository 共用当前请求的 db_session，Repository 不提交事务。create、update、delete 调用各自的 *_in_transaction 方法，由 @transactional 提交或回滚；成功返回后外层方法再清除缓存，失败时不提前清除。

## 提示词配置缓存

内部读取入口为 cache.py 的 get_prompt_config(prompt_id)，返回 PromptConfig 或 None。缓存使用 dict[int, PromptConfig]：命中直接返回完整实体，未命中自行创建短查询会话，查询事务结束并关闭会话后缓存实体；找不到返回 None，不缓存空值。Session 使用现有连接池和 expire_on_commit=False，缓存仅保存已加载的配置，供内部只读使用。

加载和失效共用线程锁，避免并发查询在清除后把旧内容重新写回。新增、修改、删除提交成功后调用 invalidate_prompt_config；修改主键时同时清除旧ID和新ID。写入使用请求会话单独查询实体，不修改已交给调用方的缓存实体。DEBUG 日志只记录请求ID、提示词ID和命中情况，不记录正文。

管理接口列表、详情仍直接查库，不走缓存。workflow_nodes/factory.py 在准备选中提示词的 LLM 节点时调用缓存入口，找不到引用记录时返回 HTTP 404；节点内不查库。正文原样作为系统消息，上游内容作为用户消息，不进行模板变量替换。缓存每个进程一份，重启清空；直接在数据库里修改提示词不会自动刷新，多进程之间也不自动同步。

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
