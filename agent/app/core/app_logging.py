"""公共日志对象和请求上下文；文件名避免与标准库 logging 重名。"""

import logging
from contextvars import ContextVar


# ContextVar 为每个并发请求保留独立的值，避免不同请求的日志ID互相覆盖。
# main.py 在请求开始时设置它；同步端点在线程池执行时也会携带该上下文。
request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
# 复用 Uvicorn 的日志输出，在 PyCharm 控制台查看，不额外建立日志系统。
logger = logging.getLogger("uvicorn.error")
