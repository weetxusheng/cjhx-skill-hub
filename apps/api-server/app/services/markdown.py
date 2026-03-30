from __future__ import annotations

from functools import lru_cache

from markdown_it import MarkdownIt


@lru_cache
def _markdown_renderer() -> MarkdownIt:
    """构建并缓存 Markdown 渲染器实例。

    配置:
    - commonmark 语法
    - 禁止原始 HTML
    - 启用 linkify 与 typographer
    """
    return MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})


def render_markdown_html(markdown: str) -> str:
    """将 Markdown 文本渲染为 HTML 字符串。"""
    return _markdown_renderer().render(markdown)
