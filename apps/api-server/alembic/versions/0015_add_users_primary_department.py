"""0015 add users primary_department

Revision ID: 0015_users_primary_department
Revises: 0014_expand_skill_grant_scopes
Create Date: 2026-03-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015_users_primary_department"
down_revision = "0014_expand_skill_grant_scopes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("primary_department", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "primary_department")
