"""后台治理与审计相关的 Pydantic 模型：用户、角色、审核队列、授权与统计。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AdminScopeAssigneeItem(BaseModel):
    target_id: UUID
    target_type: Literal["user", "role"]
    target_name: str
    members: list[str] = []


class AdminReviewListItem(BaseModel):
    version_id: UUID
    skill_id: UUID
    skill_name: str
    skill_slug: str
    version: str
    category_name: str
    created_by_display_name: str
    created_at: datetime
    review_status: str
    latest_review_comment: str | None = None
    latest_action_at: datetime | None = None
    assigned_reviewers: list[str] = []
    assigned_reviewer_details: list[AdminScopeAssigneeItem] = []
    assigned_publishers: list[str] = []


class PendingReleaseItem(BaseModel):
    version_id: UUID
    skill_id: UUID
    skill_name: str
    skill_slug: str
    version: str
    category_name: str
    created_by_display_name: str
    approved_at: datetime | None
    latest_review_comment: str | None = None
    assigned_publishers: list[str] = []


class ReviewHistoryItem(BaseModel):
    version_id: UUID
    skill_id: UUID
    skill_name: str
    version: str
    category_name: str
    action: str
    comment: str
    operator_display_name: str
    created_at: datetime


class DepartmentBrief(BaseModel):
    """一级部门：底层以 id 关联，name 为展示用中文名。"""

    id: UUID
    name: str


class AdminUserListItem(BaseModel):
    id: UUID
    username: str
    display_name: str
    email: str | None
    primary_department: DepartmentBrief | None = None
    status: str
    roles: list[str]
    last_login_at: datetime | None
    created_at: datetime


class AdminUserOptionItem(BaseModel):
    id: UUID
    username: str
    display_name: str
    primary_department: DepartmentBrief | None = None
    status: str


class AdminUserSkillGrantItem(BaseModel):
    skill_id: UUID
    skill_name: str
    skill_slug: str
    category_name: str
    effective_scopes: list[str]
    direct_scopes: list[str] = []
    inherited_scopes: list[str] = []
    inherited_roles: list[str] = []


class PermissionItem(BaseModel):
    code: str
    name: str
    description: str | None
    group_key: str


class AdminRoleItem(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    is_system: bool
    is_active: bool
    permission_codes: list[str]
    created_at: datetime


class AdminRoleOptionItem(BaseModel):
    id: UUID
    code: str
    name: str
    is_active: bool


class AdminAuditLogItem(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    actor_display_name: str | None
    action: str
    target_type: str
    target_id: UUID | None
    request_id: str | None
    before_json: dict | None = None
    after_json: dict | None = None
    created_at: datetime


class UserRoleAssignmentRequest(BaseModel):
    roles: list[str] = Field(min_length=1)


class RoleUpsertRequest(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)


class RolePermissionsRequest(BaseModel):
    permission_codes: list[str] = Field(min_length=1)


class SkillGrantItem(BaseModel):
    id: UUID
    target_type: str
    target_id: UUID
    target_name: str
    target_primary_department: DepartmentBrief | None = None
    permission_scope: str
    created_at: datetime


class SkillGrantUpsertRequest(BaseModel):
    target_ids: list[UUID] = Field(min_length=1)
    permission_scope: str = Field(pattern="^(owner|maintainer|reviewer|publisher|rollback|viewer)$")


class SkillStatsSeriesPoint(BaseModel):
    day: str
    count: int


class SkillStatsOverview(BaseModel):
    skill_id: UUID
    like_count: int
    favorite_count: int
    download_count: int
    recent_downloads: list[SkillStatsSeriesPoint]
    recent_favorites: list[SkillStatsSeriesPoint]
    recent_likes: list[SkillStatsSeriesPoint]


class SkillFavoriteRecord(BaseModel):
    user_id: UUID
    username: str
    display_name: str
    created_at: datetime


class SkillDownloadRecord(BaseModel):
    id: UUID
    user_id: UUID | None
    username: str | None
    display_name: str | None
    version: str
    created_at: datetime
    ip: str | None
    user_agent: str | None
