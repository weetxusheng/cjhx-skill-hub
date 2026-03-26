from __future__ import annotations

"""0010 add audit request id

Revision ID: 0010_add_audit_request_id
Revises: 0009_seed_initial_data
Create Date: 2026-03-25 12:00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0010_add_audit_request_id"
down_revision: str | None = "0009_seed_initial_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("request_id", sa.Text(), nullable=True))
    op.create_index("idx_audit_logs_request_id", "audit_logs", ["request_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_audit_logs_request_id", table_name="audit_logs")
    op.drop_column("audit_logs", "request_id")
