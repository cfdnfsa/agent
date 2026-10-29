"""流程配置实体：只保存主键、名称和流程定义文本，不解析或执行流程。"""

from typing import Any

from sqlalchemy import String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class WorkflowConfig(Base):
    """流程配置表映射，一条记录对应一个流程，没有创建时间和更新时间字段。"""

    __tablename__ = "workflow_config"

    # 页面展示的流程名称；当前只保存原始值，不增加唯一性或长度校验。
    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 内容可以是 JSON 字符串，但数据库使用文本列；MySQL 使用 LONGTEXT，PostgreSQL 使用 TEXT。
    workflow_definition: Mapped[str] = mapped_column(
        Text().with_variant(LONGTEXT(), "mysql"), nullable=False
    )

    # ---------- 输出流程配置字段
    def to_dict(self) -> dict[str, Any]:
        """直接输出实体的三个映射字段，流程定义保持字符串，不转换为 JSON 对象。"""
        return {field.key: getattr(self, field.key) for field in self.__mapper__.column_attrs}
