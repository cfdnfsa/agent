"""模型表的数据库操作入口：只使用 SQLAlchemy ORM，不在这里决定事务提交。"""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.model_config.entity import ModelConfig


class ModelConfigRepository:
    """封装模型表的 ORM 操作，事务由业务服务统一提交。"""

    def __init__(self, db_session: Session):
        """接收当前请求的会话，与同次业务中的其他数据库操作共用事务。"""
        self.db_session = db_session

    def get_by_id(self, model_id: int) -> type[ModelConfig] | None:
        """按主键查询单条模型配置。"""
        # Session.get 按主键定位记录，不存在时返回 None，交给 Service 处理。
        return self.db_session.get(ModelConfig, model_id)

    def list_page(self, page: int, page_size: int) -> Sequence[ModelConfig]:
        """按主键倒序分页，限制每次加载的配置数量。"""
        model_config_query = (
            # select(ModelConfig) 根据实体映射生成查询，不是拼接 SQL 字符串。
            select(ModelConfig)
            # 主键倒序保证排序明确，也让最新创建的配置排在前面。
            .order_by(ModelConfig.id.desc())
            # 页码从 1 开始，offset 是跳过的记录数，limit 限制本次返回数量。
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        # scalars 提取实体对象，all 取出本页结果；前面的 limit 已限制查询规模。
        return self.db_session.scalars(model_config_query).all()

    def count(self) -> int:
        """查询总数量，不加载完整记录。"""
        model_config_count_query = select(func.count()).select_from(ModelConfig)
        # scalar 取 COUNT 查询的单个数字，不会把全部模型记录加载到内存。
        return self.db_session.scalar(model_config_count_query) or 0

    def save(self, model_config: ModelConfig) -> ModelConfig:
        """保存并刷新主键和时间字段，不在仓储中提交事务。"""
        # 新实体被标记为待插入；已经查询出的实体会由 ORM 跟踪字段变化。
        self.db_session.add(model_config)
        # flush 把 INSERT/UPDATE 发给数据库，但还没有 commit，仍然可以回滚。
        self.db_session.flush()
        # 回读数据库生成的主键、时间，确保接口响应使用实际保存的值。
        self.db_session.refresh(model_config)
        return model_config

    def delete(self, model_config: ModelConfig) -> None:
        """删除已经按主键定位的配置，不执行无条件删除。"""
        # 先标记待删除，实际 DELETE 由 Service 结束事务时统一执行并提交。
        self.db_session.delete(model_config)
