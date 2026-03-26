"""0001 enable extensions

Revision ID: 0001_enable_extensions
Revises: 
Create Date: 2026-03-24 22:20:00
"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_enable_extensions"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('create extension if not exists "pgcrypto";')
    op.execute('create extension if not exists "pg_trgm";')


def downgrade() -> None:
    op.execute('drop extension if exists "pg_trgm";')
    op.execute('drop extension if exists "pgcrypto";')
