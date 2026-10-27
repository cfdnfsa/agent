"""公共业务异常：描述业务失败原因，不依赖 FastAPI 或具体业务模块。"""

from http import HTTPStatus


class BusinessError(Exception):
    """业务未满足预期条件时抛出，由统一异常处理器生成接口响应。"""

    # ---------- 初始化业务异常
    def __init__(self, message: str, status_code: int = HTTPStatus.BAD_REQUEST):
        """message 是可公开说明，status_code 是 HTTP 状态码，默认 400 表示请求不合法。"""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
