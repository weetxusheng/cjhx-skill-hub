"""一级部门主数据：底层以 UUID 标识，名称用于界面展示。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Department(Base):
    """一级部门；`name` 为展示用中文名，可与 OA 主数据对齐。"""

    __tablename__ = "departments"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
