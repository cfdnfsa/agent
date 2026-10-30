# 数据库初始化 SQL

在已创建的目标数据库中，按数据库类型执行对应脚本：

| 文件 | 支持版本 | 内容 |
|---|---|---|
| mysql.sql | MySQL 5.7+ | 模型配置表、流程配置表、提示词配置表 |
| pgsql.sql | PostgreSQL 14+ | 模型配置表、流程配置表、提示词配置表和字段注释 |

mysql.sql、pgsql.sql 这两个初始化脚本只创建尚不存在的表，不包含删表、清库或已有表迁移。后端启动不会自动执行脚本。已有 model_config、workflow_config 表时，对应 CREATE TABLE IF NOT EXISTS 会跳过建表，新增加的 prompt_config 会独立创建。

workflow_config 只有 id、workflow_name、workflow_definition 三个字段；定义内容保存为普通文本，MySQL 使用 LONGTEXT，PostgreSQL 使用 TEXT，不使用 JSON/JSONB 列。model_config 同样不再维护创建时间和更新时间。

prompt_config 只有 id、prompt_name、prompt_content 三个字段：自增主键、名称、正文。正文使用 MySQL LONGTEXT、PostgreSQL TEXT；名称允许重复，不增加时间、状态或版本字段，也不建立数据库外键。[提示词管理接口](../agent/app/modules/prompt_config/README.md) 已提供基础增删改查，列表只读 ID、名称，详情读取正文。后续 LLM 节点通过流程定义中的 prompt_config_id 引用提示词，输入来源选项仍由节点维护；节点接入尚未实现。

后端当前连接 PostgreSQL，应用暂未配置 MySQL 驱动。修改表结构时同步检查对应 ORM 实体和包文档；已有表需要变更时单独提供迁移 SQL。
