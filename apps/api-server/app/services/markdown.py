from __future__ import annotations

from functools import lru_cache

from markdown_it import MarkdownIt


@lru_cache
def _markdown_renderer() -> MarkdownIt:
    return MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})


def render_markdown_html(markdown: str) -> str:
    return _markdown_renderer().render(markdown)
