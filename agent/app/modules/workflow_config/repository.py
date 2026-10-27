"""流程配置的数据库操作：使用 SQLAlchemy ORM，提交或回滚交给 Service 的事务。"""

from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.workflow_config.entity import WorkflowConfig


class WorkflowConfigRepository:
    """保存流程实体，列表只查询 ID 和名称，详情才读取完整定义文本。"""

    # ---------- 初始化流程配置数据库操作
    def __init__(self, db_session: Session):
        """db_session 是当前请求的会话，与 Service 共用，不在这里创建或关闭。"""
        self.db_session = db_session

    # ---------- 按主键查询流程配置
    def get_by_id(self, workflow_id: int) -> WorkflowConfig | None:
        """workflow_id 是流程主键；返回完整实体，记录不存在时返回 None。"""
        workflow_config = self.db_session.get(WorkflowConfig, workflow_id)
        # 兼容部分 PyCharm 的泛型推断；只提示返回类型，不转换实体。
        return cast(WorkflowConfig | None, workflow_config)

    # ---------- 分页查询流程概要
    def list_page(self, page: int, page_size: int) -> list[dict[str, Any]]:
        """查询一页流程概要，不读取 workflow_definition 大文本。

        Args:
            page: 页码，从 1 开始，当前不额外校验范围。
            page_size: 每页数量，沿用现有分页接口的直接传值方式。

        Returns:
            只包含 id、workflow_name 的字典列表，可能为空。
        """
        workflow_query = (
            select(WorkflowConfig.id, WorkflowConfig.workflow_name)
            # 主键倒序显示最近新增的流程，分页在数据库中完成。
            .order_by(WorkflowConfig.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        # RowMapping 同时允许列对象作为索引键；这里按列名生成字典，用 cast 明确字符串键类型。
        return [
            cast(dict[str, Any], dict(workflow_row))
            for workflow_row in self.db_session.execute(workflow_query).mappings()
        ]

    # ---------- 查询流程配置总数
    def count(self) -> int:
        """只执行 COUNT，返回流程记录总数，不加载流程定义。"""
        workflow_count_query = select(func.count()).select_from(WorkflowConfig)
        return self.db_session.scalar(workflow_count_query) or 0

    # ---------- 保存流程配置
    def save(self, workflow_config: WorkflowConfig) -> WorkflowConfig:
        """保存传入的实体并取得自增主键，返回同一个对象；这里不提交事务。"""
        self.db_session.add(workflow_config)
        # flush 执行待保存的 SQL 并回填主键；这张表没有需要 refresh 回读的时间字段。
        self.db_session.flush()
        return workflow_config

    # ---------- 删除流程配置
    def delete(self, workflow_config: WorkflowConfig) -> None:
        """标记传入实体为待删除，实际提交由调用方的 @transactional 负责。"""
        self.db_session.delete(workflow_config)
