"""数据库实体共享的映射基础：主键、创建时间、更新时间。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """ORM 公共字段；只声明映射，应用启动时不自动创建数据库表。"""

    # Mapped[int] 表示 Python 字段类型，mapped_column 描述数据库列。
    # 业务实体继承 Base 后自动具有这些字段，无需重复声明。
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # server_default 表示插入时交给数据库生成时间，对应建表脚本中的默认值。
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    # onupdate 会在 ORM 真正更新记录时附加数据库当前时间，不是数据库触发器。
    # 如果以后绕过 ORM 直接更新表，也需要由更新方维护 updated_at。
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
