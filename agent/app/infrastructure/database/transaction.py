"""同步 Service 的事务装饰器：复用当前请求会话，由 SQLAlchemy 提交或回滚。"""

from collections.abc import Callable
from functools import wraps

from sqlalchemy.orm import Session

from app.core.app_logging import logger, request_id_context


# ---------- 为同步业务方法统一管理事务
def transactional[**Parameters, ReturnType](
    business_method: Callable[Parameters, ReturnType],
) -> Callable[Parameters, ReturnType]:
    """给持有 db_session 的同步 Service 方法添加事务。

    Args:
        business_method: 被 @transactional 标记的方法，所属对象必须有 db_session 属性。

    Returns:
        参数和返回类型保持不变的方法；正常执行后提交，异常时回滚并继续向外抛出。
        只管理当前方法的事务，不支持异步方法、嵌套调用或加入已有事务。
    """
    # wraps 保留原方法的名称、文档和签名，便于接口检查与日志排查。
    # ---------- 在当前请求会话中执行业务方法
    @wraps(business_method)
    def run_in_transaction(*args: Parameters.args, **kwargs: Parameters.kwargs) -> ReturnType:
        """args 首项是 Service 的 self，其余位置参数和 kwargs 原样交给业务方法。"""
        # getattr 读取 self.db_session，不创建新会话，Repository 仍使用同一个会话。
        db_session: Session = getattr(args[0], "db_session")
        with db_session.begin():
            result = business_method(*args, **kwargs)
        # 只有退出 begin 且提交成功后才记录此日志；提交失败会交给公共异常处理。

        logger.info("请求ID=%s 操作=数据库事务提交 方法=%s", request_id_context.get(), business_method.__qualname__)

        return result

    return run_in_transaction
