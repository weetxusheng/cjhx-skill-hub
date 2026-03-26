from __future__ import annotations

"""0004 create file assets

Revision ID: 0004_create_file_assets
Revises: 0003_create_taxonomy_tables
Create Date: 2026-03-25 00:08:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_create_file_assets"
down_revision: str | None = "0003_create_taxonomy_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "file_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("bucket", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("file_kind", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_file_assets_created_by",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bucket", "object_key", name="uq_file_assets_object"),
        sa.UniqueConstraint("sha256", "file_kind", name="uq_file_assets_sha256_kind"),
        sa.CheckConstraint(
            "file_kind in ('package','readme','icon','screenshot','attachment')",
            name="ck_file_assets_kind",
        ),
    )


def downgrade() -> None:
    op.drop_table("file_assets")
