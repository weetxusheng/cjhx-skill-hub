from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SkillTag(Base):
    __tablename__ = "skill_tags"

    skill_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
