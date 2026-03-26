from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
