from __future__ import annotations

"""0005 create skill tables

Revision ID: 0005_create_skill_tables
Revises: 0004_create_file_assets
Create Date: 2026-03-25 00:09:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_create_skill_tables"
down_revision: str | None = "0004_create_file_assets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("icon_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("current_published_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("latest_version_no", sa.Text(), nullable=True),
        sa.Column("view_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("download_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("favorite_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name="fk_skills_owner"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name="fk_skills_category"),
        sa.ForeignKeyConstraint(["icon_file_id"], ["file_assets.id"], name="fk_skills_icon"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_skills_slug"),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_skills_status"),
    )

    op.create_table(
        "skill_tags",
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name="fk_skill_tags_skill", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], name="fk_skill_tags_tag", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("skill_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("skill_tags")
    op.drop_table("skills")
