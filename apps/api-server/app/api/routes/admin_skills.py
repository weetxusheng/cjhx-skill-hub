"""后台技能：列表、上传、详情与展示信息、统计、授权矩阵与运营明细。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permissions
from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.repositories.skills import AdminSkillListParams
from app.schemas.admin import SkillGrantUpsertRequest
from app.schemas.common import success_response
from app.schemas.skill import UpdateSkillRequest
from app.services.skill_upload import upload_skill_package
from app.services.skill_access import OWNER_SCOPES, EDIT_SCOPES, VIEW_SCOPES, ensure_skill_scopes
from app.services.skills import (
    assign_skill_role_grants,
    assign_skill_user_grants,
    delete_skill_role_grant,
    delete_skill_user_grant,
    get_admin_skill_detail,
    get_admin_skill_list,
    get_skill_download_records,
    get_skill_favorite_records,
    get_skill_permissions_payload,
    get_skill_stats,
    update_skill_display,
)
from app.models.user import User

router = APIRouter()
settings = get_settings()


@router.get("/skills")
def list_admin_skills(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.view")),
) -> dict:
    """分页列出后台可见技能，受全局权限与 skill 级作用域过滤。"""
    payload = get_admin_skill_list(
        db,
        AdminSkillListParams(category=category, q=q, status=status, page=page, page_size=page_size),
        current_user=current_user,
    )
    return success_response(payload.model_dump(mode="json"))


@router.post("/skills/upload")
async def upload_skill(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.upload")),
) -> dict:
    """上传 zip 包并创建/关联版本（默认直接进入待审核）；受 per-user+IP 上传限流。"""
    enforce_rate_limit(
        scope="admin-upload",
        actor_key=f"{current_user.id}:{request.client.host if request and request.client else 'unknown'}",
        rule_raw=settings.upload_rate_limit,
    )
    actor = db.get(User, current_user.id)
    assert actor is not None
    package_bytes = await file.read()
    payload = upload_skill_package(db, actor=actor, upload=file, package_bytes=package_bytes)
    return success_response(payload.model_dump(mode="json"))


@router.get("/skills/{skill_id}")
def get_skill_detail(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.view")),
) -> dict:
    """技能详情（后台视图，含版本与授权等），需 skill 级 view。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=VIEW_SCOPES)
    payload = get_admin_skill_detail(db, skill_id, current_user)
    return success_response(payload.model_dump(mode="json"))


@router.patch("/skills/{skill_id}")
def patch_skill(
    skill_id: UUID,
    body: UpdateSkillRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.edit")),
) -> dict:
    """更新名称、摘要、描述、分类等展示字段；需 skill 级 edit。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=EDIT_SCOPES)
    payload = update_skill_display(
        db,
        skill_id=skill_id,
        name=body.name,
        summary=body.summary,
        description=body.description,
        category_slug=body.category_slug,
    )
    return success_response(payload.model_dump(mode="json"))


@router.get("/skills/{skill_id}/stats")
def get_skill_stats_view(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.view")),
) -> dict:
    """技能运营统计（下载、收藏等聚合口径）。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=VIEW_SCOPES)
    payload = get_skill_stats(db, skill_id=skill_id)
    return success_response(payload.model_dump(mode="json"))


@router.get("/skills/{skill_id}/favorites")
def get_skill_favorites_view(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.users.view")),
) -> dict:
    """收藏用户明细列表；需用户治理权限与 skill 级 view。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=VIEW_SCOPES)
    payload = get_skill_favorite_records(db, skill_id=skill_id)
    return success_response([item.model_dump(mode="json") for item in payload])


@router.get("/skills/{skill_id}/downloads")
def get_skill_downloads_view(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.users.view")),
) -> dict:
    """下载记录明细（含脱敏/权限控制）；需用户治理权限与 skill 级 view。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=VIEW_SCOPES)
    payload = get_skill_download_records(db, skill_id=skill_id, current_user=current_user)
    return success_response([item.model_dump(mode="json") for item in payload])


@router.get("/skills/{skill_id}/permissions")
def get_skill_permissions_view(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.view")),
) -> dict:
    """当前用户可见的 skill 级授权矩阵（用户/角色授予）。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=VIEW_SCOPES)
    payload = get_skill_permissions_payload(db, skill_id=skill_id)
    return success_response([item.model_dump(mode="json") for item in payload])


@router.post("/skills/{skill_id}/role-grants")
def post_skill_role_grants(
    skill_id: UUID,
    body: SkillGrantUpsertRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.edit")),
) -> dict:
    """批量设置角色授权；需 skill 级 owner 范围。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=OWNER_SCOPES)
    payload = assign_skill_role_grants(
        db,
        skill_id=skill_id,
        role_ids=body.target_ids,
        permission_scope=body.permission_scope,
        actor_user_id=current_user.id,
    )
    return success_response([item.model_dump(mode="json") for item in payload])


@router.post("/skills/{skill_id}/user-grants")
def post_skill_user_grants(
    skill_id: UUID,
    body: SkillGrantUpsertRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.edit")),
) -> dict:
    """批量设置用户直接授权；需 skill 级 owner 范围。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=OWNER_SCOPES)
    payload = assign_skill_user_grants(
        db,
        skill_id=skill_id,
        user_ids=body.target_ids,
        permission_scope=body.permission_scope,
        actor_user_id=current_user.id,
    )
    return success_response([item.model_dump(mode="json") for item in payload])


@router.delete("/skills/{skill_id}/role-grants/{grant_id}")
def remove_skill_role_grant(
    skill_id: UUID,
    grant_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.edit")),
) -> dict:
    """删除指定角色授权记录。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=OWNER_SCOPES)
    delete_skill_role_grant(db, skill_id=skill_id, grant_id=grant_id, actor_user_id=current_user.id)
    return success_response({"deleted": True})


@router.delete("/skills/{skill_id}/user-grants/{grant_id}")
def remove_skill_user_grant(
    skill_id: UUID,
    grant_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.edit")),
) -> dict:
    """删除指定用户直接授权记录。"""
    ensure_skill_scopes(db, skill_id=skill_id, current_user=current_user, allowed_scopes=OWNER_SCOPES)
    delete_skill_user_grant(db, skill_id=skill_id, grant_id=grant_id, actor_user_id=current_user.id)
    return success_response({"deleted": True})
