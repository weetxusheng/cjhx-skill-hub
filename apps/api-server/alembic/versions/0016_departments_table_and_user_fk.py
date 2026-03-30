"""0016 departments table and users.primary_department_id

Revision ID: 0016_departments_user_fk
Revises: 0015_users_primary_department
Create Date: 2026-03-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0016_departments_user_fk"
down_revision = "0015_users_primary_department"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_departments_name"),
    )
    op.add_column(
        "users",
        sa.Column("primary_department_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_primary_department",
        "users",
        "departments",
        ["primary_department_id"],
        ["id"],
        ondelete="SET NULL",
    )

    bind = op.get_bind()
    names = bind.execute(
        sa.text(
            "SELECT DISTINCT trim(primary_department) AS n FROM users "
            "WHERE primary_department IS NOT NULL AND trim(primary_department) <> ''"
        )
    ).fetchall()
    for (name,) in names:
        bind.execute(
            sa.text("INSERT INTO departments (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
            {"name": name},
        )
    bind.execute(
        sa.text(
            """
            UPDATE users u
            SET primary_department_id = d.id
            FROM departments d
            WHERE u.primary_department IS NOT NULL AND trim(u.primary_department) = d.name
            """
        )
    )
    op.drop_column("users", "primary_department")


def downgrade() -> None:
    op.add_column("users", sa.Column("primary_department", sa.Text(), nullable=True))
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE users u
            SET primary_department = d.name
            FROM departments d
            WHERE u.primary_department_id IS NOT NULL AND u.primary_department_id = d.id
            """
        )
    )
    op.drop_constraint("fk_users_primary_department", "users", type_="foreignkey")
    op.drop_column("users", "primary_department_id")
    op.drop_table("departments")
