"""接口数据结构：校验请求字段，并限制哪些字段可以返回给前端。"""

from datetime import datetime
from enum import StrEnum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, SecretStr


class ModelProvider(StrEnum):
    """可保存的模型接入方式；本次只实现配置管理，不发起模型调用。"""

    # 左侧是代码中的枚举名称，右侧字符串用于接口传参和数据库保存。
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GOOGLE_GENAI = "google_genai"


class ModelConfigCreate(BaseModel):
    """新增模型配置，密钥允许省略。"""

    # 拒绝未定义字段，避免字段拼错后被悄悄忽略；普通字符串去掉首尾空格。
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Field 同时定义校验规则和 /docs 中的说明；校验失败不会进入业务方法。
    model_name: str = Field(min_length=1, max_length=100, description="模型显示名称")
    model_code: str = Field(min_length=1, max_length=255, description="实际模型标识")
    model_provider: ModelProvider = Field(description="模型接入方式")
    # AnyHttpUrl 只允许 HTTP/HTTPS 地址，也允许本地地址和 IP。
    model_base_url: AnyHttpUrl = Field(max_length=1024, description="模型服务 Base URL")
    # SecretStr 只避免打印请求对象时显示原 Key，不改变明文保存的约定。
    model_api_key: SecretStr | None = Field(default=None, description="API Key，无需密钥时可不传")


class ModelConfigUpdate(ModelConfigCreate):
    """整体修改配置；Key 未传则保留，传 null 或空字符串则清除。"""

    # 复用新增时的四个必填配置项，只补充修改 Key 的行为说明。
    # 是否实际提交这个字段，由 Service 通过 model_fields_set 区分。
    model_api_key: SecretStr | None = Field(
        default=None,
        description="不传则保留原 Key；null 或空字符串清除；其他值替换原 Key",
    )


class ModelConfigResponse(BaseModel):
    """模型配置出参，明确排除 API Key 明文。"""

    # model_validate 可以直接读取 ORM 实体属性，无需手工组装响应字典。
    model_config = ConfigDict(from_attributes=True)

    # 这里只声明可公开字段，没有 model_api_key，因此不会把 Key 序列化出去。
    id: int
    model_name: str
    model_code: str
    model_provider: ModelProvider
    model_base_url: str
    # 对应实体的计算属性，页面可以显示“已配置”或“未配置”。
    has_api_key: bool
    created_at: datetime
    updated_at: datetime


