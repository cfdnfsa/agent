# 数据库初始化 SQL

在已创建的目标数据库中，按数据库类型执行对应脚本：

| 文件 | 支持版本 | 内容 |
|---|---|---|
| mysql.sql | MySQL 5.7+ | 模型配置表、流程配置表 |
| pgsql.sql | PostgreSQL 14+ | 模型配置表、流程配置表和字段注释 |
| remove_model_config_time_columns.sql | MySQL 5.7+ / PostgreSQL 14+ | 旧模型表删除 created_at、updated_at 两列 |

mysql.sql、pgsql.sql 这两个初始化脚本只创建尚不存在的表，不包含删表、清库或已有表迁移。后端启动不会自动执行脚本。已有 model_config 表时，对应 CREATE TABLE IF NOT EXISTS 会跳过建表，新增加的 workflow_config 会独立创建。

workflow_config 只有 id、workflow_name、workflow_definition 三个字段；定义内容保存为普通文本，MySQL 使用 LONGTEXT，PostgreSQL 使用 TEXT，不使用 JSON/JSONB 列。model_config 同样不再维护创建时间和更新时间。

已有 model_config 表且仍包含两个时间字段时，单独执行 remove_model_config_time_columns.sql；该脚本一次性执行，删除这两列及其存储的时间数据。新库不需要执行增量脚本。初始化脚本中的 CREATE TABLE IF NOT EXISTS 不会修改旧表。

后端当前连接 PostgreSQL，应用暂未配置 MySQL 驱动。修改表结构时同步检查对应 ORM 实体和包文档；已有表需要变更时单独提供迁移 SQL。
