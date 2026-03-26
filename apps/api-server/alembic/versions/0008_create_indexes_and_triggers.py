from __future__ import annotations

"""0008 create indexes and triggers

Revision ID: 0008_create_indexes_and_triggers
Revises: 0007_create_reviews_and_logs
Create Date: 2026-03-25 00:12:00
"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_create_indexes_and_triggers"
down_revision: str | None = "0007_create_reviews_and_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("idx_categories_visible_sort", "categories", ["is_visible", "sort_order"], unique=False)
    op.create_index("idx_skills_category_status", "skills", ["category_id", "status"], unique=False)
    op.create_index("idx_skills_published_at", "skills", ["published_at"], unique=False)
    op.create_index("idx_skills_download_count", "skills", ["download_count"], unique=False)
    op.create_index("idx_skills_favorite_count", "skills", ["favorite_count"], unique=False)
    op.create_index(
        "idx_skills_name_trgm",
        "skills",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_skills_summary_trgm",
        "skills",
        ["summary"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"summary": "gin_trgm_ops"},
    )
    op.create_index("idx_skill_versions_skill_status", "skill_versions", ["skill_id", "review_status"], unique=False)
    op.create_index("idx_skill_versions_published_at", "skill_versions", ["published_at"], unique=False)
    op.create_index(
        "idx_version_reviews_version_created",
        "version_reviews",
        ["skill_version_id", "created_at"],
        unique=False,
    )
    op.create_index("idx_download_logs_skill_created", "download_logs", ["skill_id", "created_at"], unique=False)
    op.create_index("idx_audit_logs_target", "audit_logs", ["target_type", "target_id", "created_at"], unique=False)
    op.execute(
        """
        create unique index uq_skill_versions_one_published
        on skill_versions(skill_id)
        where review_status = 'published';
        """
    )

    op.execute(
        """
        create or replace function set_updated_at()
        returns trigger as $$
        begin
          new.updated_at = now();
          return new;
        end;
        $$ language plpgsql;
        """
    )
    op.execute(
        """
        create trigger trg_users_updated_at
        before update on users
        for each row execute function set_updated_at();
        """
    )
    op.execute(
        """
        create trigger trg_categories_updated_at
        before update on categories
        for each row execute function set_updated_at();
        """
    )
    op.execute(
        """
        create trigger trg_skills_updated_at
        before update on skills
        for each row execute function set_updated_at();
        """
    )
    op.execute(
        """
        create trigger trg_skill_versions_updated_at
        before update on skill_versions
        for each row execute function set_updated_at();
        """
    )


def downgrade() -> None:
    op.execute("drop trigger if exists trg_skill_versions_updated_at on skill_versions;")
    op.execute("drop trigger if exists trg_skills_updated_at on skills;")
    op.execute("drop trigger if exists trg_categories_updated_at on categories;")
    op.execute("drop trigger if exists trg_users_updated_at on users;")
    op.execute("drop function if exists set_updated_at();")
    op.execute("drop index if exists uq_skill_versions_one_published;")
    op.drop_index("idx_audit_logs_target", table_name="audit_logs")
    op.drop_index("idx_download_logs_skill_created", table_name="download_logs")
    op.drop_index("idx_version_reviews_version_created", table_name="version_reviews")
    op.drop_index("idx_skill_versions_published_at", table_name="skill_versions")
    op.drop_index("idx_skill_versions_skill_status", table_name="skill_versions")
    op.drop_index("idx_skills_summary_trgm", table_name="skills")
    op.drop_index("idx_skills_name_trgm", table_name="skills")
    op.drop_index("idx_skills_favorite_count", table_name="skills")
    op.drop_index("idx_skills_download_count", table_name="skills")
    op.drop_index("idx_skills_published_at", table_name="skills")
    op.drop_index("idx_skills_category_status", table_name="skills")
    op.drop_index("idx_categories_visible_sort", table_name="categories")
