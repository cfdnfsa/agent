"""提示词配置实体：保存名称和正文，供配置管理与后续流程节点复用。"""

from typing import Any

from sqlalchemy import String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class PromptConfig(Base):
    """提示词配置表映射，继承公共主键，不增加时间、状态或版本字段。

    Attributes:
        prompt_name: 提示词显示名称，允许重复，方便后续复制复用。
        prompt_content: 提示词正文，按输入原文保存。
    """

    __tablename__ = "prompt_config"

    # 名称供列表展示，长度与初始化 SQL 保持一致。
    prompt_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 正文使用普通文本列，MySQL 对应 LONGTEXT，PostgreSQL 对应 TEXT。
    prompt_content: Mapped[str] = mapped_column(
        Text().with_variant(LONGTEXT(), "mysql"), nullable=False
    )

    # ---------- 输出提示词配置字段
    def to_dict(self) -> dict[str, Any]:
        """读取实体的三个映射字段用于 JSON 返回，正文保持原文。"""
        prompt_data: dict[str, Any] = {}
        for field in self.__mapper__.column_attrs:
            prompt_data[field.key] = getattr(self, field.key)
        return prompt_data
