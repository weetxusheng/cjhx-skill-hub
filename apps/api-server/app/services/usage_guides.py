from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.config import get_settings


def _download_url(skill_id: UUID) -> str:
    settings = get_settings()
    return f"{settings.app_base_url.rstrip('/')}{settings.api_prefix}/public/skills/{skill_id}/download"


def _normalize_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def build_default_usage_guide(
    *,
    skill_id: UUID,
    skill_name: str,
    skill_slug: str,
    summary: str,
    description: str,
    install_notes: str,
) -> dict:
    download_url = _download_url(skill_id)
    install_hint = install_notes.strip() or "请先下载 ZIP 包，解压后阅读 README.md 再继续使用。"
    skill_intro = summary.strip() or description.strip() or f"请帮我使用 {skill_name}。"
    archive_name = f"{skill_slug}.zip"

    return {
        "agent": {
            "standard_prompt": (
                f"请帮我使用 Skill Hub 技能“{skill_name}”（slug: {skill_slug}）。"
                f"先通过 {download_url} 下载当前已发布 ZIP 包，解压后阅读 README.md，"
                f"再按以下安装提示继续执行：{install_hint}。"
                f"技能简介：{skill_intro}"
            ),
            "accelerated_prompt": (
                f"请优先通过 Skill Hub 平台下载接口获取“{skill_name}”（slug: {skill_slug}）的已发布 ZIP 包：{download_url}。"
                f"下载后解压、查看 README.md，并尽量按平台推荐链路完成安装与使用。"
                f"安装提示：{install_hint}"
            ),
        },
        "human": {
            "standard_command": f'curl -L "{download_url}" -o "{archive_name}"',
            "accelerated_command": f'curl -L --retry 3 --connect-timeout 10 "{download_url}" -o "{archive_name}"',
            "post_install_command": (
                f'unzip -o "{archive_name}" -d "{skill_slug}" && cd "{skill_slug}" && '
                "echo '--- README.md ---' && cat README.md"
            ),
        },
    }


def normalize_usage_guide(
    raw_usage_guide: Any,
    *,
    skill_id: UUID,
    skill_name: str,
    skill_slug: str,
    summary: str,
    description: str,
    install_notes: str,
) -> dict:
    fallback = build_default_usage_guide(
        skill_id=skill_id,
        skill_name=skill_name,
        skill_slug=skill_slug,
        summary=summary,
        description=description,
        install_notes=install_notes,
    )

    raw = raw_usage_guide if isinstance(raw_usage_guide, dict) else {}
    agent = raw.get("agent") if isinstance(raw.get("agent"), dict) else {}
    human = raw.get("human") if isinstance(raw.get("human"), dict) else {}

    return {
        "agent": {
            "standard_prompt": _normalize_text(agent.get("standard_prompt")) or fallback["agent"]["standard_prompt"],
            "accelerated_prompt": _normalize_text(agent.get("accelerated_prompt")) or fallback["agent"]["accelerated_prompt"],
        },
        "human": {
            "standard_command": _normalize_text(human.get("standard_command")) or fallback["human"]["standard_command"],
            "accelerated_command": _normalize_text(human.get("accelerated_command")) or fallback["human"]["accelerated_command"],
            "post_install_command": _normalize_text(human.get("post_install_command")) or fallback["human"]["post_install_command"],
        },
    }
