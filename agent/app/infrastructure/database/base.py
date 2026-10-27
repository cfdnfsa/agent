"""数据库实体共享的映射基础：提供自增主键，其他字段由业务实体按需声明。"""

from sqlalchemy import BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """ORM 公共主键；只声明映射，应用启动时不自动创建数据库表。"""

    # Mapped[int] 表示 Python 字段类型，mapped_column 描述数据库列。
    # 业务实体继承 Base 后自动具有 id，其他字段由各实体声明。
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
