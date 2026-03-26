from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PagedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


def success_response(data: Any, message: str = "ok") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def paged_success_response(items: list[Any], total: int, page: int, page_size: int, message: str = "ok") -> dict[str, Any]:
    payload = PagedResponse[Any](items=items, total=total, page=page, page_size=page_size)
    return success_response(payload.model_dump(mode="json"), message=message)
