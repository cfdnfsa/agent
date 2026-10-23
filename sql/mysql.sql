-- 模型配置初始化脚本，最低支持 MySQL 5.7，在目标数据库中执行。
-- 仅创建尚不存在的表；已有表的字段变更需另写迁移脚本。
-- updated_at 由应用在修改记录时更新。
CREATE TABLE IF NOT EXISTS model_config
(
    id             BIGINT        NOT NULL AUTO_INCREMENT COMMENT '模型配置ID',
    model_name     VARCHAR(100)  NOT NULL COMMENT '模型显示名称',
    model_code     VARCHAR(255)  NOT NULL COMMENT '调用服务时使用的模型标识',
    model_provider VARCHAR(32)   NOT NULL COMMENT '接入方式：openai=OpenAI兼容，ollama=Ollama，anthropic=Anthropic，google_genai=Gemini',
    model_base_url VARCHAR(1024) NOT NULL COMMENT '模型服务Base URL',
    model_api_key  TEXT          NULL COMMENT 'API Key密文；无需密钥时为空；加解密由应用负责',
    created_at     DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    updated_at     DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '更新时间；修改记录时由应用更新',
    PRIMARY KEY (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='模型配置';
