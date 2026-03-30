"""通用 API 响应包装与分页结构。"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PagedResponse(BaseModel, Generic[T]):
    """标准分页载荷：列表 + 总数 + 页码参数。"""

    items: list[T]
    total: int
    page: int
    page_size: int


def success_response(data: Any, message: str = "ok") -> dict[str, Any]:
    """统一成功体：`{ code: 0, message, data }`。"""
    return {"code": 0, "message": message, "data": data}


def paged_success_response(items: list[Any], total: int, page: int, page_size: int, message: str = "ok") -> dict[str, Any]:
    """分页成功体：data 内为 PagedResponse 序列化结果。"""
    payload = PagedResponse[Any](items=items, total=total, page=page, page_size=page_size)
    return success_response(payload.model_dump(mode="json"), message=message)
