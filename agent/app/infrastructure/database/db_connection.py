"""数据库连接管理：创建连接池，并为每个请求提供独立的数据库会话。"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


app_settings = get_settings()

# 使用 URL 对象处理密码中的 @ 等特殊字符，避免手工拼接连接字符串。
database_url = URL.create(
    # postgresql 是数据库类型，psycopg 是 Python 连接 PostgreSQL 使用的驱动。
    drivername="postgresql+psycopg",
    username=app_settings.db_user,
    password=app_settings.db_password.get_secret_value(),
    host=app_settings.db_host,
    port=app_settings.db_port,
    database=app_settings.db_name,
)

# Engine 在进程内复用连接池；创建它不立即连接数据库，查询时才取连接。
# pool_pre_ping 检查连接是否有效；hide_parameters 隐藏异常日志中的 SQL 参数。
db_engine = create_engine(database_url, pool_pre_ping=True, hide_parameters=True)

# sessionmaker 是“创建会话的工厂”，不是所有请求共享的一个 Session。
# autoflush=False：由 Repository 的 flush 决定何时把改动发送给数据库。
# expire_on_commit=False：提交后保留已读取字段，避免生成响应时又隐式查库。
db_session_factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)


# ---------- 提供当前请求的数据库会话
def get_db_session() -> Iterator[Session]:
    """为当前请求提供独立的数据库会话。

    Yields:
        一个 Session 对象，由 Depends 注入给需要数据库的服务。
        请求结束后关闭会话、归还连接，并回滚尚未提交的事务。
    """
    with db_session_factory() as db_session:
        # Depends 把 yield 出去的会话交给接口；请求结束后回到这里退出 with。
        # 退出时关闭会话、归还连接；写入提交仍由 Service 的事务代码决定。
        yield db_session


# 公共依赖别名：声明参数为 DbSession 时，FastAPI 会通过 get_db_session 提供会话。
# 这里只保存类型和依赖规则，不会创建会话，也不会让不同请求共享同一个 Session。
DbSession = Annotated[Session, Depends(get_db_session)]
