-- 模型配置与流程配置初始化脚本，最低支持 MySQL 5.7，在目标数据库中执行。
-- 仅创建尚不存在的表；已有表的字段变更需另写迁移脚本。
CREATE TABLE IF NOT EXISTS model_config
(
    id             BIGINT        NOT NULL AUTO_INCREMENT COMMENT '模型配置ID',
    model_name     VARCHAR(100)  NOT NULL COMMENT '模型显示名称',
    model_code     VARCHAR(255)  NOT NULL COMMENT '调用服务时使用的模型标识',
    model_provider VARCHAR(32)   NOT NULL COMMENT '接入方式：openai=OpenAI兼容，ollama=Ollama，anthropic=Anthropic，google_genai=Gemini',
    model_base_url VARCHAR(1024) NOT NULL COMMENT '模型服务Base URL',
    model_api_key  TEXT          NULL COMMENT 'API Key；当前明文保存；无需密钥时为空；查询接口不返回',
    PRIMARY KEY (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='模型配置';

-- 流程定义按文本原样保存，不使用 JSON 类型，也不增加节点表、连线表。
CREATE TABLE IF NOT EXISTS workflow_config
(
    id                  BIGINT       NOT NULL AUTO_INCREMENT COMMENT '流程配置ID',
    workflow_name       VARCHAR(100) NOT NULL COMMENT '流程名称',
    workflow_definition LONGTEXT     NOT NULL COMMENT '流程定义文本；保存JSON字符串，当前不解析或校验',
    PRIMARY KEY (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='流程配置';
