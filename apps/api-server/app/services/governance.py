from __future__ import annotations

from collections.abc import Iterable
from csv import DictWriter
from datetime import UTC, datetime
from io import StringIO
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.department import Department
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.skill import Skill
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_user_grant import SkillUserGrant
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.admin import (
    AdminAuditLogItem,
    AdminRoleItem,
    AdminRoleOptionItem,
    AdminUserListItem,
    AdminUserOptionItem,
    AdminUserSkillGrantItem,
    DepartmentBrief,
    PermissionItem,
)
from app.schemas.category import CategoryItem, CategoryUpsertRequest
from app.schemas.common import PagedResponse
from app.services.audit import write_audit_log
from app.services.auth import revoke_all_user_refresh_tokens
from app.services.cache import delete_cached_json

"""治理域服务：分类、角色、权限与后台用户管理。"""

PROTECTED_SYSTEM_ROLE_CODES = {"admin"}


def list_admin_categories(db: Session) -> list[CategoryItem]:
    """返回后台分类列表（含技能数量）。"""
    query = (
        select(
            Category.id,
            Category.name,
            Category.slug,
            Category.icon,
            Category.description,
            Category.sort_order,
            Category.is_visible,
            func.count(Skill.id).label("skill_count"),
        )
        .select_from(Category)
        .outerjoin(Skill, Skill.category_id == Category.id)
        .group_by(
            Category.id,
            Category.name,
            Category.slug,
            Category.icon,
            Category.description,
            Category.sort_order,
            Category.is_visible,
        )
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )
    return [CategoryItem.model_validate(row) for row in db.execute(query).mappings()]


def create_category(db: Session, *, payload: CategoryUpsertRequest, actor_user_id: UUID) -> CategoryItem:
    """创建分类，并写审计日志与清理前台分类缓存。"""
    exists = db.execute(select(Category).where(or_(Category.slug == payload.slug, Category.name == payload.name))).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="分类名称或 slug 已存在")
    category = Category(**payload.model_dump())
    db.add(category)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="category.create",
        target_type="category",
        target_id=category.id,
        after_json=payload.model_dump(),
    )
    db.commit()
    delete_cached_json("public:categories")
    return CategoryItem(
        id=category.id,
        name=category.name,
        slug=category.slug,
        icon=category.icon,
        description=category.description,
        sort_order=category.sort_order,
        is_visible=category.is_visible,
        skill_count=0,
    )


def update_category(
    db: Session,
    *,
    category_id: UUID,
    payload: CategoryUpsertRequest,
    actor_user_id: UUID,
) -> CategoryItem:
    """更新分类，记录 before/after 审计并清理缓存。"""
    category = db.execute(select(Category).where(Category.id == category_id)).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    conflict = db.execute(
        select(Category).where(
            Category.id != category_id,
            or_(Category.slug == payload.slug, Category.name == payload.name),
        )
    ).scalar_one_or_none()
    if conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="分类名称或 slug 已存在")
    before = {
        "name": category.name,
        "slug": category.slug,
        "icon": category.icon,
        "description": category.description,
        "sort_order": category.sort_order,
        "is_visible": category.is_visible,
    }
    for key, value in payload.model_dump().items():
        setattr(category, key, value)
    db.flush()
    skill_count = db.execute(select(func.count(Skill.id)).where(Skill.category_id == category.id)).scalar_one()
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="category.update",
        target_type="category",
        target_id=category.id,
        before_json=before,
        after_json=payload.model_dump(),
    )
    db.commit()
    delete_cached_json("public:categories")
    return CategoryItem(
        id=category.id,
        name=category.name,
        slug=category.slug,
        icon=category.icon,
        description=category.description,
        sort_order=category.sort_order,
        is_visible=category.is_visible,
        skill_count=skill_count,
    )


def delete_category(db: Session, *, category_id: UUID, actor_user_id: UUID) -> None:
    """删除分类（仅在无关联技能时允许），并记录审计与清理缓存。"""
    category = db.execute(select(Category).where(Category.id == category_id)).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    linked_count = db.execute(select(func.count(Skill.id)).where(Skill.category_id == category.id)).scalar_one()
    if linked_count > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="分类已被技能使用，无法删除")
    before = {
        "name": category.name,
        "slug": category.slug,
        "icon": category.icon,
        "description": category.description,
        "sort_order": category.sort_order,
        "is_visible": category.is_visible,
    }
    db.execute(delete(Category).where(Category.id == category_id))
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="category.delete",
        target_type="category",
        target_id=category_id,
        before_json=before,
    )
    db.commit()
    delete_cached_json("public:categories")


def _build_user_query(*, q: str | None = None, status_filter: str | None = None):
    """构造用户列表基础查询（支持关键字与状态筛选）。"""
    query = select(User).options(joinedload(User.department)).order_by(User.created_at.desc())
    if q:
        term = f"%{q.strip()}%"
        dept_match = exists().where(and_(Department.id == User.primary_department_id, Department.name.ilike(term)))
        query = query.where(
            or_(User.username.ilike(term), User.display_name.ilike(term), User.email.ilike(term), dept_match)
        )
    if status_filter:
        query = query.where(User.status == status_filter)
    return query


def _build_user_items(db: Session, users: list[User]) -> list[AdminUserListItem]:
    """将用户与其角色聚合为后台列表项。"""
    if not users:
        return []
    user_ids = [user.id for user in users]
    role_map: dict[UUID, list[str]] = {user_id: [] for user_id in user_ids}
    rows = db.execute(
        select(UserRole.user_id, Role.code)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id.in_(user_ids))
    ).all()
    for user_id, role_code in rows:
        role_map[user_id].append(role_code)
    return [
        AdminUserListItem(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            primary_department=DepartmentBrief(id=user.department.id, name=user.department.name)
            if user.department
            else None,
            status=user.status,
            roles=sorted(role_map.get(user.id, [])),
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
        for user in users
    ]


def list_admin_users(db: Session, *, q: str | None = None, status_filter: str | None = None) -> list[AdminUserListItem]:
    """返回后台用户列表（支持筛选）。"""
    users = list(db.execute(_build_user_query(q=q, status_filter=status_filter)).scalars())
    return _build_user_items(db, users)


def list_admin_users_paginated(
    db: Session,
    *,
    q: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PagedResponse[AdminUserListItem]:
    """返回后台用户分页列表。"""
    base_query = _build_user_query(q=q, status_filter=status_filter)
    total = db.execute(select(func.count()).select_from(base_query.order_by(None).subquery())).scalar_one()
    users = list(db.execute(base_query.offset((page - 1) * page_size).limit(page_size)).scalars())
    return PagedResponse[AdminUserListItem](
        items=_build_user_items(db, users),
        total=total,
        page=page,
        page_size=page_size,
    )


def list_admin_user_options(db: Session, *, q: str | None = None, status_filter: str | None = None) -> list[AdminUserOptionItem]:
    """返回轻量用户选项（下拉/自动补全）。"""
    users = list(db.execute(_build_user_query(q=q, status_filter=status_filter)).scalars())
    return [
        AdminUserOptionItem(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            primary_department=DepartmentBrief(id=user.department.id, name=user.department.name)
            if user.department
            else None,
            status=user.status,
        )
        for user in users
    ]


def list_user_skill_grants(db: Session, *, user_id: UUID) -> list[AdminUserSkillGrantItem]:
    """按技能维度返回用户有效授权（直授 + 继承）。"""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    aggregated: dict[UUID, dict[str, object]] = {}

    direct_rows = db.execute(
        select(
            Skill.id.label("skill_id"),
            Skill.name.label("skill_name"),
            Skill.slug.label("skill_slug"),
            Category.name.label("category_name"),
            SkillUserGrant.permission_scope.label("permission_scope"),
        )
        .join(Skill, Skill.id == SkillUserGrant.skill_id)
        .join(Category, Category.id == Skill.category_id)
        .where(SkillUserGrant.user_id == user_id)
        .order_by(Skill.name.asc(), SkillUserGrant.permission_scope.asc())
    ).mappings()
    for row in direct_rows:
        item = aggregated.setdefault(
            row["skill_id"],
            {
                "skill_id": row["skill_id"],
                "skill_name": row["skill_name"],
                "skill_slug": row["skill_slug"],
                "category_name": row["category_name"],
                "direct_scopes": set(),
                "inherited_scopes": set(),
                "inherited_roles": set(),
            },
        )
        item["direct_scopes"].add(row["permission_scope"])

    inherited_rows = db.execute(
        select(
            Skill.id.label("skill_id"),
            Skill.name.label("skill_name"),
            Skill.slug.label("skill_slug"),
            Category.name.label("category_name"),
            SkillRoleGrant.permission_scope.label("permission_scope"),
            Role.name.label("role_name"),
            Role.code.label("role_code"),
        )
        .join(Role, Role.id == SkillRoleGrant.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .join(Skill, Skill.id == SkillRoleGrant.skill_id)
        .join(Category, Category.id == Skill.category_id)
        .where(UserRole.user_id == user_id, Role.is_active.is_(True))
        .order_by(Skill.name.asc(), Role.name.asc(), SkillRoleGrant.permission_scope.asc())
    ).mappings()
    for row in inherited_rows:
        item = aggregated.setdefault(
            row["skill_id"],
            {
                "skill_id": row["skill_id"],
                "skill_name": row["skill_name"],
                "skill_slug": row["skill_slug"],
                "category_name": row["category_name"],
                "direct_scopes": set(),
                "inherited_scopes": set(),
                "inherited_roles": set(),
            },
        )
        item["inherited_scopes"].add(row["permission_scope"])
        item["inherited_roles"].add(row["role_name"])

    items: list[AdminUserSkillGrantItem] = []
    for item in aggregated.values():
        direct_scopes = sorted(item["direct_scopes"])
        inherited_scopes = sorted(item["inherited_scopes"])
        items.append(
            AdminUserSkillGrantItem(
                skill_id=item["skill_id"],
                skill_name=item["skill_name"],
                skill_slug=item["skill_slug"],
                category_name=item["category_name"],
                effective_scopes=sorted(set(direct_scopes).union(inherited_scopes)),
                direct_scopes=direct_scopes,
                inherited_scopes=inherited_scopes,
                inherited_roles=sorted(item["inherited_roles"]),
            )
        )
    return sorted(items, key=lambda item: (item.skill_name.lower(), item.skill_slug))


def assign_user_roles(db: Session, *, user_id: UUID, roles: Iterable[str], actor_user_id: UUID) -> AdminUserListItem:
    """替换用户角色分配，并记录审计。"""
    role_codes = sorted(set(roles))
    if not role_codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色列表非法")
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    available_roles = {
        role.code: role.id
        for role in db.execute(select(Role).where(Role.code.in_(role_codes), Role.is_active.is_(True))).scalars()
    }
    if set(available_roles.keys()) != set(role_codes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不存在")
    before_roles = [item.roles for item in list_admin_users(db) if item.id == user_id]
    db.execute(delete(UserRole).where(UserRole.user_id == user_id))
    db.add_all([UserRole(user_id=user_id, role_id=available_roles[code]) for code in role_codes])
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="user.roles.update",
        target_type="user",
        target_id=user_id,
        before_json={"roles": before_roles[0] if before_roles else []},
        after_json={"roles": role_codes},
    )
    db.commit()
    return next(item for item in list_admin_users(db) if item.id == user_id)


def list_permissions(db: Session) -> list[PermissionItem]:
    """按分组与编码排序返回权限点列表。"""
    rows = db.execute(select(Permission).order_by(Permission.group_key.asc(), Permission.code.asc())).scalars()
    return [PermissionItem(code=item.code, name=item.name, description=item.description, group_key=item.group_key) for item in rows]


def _build_role_query():
    """构造角色列表基础查询（系统角色优先）。"""
    return select(Role).order_by(Role.is_system.desc(), Role.created_at.asc())


def _build_role_items(db: Session, roles: list[Role]) -> list[AdminRoleItem]:
    """将角色与权限编码聚合为后台列表项。"""
    if not roles:
        return []
    role_ids = [role.id for role in roles]
    permission_rows = db.execute(
        select(RolePermission.role_id, Permission.code)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id.in_(role_ids))
    ).all()
    permission_map: dict[UUID, list[str]] = {role.id: [] for role in roles}
    for role_id, permission_code in permission_rows:
        permission_map[role_id].append(permission_code)
    return [
        AdminRoleItem(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            permission_codes=sorted(permission_map.get(role.id, [])),
            created_at=role.created_at,
        )
        for role in roles
    ]


def list_roles(db: Session) -> list[AdminRoleItem]:
    """返回治理页面角色列表。"""
    roles = list(db.execute(_build_role_query()).scalars())
    return _build_role_items(db, roles)


def list_roles_paginated(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    is_active: bool | None = None,
) -> PagedResponse[AdminRoleItem]:
    """返回治理页面角色分页列表；支持按 code/name/description 关键字与启用状态筛选。"""
    stmt = select(Role)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Role.code.ilike(term), Role.name.ilike(term), Role.description.ilike(term)),
        )
    if is_active is not None:
        stmt = stmt.where(Role.is_active.is_(is_active))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    ordered = stmt.order_by(Role.is_system.desc(), Role.created_at.asc())
    roles = list(db.execute(ordered.offset((page - 1) * page_size).limit(page_size)).scalars())
    return PagedResponse[AdminRoleItem](
        items=_build_role_items(db, roles),
        total=total,
        page=page,
        page_size=page_size,
    )


def list_role_options(db: Session) -> list[AdminRoleOptionItem]:
    """返回轻量角色选项（下拉/自动补全）。"""
    roles = list(db.execute(_build_role_query()).scalars())
    return [
        AdminRoleOptionItem(id=role.id, code=role.code, name=role.name, is_active=role.is_active)
        for role in roles
    ]


def create_role(db: Session, *, code: str, name: str, description: str | None, actor_user_id: UUID) -> AdminRoleItem:
    """创建非系统角色，并记录审计。"""
    normalized_code = code.strip()
    if not normalized_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色 code 不能为空")
    exists = db.execute(select(Role).where(Role.code == normalized_code)).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色 code 已存在")
    role = Role(code=normalized_code, name=name.strip(), description=description, is_system=False, is_active=True)
    db.add(role)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="role.create",
        target_type="role",
        target_id=role.id,
        after_json={"code": role.code, "name": role.name, "description": role.description, "is_active": role.is_active},
    )
    db.commit()
    return next(item for item in list_roles(db) if item.id == role.id)


def update_role(
    db: Session,
    *,
    role_id: UUID,
    code: str,
    name: str,
    description: str | None,
    actor_user_id: UUID,
) -> AdminRoleItem:
    """更新角色基础字段；系统角色不允许改 code。"""
    role = db.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    normalized_code = code.strip()
    if role.is_system and normalized_code != role.code:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="系统角色不允许修改 code")
    conflict = db.execute(select(Role).where(Role.id != role_id, Role.code == normalized_code)).scalar_one_or_none()
    if conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色 code 已存在")
    before = {"code": role.code, "name": role.name, "description": role.description}
    role.code = normalized_code
    role.name = name.strip()
    role.description = description
    db.flush()
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="role.update",
        target_type="role",
        target_id=role.id,
        before_json=before,
        after_json={"code": role.code, "name": role.name, "description": role.description},
    )
    db.commit()
    return next(item for item in list_roles(db) if item.id == role.id)


def set_role_permissions(db: Session, *, role_id: UUID, permission_codes: Iterable[str], actor_user_id: UUID) -> AdminRoleItem:
    """替换角色权限集合，并记录审计。"""
    codes = sorted(set(permission_codes))
    if not codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="权限列表不能为空")
    role = db.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    permissions = list(db.execute(select(Permission).where(Permission.code.in_(codes))).scalars())
    if len(permissions) != len(codes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="存在非法权限点")
    before = next(item.permission_codes for item in list_roles(db) if item.id == role_id)
    db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    db.add_all([RolePermission(role_id=role_id, permission_id=item.id) for item in permissions])
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="role.permissions.update",
        target_type="role",
        target_id=role_id,
        before_json={"permission_codes": before},
        after_json={"permission_codes": codes},
    )
    db.commit()
    return next(item for item in list_roles(db) if item.id == role_id)


def set_role_status(db: Session, *, role_id: UUID, enabled: bool, actor_user_id: UUID) -> AdminRoleItem:
    """启用/禁用角色；受保护的系统管理员角色不可禁用。"""
    role = db.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    if not enabled and role.is_system and role.code in PROTECTED_SYSTEM_ROLE_CODES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="系统管理员角色不允许禁用")
    before_status = role.is_active
    role.is_active = enabled
    db.flush()
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="role.enable" if enabled else "role.disable",
        target_type="role",
        target_id=role_id,
        before_json={"is_active": before_status},
        after_json={"is_active": role.is_active},
    )
    db.commit()
    return next(item for item in list_roles(db) if item.id == role_id)


def set_user_status(db: Session, *, user_id: UUID, enabled: bool, actor_user_id: UUID) -> AdminUserListItem:
    """启用/禁用用户；禁用时回收 refresh token 并记录审计。"""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    before_status = user.status
    user.status = "active" if enabled else "disabled"
    db.flush()
    if not enabled:
        revoke_all_user_refresh_tokens(db, user.id)
        db.flush()
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="user.enable" if enabled else "user.disable",
        target_type="user",
        target_id=user.id,
        before_json={"status": before_status},
        after_json={"status": user.status},
    )
    db.commit()
    return next(item for item in list_admin_users(db) if item.id == user_id)


def list_audit_logs(
    db: Session,
    *,
    actor_query: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int | None = None,
):
    """构造审计日志查询（用于列表与导出）。"""
    query = (
        select(
            AuditLog.id,
            AuditLog.actor_user_id,
            User.display_name.label("actor_display_name"),
            AuditLog.action,
            AuditLog.target_type,
            AuditLog.target_id,
            AuditLog.request_id,
            AuditLog.before_json,
            AuditLog.after_json,
            AuditLog.created_at,
        )
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .order_by(AuditLog.created_at.desc())
    )
    filters = []
    if actor_query:
        actor_term = f"%{actor_query.strip()}%"
        filters.append(or_(User.display_name.ilike(actor_term), User.username.ilike(actor_term)))
    if action:
        filters.append(AuditLog.action == action)
    if target_type:
        filters.append(AuditLog.target_type == target_type)
    if date_from:
        filters.append(AuditLog.created_at >= date_from.astimezone(UTC))
    if date_to:
        filters.append(AuditLog.created_at <= date_to.astimezone(UTC))
    if filters:
        query = query.where(and_(*filters))
    if limit is not None:
        query = query.limit(limit)
    return query


def list_audit_logs_paginated(
    db: Session,
    *,
    actor_query: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> PagedResponse[AdminAuditLogItem]:
    """返回治理页面审计日志分页列表。"""
    base_query = list_audit_logs(
        db,
        actor_query=actor_query,
        action=action,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
    )
    total = db.execute(select(func.count()).select_from(base_query.order_by(None).subquery())).scalar_one()
    rows = db.execute(base_query.offset((page - 1) * page_size).limit(page_size)).mappings()
    return PagedResponse[AdminAuditLogItem](
        items=[AdminAuditLogItem.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def list_audit_logs_for_export(
    db: Session,
    *,
    actor_query: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 500,
) -> list[AdminAuditLogItem]:
    """返回用于导出的审计日志（含默认上限，避免超大结果集）。"""
    query = list_audit_logs(
        db,
        actor_query=actor_query,
        action=action,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return [AdminAuditLogItem.model_validate(row) for row in db.execute(query).mappings()]


def export_audit_logs_csv(items: list[AdminAuditLogItem]) -> str:
    """将审计日志导出为 CSV（内存构建）。"""
    buffer = StringIO()
    writer = DictWriter(
        buffer,
        fieldnames=[
            "id",
            "actor_user_id",
            "actor_display_name",
            "action",
            "target_type",
            "target_id",
            "request_id",
            "created_at",
        ],
    )
    writer.writeheader()
    for item in items:
        writer.writerow(
            {
                "id": item.id,
                "actor_user_id": item.actor_user_id,
                "actor_display_name": item.actor_display_name,
                "action": item.action,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "request_id": item.request_id,
                "created_at": item.created_at.isoformat(),
            }
        )
    return buffer.getvalue()
