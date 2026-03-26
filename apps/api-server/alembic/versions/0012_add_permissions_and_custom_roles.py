from __future__ import annotations

"""0012 add permissions and custom roles

Revision ID: 0012_custom_roles_perms
Revises: 0011_add_likes_and_usage_guides
Create Date: 2026-03-25 14:40:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0012_custom_roles_perms"
down_revision: str | None = "0011_add_likes_and_usage_guides"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


DEFAULT_ROLE_CONFIG = {
    "viewer": {"name": "浏览者", "description": "仅浏览前台技能广场"},
    "contributor": {"name": "贡献者", "description": "可上传、编辑并提交技能版本"},
    "reviewer": {"name": "审核员", "description": "可审核待审技能版本"},
    "publisher": {"name": "发布员", "description": "可发布、归档与回滚技能版本"},
    "admin": {"name": "管理员", "description": "拥有后台全部治理权限"},
}

PERMISSION_SEED = [
    ("skill.view", "查看技能", "skill", "查看后台技能列表、技能详情和版本详情"),
    ("skill.upload", "上传技能", "skill", "上传新技能包或追加新版本"),
    ("skill.edit", "编辑技能主档", "skill", "编辑技能主档展示信息"),
    ("skill.version.edit", "编辑版本文案", "skill", "编辑 draft/rejected 版本文案与使用指引"),
    ("skill.submit", "提交审核", "skill", "将 draft/rejected 版本提交审核"),
    ("skill.review", "审核技能", "skill", "查看待审队列并执行通过/拒绝"),
    ("skill.publish", "发布技能", "skill", "发布 approved 版本"),
    ("skill.archive", "归档技能", "skill", "归档当前 published 版本"),
    ("skill.rollback", "回滚技能", "skill", "回滚到历史 archived 版本"),
    ("admin.dashboard.view", "查看仪表盘", "admin", "访问后台 Dashboard"),
    ("admin.categories.view", "查看分类管理", "admin", "查看后台分类列表"),
    ("admin.categories.manage", "管理分类", "admin", "新建、编辑、删除分类"),
    ("admin.users.view", "查看用户管理", "admin", "查看后台用户列表"),
    ("admin.users.manage", "管理用户", "admin", "配置用户角色、启停用用户"),
    ("admin.roles.view", "查看角色管理", "admin", "查看角色和权限配置"),
    ("admin.roles.manage", "管理角色", "admin", "创建、编辑、启停用角色并配置权限"),
    ("admin.audit.view", "查看审计日志", "admin", "查看后台审计日志"),
    ("admin.audit.export", "导出审计日志", "admin", "导出后台审计日志"),
]

ROLE_PERMISSION_MAP = {
    "viewer": [],
    "contributor": [
        "admin.dashboard.view",
        "admin.categories.view",
        "skill.view",
        "skill.upload",
        "skill.edit",
        "skill.version.edit",
        "skill.submit",
    ],
    "reviewer": [
        "admin.dashboard.view",
        "admin.categories.view",
        "skill.view",
        "skill.review",
    ],
    "publisher": [
        "admin.dashboard.view",
        "admin.categories.view",
        "skill.view",
        "skill.publish",
        "skill.archive",
        "skill.rollback",
    ],
    "admin": [code for code, _, _, _ in PERMISSION_SEED],
}


def upgrade() -> None:
    conn = op.get_bind()

    op.drop_constraint("ck_roles_code", "roles", type_="check")
    op.add_column("roles", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("roles", sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("roles", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("group_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], name="fk_role_permissions_permission", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_role_permissions_role", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    for code, name, group_key, description in PERMISSION_SEED:
        conn.execute(
            sa.text(
                """
                insert into permissions (code, name, group_key, description)
                values (:code, :name, :group_key, :description)
                on conflict (code) do nothing
                """
            ),
            {"code": code, "name": name, "group_key": group_key, "description": description},
        )

    for code, config in DEFAULT_ROLE_CONFIG.items():
        conn.execute(
            sa.text(
                """
                update roles
                set name = :name,
                    description = :description,
                    is_system = true,
                    is_active = true
                where code = :code
                """
            ),
            {"code": code, "name": config["name"], "description": config["description"]},
        )

    for role_code, permission_codes in ROLE_PERMISSION_MAP.items():
        for permission_code in permission_codes:
            conn.execute(
                sa.text(
                    """
                    insert into role_permissions (role_id, permission_id)
                    select roles.id, permissions.id
                    from roles
                    join permissions on permissions.code = :permission_code
                    where roles.code = :role_code
                    on conflict (role_id, permission_id) do nothing
                    """
                ),
                {"role_code": role_code, "permission_code": permission_code},
            )


def downgrade() -> None:
    conn = op.get_bind()
    default_role_codes = tuple(DEFAULT_ROLE_CONFIG.keys())
    placeholders = ", ".join(f":code_{index}" for index, _ in enumerate(default_role_codes))
    bind = {f"code_{index}": code for index, code in enumerate(default_role_codes)}

    conn.execute(
        sa.text(
            f"""
            delete from user_roles
            where role_id in (
              select id from roles where code not in ({placeholders})
            )
            """
        ),
        bind,
    )
    conn.execute(
        sa.text(
            f"""
            delete from role_permissions
            where role_id in (
              select id from roles where code not in ({placeholders})
            )
            """
        ),
        bind,
    )
    conn.execute(
        sa.text(f"delete from roles where code not in ({placeholders})"),
        bind,
    )
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_column("roles", "is_active")
    op.drop_column("roles", "is_system")
    op.drop_column("roles", "description")
    op.create_check_constraint("ck_roles_code", "roles", "code in ('viewer','contributor','reviewer','publisher','admin')")
