from __future__ import annotations

"""0006 create skill versions

Revision ID: 0006_create_skill_versions
Revises: 0005_create_skill_tables
Create Date: 2026-03-25 00:10:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006_create_skill_versions"
down_revision: str | None = "0005_create_skill_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "skill_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("install_notes", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("breaking_changes", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("readme_markdown", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False, server_default=sa.text("'upload_zip'")),
        sa.Column("package_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("readme_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_status", sa.Text(), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name="fk_skill_versions_skill", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["package_file_id"], ["file_assets.id"], name="fk_skill_versions_package"),
        sa.ForeignKeyConstraint(["readme_file_id"], ["file_assets.id"], name="fk_skill_versions_readme"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], name="fk_skill_versions_reviewed_by"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], name="fk_skill_versions_published_by"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_skill_versions_created_by"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", "version", name="uq_skill_versions_skill_version"),
        sa.CheckConstraint(
            "review_status in ('draft','submitted','approved','rejected','published','archived')",
            name="ck_skill_versions_status",
        ),
        sa.CheckConstraint("source_type = 'upload_zip'", name="ck_skill_versions_source"),
    )

    op.create_foreign_key(
        "fk_skills_current_published_version",
        "skills",
        "skill_versions",
        ["current_published_version_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_skills_current_published_version", "skills", type_="foreignkey")
    op.drop_table("skill_versions")
