"""公共接口结构：统一返回外层格式，并复用分页数据结构。"""

from http import HTTPStatus
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


# T 表示可替换的数据类型，例如 Result[模型详情]、Page[模型详情]。
T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """接口统一返回：成功 code 为 0，失败 code 使用对应的 HTTP 状态码。"""

    code: int = Field(default=0, description="结果码：0 成功，失败时为 HTTP 状态码")
    message: str = Field(default="成功", description="结果说明")
    data: T | None = Field(default=None, description="业务数据，无数据时为 null")


class Page(BaseModel, Generic[T]):
    """通用分页数据，作为 Result.data 使用，不额外包装成功或失败信息。"""

    items: list[T] = Field(description="本页记录")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")


# 各 Router 共用错误文档，避免 /docs 仍显示 FastAPI 默认的 detail 格式。
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    HTTPStatus.BAD_REQUEST: {"model": Result[None], "description": "业务请求不合法"},
    HTTPStatus.NOT_FOUND: {"model": Result[None], "description": "资源不存在"},
    HTTPStatus.UNPROCESSABLE_ENTITY: {
        "model": Result[list[dict[str, Any]]],
        "description": "参数校验失败，data 仅包含错误类型、字段位置和说明",
    },
    HTTPStatus.INTERNAL_SERVER_ERROR: {"model": Result[None], "description": "服务端处理失败"},
}
