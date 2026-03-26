from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


SkillStatus = Literal["active", "inactive"]
SkillVersionStatus = Literal["draft", "submitted", "approved", "rejected", "published", "archived"]


class AdminSkillListItem(BaseModel):
    id: UUID
    name: str
    slug: str
    status: SkillStatus
    category_name: str
    category_slug: str
    latest_version_no: str | None
    current_published_version_id: UUID | None
    latest_version_status: SkillVersionStatus | None = None
    current_published_version: str | None = None
    owner_display_name: str | None = None
    pending_review_count: int = 0
    pending_release_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    download_count: int = 0
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PublicSkillListItem(BaseModel):
    id: UUID
    name: str
    slug: str
    summary: str
    category_name: str
    category_slug: str
    latest_version_no: str | None
    download_count: int
    favorite_count: int
    like_count: int
    published_at: datetime | None
    icon_file_id: UUID | None


class SkillVersionSummary(BaseModel):
    id: UUID
    version: str
    review_status: SkillVersionStatus
    created_at: datetime
    published_at: datetime | None


class ReviewRecordItem(BaseModel):
    id: UUID
    action: str
    comment: str
    operator_user_id: UUID
    operator_display_name: str
    created_at: datetime


class SkillDetailBase(BaseModel):
    id: UUID
    name: str
    slug: str
    summary: str
    description: str
    status: SkillStatus
    category_id: UUID
    category_name: str
    category_slug: str
    latest_version_no: str | None
    current_published_version_id: UUID | None
    download_count: int
    favorite_count: int
    like_count: int
    owner_user_id: UUID
    owner_display_name: str | None = None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UsageGuideAgent(BaseModel):
    standard_prompt: str
    accelerated_prompt: str


class UsageGuideHuman(BaseModel):
    standard_command: str
    accelerated_command: str
    post_install_command: str


class UsageGuide(BaseModel):
    agent: UsageGuideAgent
    human: UsageGuideHuman


class PublicSkillCurrentVersion(BaseModel):
    id: UUID
    version: str
    readme_markdown: str
    readme_html: str
    changelog: str
    install_notes: str
    breaking_changes: str
    published_at: datetime | None


class PublicSkillDetailResponse(BaseModel):
    skill: SkillDetailBase
    current_version: PublicSkillCurrentVersion
    published_versions: list[SkillVersionSummary]
    is_favorited: bool
    is_liked: bool
    usage_guide: UsageGuide


class AdminSkillCapabilities(BaseModel):
    edit_skill: bool
    upload_version: bool
    manage_grants: bool
    view_favorite_details: bool
    view_download_details: bool
    view_sensitive_download_details: bool


class AdminSkillDetailResponse(BaseModel):
    skill: SkillDetailBase
    versions: list[SkillVersionSummary]
    recent_reviews: list[ReviewRecordItem]
    latest_version_status: SkillVersionStatus | None = None
    current_published_version: str | None = None
    pending_review_count: int = 0
    pending_release_count: int = 0
    capabilities: AdminSkillCapabilities


class AdminVersionSkillSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    category_name: str
    category_slug: str
    current_published_version_id: UUID | None


class AdminVersionDetail(BaseModel):
    id: UUID
    skill_id: UUID
    version: str
    manifest_json: dict
    usage_guide_json: UsageGuide
    readme_markdown: str
    readme_html: str
    changelog: str
    install_notes: str
    breaking_changes: str
    source_type: str
    review_status: SkillVersionStatus
    review_comment: str | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    published_by: UUID | None
    published_at: datetime | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class AdminVersionCapabilities(BaseModel):
    edit_content: bool
    submit: bool
    approve: bool
    reject: bool
    publish: bool
    archive: bool
    rollback: bool


class AdminVersionDetailResponse(BaseModel):
    skill: AdminVersionSkillSummary
    version: AdminVersionDetail
    reviews: list[ReviewRecordItem]
    capabilities: AdminVersionCapabilities


class UploadSkillResponse(BaseModel):
    skill_id: UUID
    version_id: UUID
    created_skill: bool
    review_status: SkillVersionStatus
    parsed_manifest: dict


class UpdateSkillRequest(BaseModel):
    name: str
    summary: str
    description: str
    category_slug: str


class UpdateVersionRequest(BaseModel):
    changelog: str
    install_notes: str
    breaking_changes: str
    readme_markdown: str
    usage_guide_json: UsageGuide


class VersionActionRequest(BaseModel):
    comment: str = ""


class VersionActionResponse(BaseModel):
    version_id: UUID
    review_status: SkillVersionStatus
    message: str
    skill_current_published_version_id: UUID | None = None


class FavoriteResponse(BaseModel):
    favorited: bool
    favorite_count: int


class LikeResponse(BaseModel):
    liked: bool
    like_count: int


class DownloadResponse(BaseModel):
    downloaded: bool
    download_count: int
    filename: str
