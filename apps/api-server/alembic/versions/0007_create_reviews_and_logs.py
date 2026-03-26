from __future__ import annotations

"""0007 create reviews and logs

Revision ID: 0007_create_reviews_and_logs
Revises: 0006_create_skill_versions
Create Date: 2026-03-25 00:11:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007_create_reviews_and_logs"
down_revision: str | None = "0006_create_skill_versions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "version_reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("skill_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("operator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["skill_version_id"],
            ["skill_versions.id"],
            name="fk_version_reviews_version",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["operator_user_id"], ["users.id"], name="fk_version_reviews_operator"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "action in ('submit','approve','reject','publish','archive','rollback_publish')",
            name="ck_version_reviews_action",
        ),
    )

    op.create_table(
        "favorites",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_favorites_user", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name="fk_favorites_skill", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "skill_id"),
    )

    op.create_table(
        "download_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name="fk_download_logs_skill"),
        sa.ForeignKeyConstraint(["skill_version_id"], ["skill_versions.id"], name="fk_download_logs_version"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_download_logs_user"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_audit_logs_actor"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("download_logs")
    op.drop_table("favorites")
    op.drop_table("version_reviews")
