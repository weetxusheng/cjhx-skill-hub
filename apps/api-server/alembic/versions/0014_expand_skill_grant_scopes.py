"""0014 expand skill grant scopes

Revision ID: 0014_expand_skill_grant_scopes
Revises: 0013_skill_grants_ops
Create Date: 2026-03-25 20:58:00
"""

from __future__ import annotations

from alembic import op


revision = "0014_expand_skill_grant_scopes"
down_revision = "0013_skill_grants_ops"
branch_labels = None
depends_on = None

NEW_SCOPES = ("owner", "maintainer", "reviewer", "publisher", "rollback", "viewer")
OLD_SCOPES = ("owner", "maintainer", "reviewer", "publisher", "viewer")


def upgrade() -> None:
    op.drop_constraint("ck_skill_role_grants_scope", "skill_role_grants", type_="check")
    op.drop_constraint("ck_skill_user_grants_scope", "skill_user_grants", type_="check")
    op.create_check_constraint("ck_skill_role_grants_scope", "skill_role_grants", f"permission_scope in {NEW_SCOPES}")
    op.create_check_constraint("ck_skill_user_grants_scope", "skill_user_grants", f"permission_scope in {NEW_SCOPES}")


def downgrade() -> None:
    op.drop_constraint("ck_skill_role_grants_scope", "skill_role_grants", type_="check")
    op.drop_constraint("ck_skill_user_grants_scope", "skill_user_grants", type_="check")
    op.create_check_constraint("ck_skill_role_grants_scope", "skill_role_grants", f"permission_scope in {OLD_SCOPES}")
    op.create_check_constraint("ck_skill_user_grants_scope", "skill_user_grants", f"permission_scope in {OLD_SCOPES}")
