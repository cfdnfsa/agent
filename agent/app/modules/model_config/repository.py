"""模型表的数据库操作入口：只使用 SQLAlchemy ORM，不在这里决定事务提交。"""

from collections.abc import Sequence
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session, defer

from app.modules.model_config.entity import ModelConfig


class ModelConfigRepository:
    """封装模型表的 ORM 操作，事务由业务服务统一提交。"""

    # ---------- 初始化模型配置数据库操作
    def __init__(self, db_session: Session):
        """db_session 为当前请求的会话，事务由调用方 Service 控制。"""
        self.db_session = db_session

    # ---------- 按主键查询模型配置
    def get_by_id(self, model_id: int, include_api_key: bool = False) -> ModelConfig | None:
        """按ID返回实体；普通查询不取 Key，模型测试、问答时传 include_api_key=True。"""
        options = [] if include_api_key else [defer(ModelConfig.model_api_key, raiseload=True)]
        model_config = self.db_session.get(ModelConfig, model_id, options=options)
        # 部分 PyCharm 版本误将 get 的结果推断成类；cast 只明确类型，不转换对象。
        return cast(ModelConfig | None, model_config)

    # ---------- 分页查询模型配置
    def list_page(self, page: int, page_size: int) -> Sequence[ModelConfig]:
        """按主键倒序查询一页实体。

        Args:
            page: 页码，从 1 开始；当前不额外校验范围。
            page_size: 本次加载数量，不再增加每页 100 条的限制。

        Returns:
            当前页的实体列表，可能为空。
        """
        model_config_query = (
            # select(ModelConfig) 根据实体映射生成查询，不是拼接 SQL 字符串。
            select(ModelConfig)
            .options(defer(ModelConfig.model_api_key, raiseload=True))
            # 主键倒序保证排序明确，也让最新创建的配置排在前面。
            .order_by(ModelConfig.id.desc())
            # 页码从 1 开始，offset 是跳过的记录数，limit 限制本次返回数量。
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        # scalars 提取实体对象，all 取出本页结果；前面的 limit 已限制查询规模。
        return self.db_session.scalars(model_config_query).all()

    # ---------- 查询模型配置总数
    def count(self) -> int:
        """返回配置总条数；只执行 COUNT，不加载实体。"""
        model_config_count_query = select(func.count()).select_from(ModelConfig)
        # scalar 取 COUNT 查询的单个数字，不会把全部模型记录加载到内存。
        return self.db_session.scalar(model_config_count_query) or 0

    # ---------- 保存模型配置
    def save(self, model_config: ModelConfig) -> ModelConfig:
        """保存传入的 model_config 实体，刷新后返回同一个对象，由 Service 决定提交。"""
        # 新实体被标记为待插入；已经查询出的实体会由 ORM 跟踪字段变化。
        self.db_session.add(model_config)
        # flush 把 INSERT/UPDATE 发给数据库，但还没有 commit，仍然可以回滚。
        self.db_session.flush()
        # 回读数据库生成的主键、时间，确保接口响应使用实际保存的值。
        self.db_session.refresh(model_config)
        return model_config

    # ---------- 删除模型配置
    def delete(self, model_config: ModelConfig) -> None:
        """model_config 是已查询到的实体；这里只标记删除，由 Service 事务完成提交。"""
        # 先标记待删除，实际 DELETE 由 Service 结束事务时统一执行并提交。
        self.db_session.delete(model_config)
