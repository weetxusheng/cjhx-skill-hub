"""请求级上下文：在异步链中传递 request_id（供审计日志等使用）。"""

from __future__ import annotations

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str | None) -> None:
    """设置当前上下文 request_id（一般由中间件调用）。"""
    request_id_var.set(request_id)


def get_request_id() -> str | None:
    """读取当前上下文 request_id；无则 None。"""
    return request_id_var.get()
