# 数据库初始化 SQL

在已创建的目标数据库中，先执行对应的建表脚本，需要示例提示词时再执行公共数据脚本：

1. MySQL 执行 mysql.sql，PostgreSQL 执行 pgsql.sql。
2. 执行 init_data.sql，补齐四份示例提示词。

| 文件 | 支持版本 | 内容 |
|---|---|---|
| [mysql.sql](mysql.sql) | MySQL 5.7+ | 模型、流程、提示词配置表 |
| [pgsql.sql](pgsql.sql) | PostgreSQL 14+ | 模型、流程、提示词配置表和字段注释 |
| [init_data.sql](init_data.sql) | MySQL 5.7+ / PostgreSQL 14+ | 公共初始化数据，包含四份示例提示词 |

mysql.sql、pgsql.sql 只创建尚不存在的表，不插入数据，也不包含删表、清库或已有表迁移。已有表通过 CREATE TABLE IF NOT EXISTS 跳过建表；init_data.sql 单独维护初始化数据，执行前需要先有对应表。后端启动不会自动执行这些脚本。

workflow_config 只有 id、workflow_name、workflow_definition 三个字段；定义内容保存为普通文本，MySQL 使用 LONGTEXT，PostgreSQL 使用 TEXT，不使用 JSON/JSONB 列。model_config 同样不再维护创建时间和更新时间。

prompt_config 只有 id、prompt_name、prompt_content 三个字段：自增主键、名称、正文。正文使用 MySQL LONGTEXT、PostgreSQL TEXT；名称允许重复，不增加时间、状态或版本字段，也不建立数据库外键。[提示词管理接口](../agent/app/modules/prompt_config/README.md) 已提供基础增删改查，列表只读 ID、名称，详情读取正文。LLM 节点通过流程定义中的 config.prompt_config_id 选择提示词，运行时从缓存读取正文作为系统消息，无需增加数据库字段。

后端当前连接 PostgreSQL，应用暂未配置 MySQL 驱动。修改表结构时同步检查对应 ORM 实体和包文档；已有表需要变更时单独提供迁移 SQL。

## 示例提示词

init_data.sql 包含以下四份普通文本模板，两种数据库共用同一份内容，执行后可在前端“提示词配置”页面查看、编辑：

| 名称 | 用途 |
|---|---|
| 通用问答助手 | 清晰、简洁地回答当前问题 |
| 问题分析助手 | 提取用户目标、已知条件和缺失信息 |
| 资料整理助手 | 整理输入资料，保留关键事实并指出缺失、冲突 |
| 结果汇总助手 | 结合原始问题和各上游结果生成最终回答 |

初始化不指定主键，按名称检查已有记录；重复执行时跳过同名模板，不覆盖已有正文。此规则仅用于初始化，管理接口仍允许名称重复。删除或改名后再次执行初始化脚本，会补回缺少原名称的示例。

模板不含待替换的变量表达式；LLM 节点把所选正文作为系统消息，上游输入作为用户消息，两者分开传递。已有 prompt_config 表的数据库，可直接执行 init_data.sql，无需重新建表。
