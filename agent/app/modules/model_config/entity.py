"""模型配置实体：直接承接 JSON 字段，供数据库操作与模型调用共用。"""

from typing import Any

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, column_property, mapped_column

from app.infrastructure.database.base import Base


class ModelConfig(Base):
    """模型配置表映射，字段与 sql 目录中的初始化脚本对应。"""

    # ORM 据此找到实际数据表，继承 Base 后拥有公共 id。
    __tablename__ = "model_config"

    # 显示名称与实际模型标识分开，允许同一模型配置不同地址和凭证。
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 发起模型调用时使用的服务端模型ID，不是页面显示名称。
    model_code: Mapped[str] = mapped_column(String(255), nullable=False)
    # 原样保存接入方式；当前版本不做枚举校验，调用时交给对应模型集成处理。
    model_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    # 服务基础地址，后续调用组件会根据接入方式使用它。
    model_base_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    # 当前按约定明文保存；该字段不会出现在任何接口响应模型中。
    model_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 这是 SELECT 计算值，不新增数据库列；查询可以知道是否有 Key 而不取出密钥本身。
    has_api_key: Mapped[bool] = column_property(func.coalesce(func.length(model_api_key), 0) > 0)

    # ---------- 输出配置字段并排除 Key
    def to_dict(self) -> dict[str, Any]:
        """直接读取实体字段用于 JSON 返回，唯一排除 model_api_key，不再定义独立出参类。"""
        model_data: dict[str, Any] = {}
        for field in self.__mapper__.column_attrs:
            if field.key != "model_api_key":
                model_data[field.key] = getattr(self, field.key)
        return model_data
