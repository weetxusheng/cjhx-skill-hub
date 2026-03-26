from __future__ import annotations

"""0009 seed initial data

Revision ID: 0009_seed_initial_data
Revises: 0008_create_indexes_and_triggers
Create Date: 2026-03-25 00:13:00
"""

from typing import Sequence

from alembic import op
from argon2 import PasswordHasher
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0009_seed_initial_data"
down_revision: str | None = "0008_create_indexes_and_triggers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROLE_SEED = [
    ("viewer", "浏览者"),
    ("contributor", "贡献者"),
    ("reviewer", "审核员"),
    ("publisher", "发布者"),
    ("admin", "管理员"),
]

CATEGORY_SEED = [
    ("AI 智能", "ai-intelligence", "SparkleOutlined", "智能体、模型与推理增强类技能", 10),
    ("开发工具", "developer-tools", "CodeOutlined", "开发、调试、构建与代码协作技能", 20),
    ("效率提升", "productivity", "ThunderboltOutlined", "办公、自动化、效率优化技能", 30),
    ("数据分析", "data-analysis", "BarChartOutlined", "数据处理、报表、可视化技能", 40),
    ("内容创作", "content-creation", "EditOutlined", "文本、图片、音视频创作技能", 50),
    ("安全合规", "security-compliance", "SafetyCertificateOutlined", "安全扫描、审计、合规检查技能", 60),
    ("通讯协作", "communication-collaboration", "TeamOutlined", "IM、协同、邮件与知识流转技能", 70),
]


def upgrade() -> None:
    conn = op.get_bind()
    password_hash = PasswordHasher().hash("ChangeMe123!")

    for code, name in ROLE_SEED:
        conn.execute(
            sa.text(
                """
                insert into roles (code, name)
                values (:code, :name)
                on conflict (code) do nothing
                """
            ),
            {"code": code, "name": name},
        )

    for name, slug, icon, description, sort_order in CATEGORY_SEED:
        conn.execute(
            sa.text(
                """
                insert into categories (name, slug, icon, description, sort_order, is_visible)
                values (:name, :slug, :icon, :description, :sort_order, true)
                on conflict (slug) do nothing
                """
            ),
            {
                "name": name,
                "slug": slug,
                "icon": icon,
                "description": description,
                "sort_order": sort_order,
            },
        )

    admin_id = conn.execute(
        sa.text(
            """
            insert into users (username, password_hash, display_name, email, status)
            values (:username, :password_hash, :display_name, :email, 'active')
            on conflict (username) do update
            set password_hash = excluded.password_hash,
                display_name = excluded.display_name,
                email = excluded.email
            returning id
            """
        ),
        {
            "username": "admin",
            "password_hash": password_hash,
            "display_name": "System Admin",
            "email": "admin@skillhub.local",
        },
    ).scalar_one()

    conn.execute(
        sa.text(
            """
            insert into user_roles (user_id, role_id)
            select :user_id, id
            from roles
            where code = 'admin'
            on conflict (user_id, role_id) do nothing
            """
        ),
        {"user_id": admin_id},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("delete from users where username = 'admin'"))
    categories = sa.table("categories", sa.column("slug", sa.Text()))
    roles = sa.table("roles", sa.column("code", sa.Text()))
    conn.execute(sa.delete(categories).where(categories.c.slug.in_([slug for _, slug, _, _, _ in CATEGORY_SEED])))
    conn.execute(sa.delete(roles).where(roles.c.code.in_([code for code, _ in ROLE_SEED])))
