from __future__ import annotations

"""0011 add likes and usage guides

Revision ID: 0011_add_likes_and_usage_guides
Revises: 0010_add_audit_request_id
Create Date: 2026-03-25 14:30:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0011_add_likes_and_usage_guides"
down_revision: str | None = "0010_add_audit_request_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("skills", sa.Column("like_count", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column(
        "skill_versions",
        sa.Column(
            "usage_guide_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_table(
        "skill_likes",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "skill_id", name="pk_skill_likes"),
    )
    op.create_index("idx_skill_likes_skill_created", "skill_likes", ["skill_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_skill_likes_skill_created", table_name="skill_likes")
    op.drop_table("skill_likes")
    op.drop_column("skill_versions", "usage_guide_json")
    op.drop_column("skills", "like_count")
