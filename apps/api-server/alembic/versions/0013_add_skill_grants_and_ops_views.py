"""0013 add skill grants and ops views

Revision ID: 0013_skill_grants_ops
Revises: 0012_custom_roles_perms
Create Date: 2026-03-25 18:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0013_skill_grants_ops"
down_revision = "0012_custom_roles_perms"
branch_labels = None
depends_on = None

SCOPES = ("owner", "maintainer", "reviewer", "publisher", "viewer")


def upgrade() -> None:
    op.create_table(
        "skill_role_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_scope", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name="fk_skill_role_grants_skill", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_skill_role_grants_role", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", "role_id", "permission_scope", name="uq_skill_role_grants_scope"),
        sa.CheckConstraint(f"permission_scope in {SCOPES}", name="ck_skill_role_grants_scope"),
    )
    op.create_table(
        "skill_user_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_scope", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name="fk_skill_user_grants_skill", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_skill_user_grants_user", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", "user_id", "permission_scope", name="uq_skill_user_grants_scope"),
        sa.CheckConstraint(f"permission_scope in {SCOPES}", name="ck_skill_user_grants_scope"),
    )
    op.create_index("idx_skill_role_grants_skill", "skill_role_grants", ["skill_id"])
    op.create_index("idx_skill_user_grants_skill", "skill_user_grants", ["skill_id"])


def downgrade() -> None:
    op.drop_index("idx_skill_user_grants_skill", table_name="skill_user_grants")
    op.drop_index("idx_skill_role_grants_skill", table_name="skill_role_grants")
    op.drop_table("skill_user_grants")
    op.drop_table("skill_role_grants")
