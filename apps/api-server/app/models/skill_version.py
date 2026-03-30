"""技能版本：包与 README 资产、审核状态与发布信息。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SkillVersion(Base):
    """单次上传对应的不可变版本行；`review_status` 驱动审核流。"""

    __tablename__ = "skill_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    skill_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    manifest_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    usage_guide_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changelog: Mapped[str] = mapped_column(Text, nullable=False)
    install_notes: Mapped[str] = mapped_column(Text, nullable=False)
    breaking_changes: Mapped[str] = mapped_column(Text, nullable=False)
    readme_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    package_file_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("file_assets.id"), nullable=False)
    readme_file_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("file_assets.id"), nullable=True)
    review_status: Mapped[str] = mapped_column(Text, nullable=False)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
