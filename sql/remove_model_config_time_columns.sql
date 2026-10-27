-- 已有模型配置表的增量修改，兼容 MySQL 5.7+ 和 PostgreSQL 14+。
-- 用于仍有 created_at、updated_at 两列的旧表，一次性执行；新库直接使用初始化脚本。
ALTER TABLE model_config
    DROP COLUMN created_at,
    DROP COLUMN updated_at;
