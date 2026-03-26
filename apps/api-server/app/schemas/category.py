from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class CategoryItem(BaseModel):
    id: UUID
    name: str
    slug: str
    icon: str | None
    description: str | None
    sort_order: int
    is_visible: bool
    skill_count: int


class CategoryUpsertRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: str = Field(min_length=1, max_length=80)
    icon: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, ge=0, le=9999)
    is_visible: bool = True
