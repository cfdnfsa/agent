"""提示词配置的数据库操作：只执行 ORM 查询与保存，事务由 Service 管理。"""

from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.prompt_config.entity import PromptConfig


class PromptConfigRepository:
    """读写提示词表，列表只查 ID、名称，详情才加载正文。"""

    # ---------- 初始化提示词配置数据库操作
    def __init__(self, db_session: Session):
        """db_session 来自当前请求，与 Service 共用，不在这里创建或关闭。"""
        self.db_session = db_session

    # ---------- 按主键查询提示词配置
    def get_by_id(self, prompt_id: int) -> PromptConfig | None:
        """prompt_id 为提示词主键，返回完整实体；不存在时返回 None。"""
        prompt_config = self.db_session.get(PromptConfig, prompt_id)
        # 只明确实例返回类型，兼容部分 PyCharm 的推断，不转换或复制实体。
        return cast(PromptConfig | None, prompt_config)

    # ---------- 分页查询提示词概要
    def list_page(self, page: int, page_size: int) -> list[dict[str, Any]]:
        """查询一页 ID、名称，避免列表加载提示词正文。

        Args:
            page: 页码，从 1 开始，直接使用调用方传入值。
            page_size: 本页数量，不增加额外范围校验。

        Returns:
            按主键倒序排列的概要列表，没有记录时为空列表。
        """
        prompt_query = (
            select(PromptConfig.id, PromptConfig.prompt_name)
            .order_by(PromptConfig.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        prompt_summaries: list[dict[str, Any]] = []
        for prompt_row in self.db_session.execute(prompt_query).mappings():
            # RowMapping 还支持列对象作键，这里明确按字符串列名返回。
            prompt_summary = cast(dict[str, Any], dict(prompt_row))
            prompt_summaries.append(prompt_summary)
        return prompt_summaries

    # ---------- 查询提示词配置总数
    def count(self) -> int:
        """只统计记录数，不加载提示词正文。"""
        prompt_count_query = select(func.count()).select_from(PromptConfig)
        return self.db_session.scalar(prompt_count_query) or 0

    # ---------- 保存提示词配置
    def save(self, prompt_config: PromptConfig) -> PromptConfig:
        """保存传入实体，取得主键后返回同一个对象，提交交给 Service。"""
        self.db_session.add(prompt_config)
        # flush 执行待保存的 SQL 并回填主键，此时尚未提交，仍可回滚。
        self.db_session.flush()
        return prompt_config

    # ---------- 删除提示词配置
    def delete(self, prompt_config: PromptConfig) -> None:
        """标记删除传入实体，由 Service 的事务提交实际删除。"""
        self.db_session.delete(prompt_config)
