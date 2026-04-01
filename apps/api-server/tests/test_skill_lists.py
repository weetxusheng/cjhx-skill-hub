from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from tests.support.factories import create_skill_version_record


def _login(client: TestClient, username: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["data"]


def _ensure_viewer_user(db: Session) -> User:
    viewer = db.execute(select(User).where(User.username == "viewer_smoke")).scalar_one_or_none()
    if viewer is None:
        viewer = User(
            username="viewer_smoke",
            password_hash=hash_password("ViewerPass123!"),
            display_name="Viewer Smoke",
            email="viewer-smoke@skillhub.local",
            status="active",
        )
        db.add(viewer)
        db.flush()

        viewer_role_id = db.execute(select(Role.id).where(Role.code == "viewer")).scalar_one()
        db.add(UserRole(user_id=viewer.id, role_id=viewer_role_id))
        db.commit()
        db.refresh(viewer)

    return viewer


def _admin_user(db: Session) -> User:
    return db.execute(select(User).where(User.username == "admin")).scalar_one()


def _create_user_with_permissions(db: Session, *, username: str, permission_codes: list[str]) -> User:
    role = Role(
        code=f"{username}-role",
        name=f"{username} role",
        description="test role",
        is_system=False,
        is_active=True,
    )
    db.add(role)
    db.flush()

    permission_ids = list(db.execute(select(Permission.id).where(Permission.code.in_(permission_codes))).scalars())
    db.add_all([RolePermission(role_id=role.id, permission_id=permission_id) for permission_id in permission_ids])

    user = User(
        username=username,
        password_hash=hash_password("Pass123!"),
        display_name=username,
        email=f"{username}@skillhub.local",
        status="active",
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user


def test_public_skills_only_returns_published_items(client: TestClient, db_session: Session) -> None:
    admin = _admin_user(db_session)
    create_skill_version_record(db_session, owner=admin, slug="workflow-copilot", version="1.4.0", category_slug="productivity", name="Workflow Copilot", summary="为内部流程提供模板化编排与执行建议。", description="流程编排助手。", review_status="published")
    create_skill_version_record(db_session, owner=admin, slug="sql-insight", version="2.1.0", category_slug="developer-tools", name="SQL Insight", summary="帮助分析查询性能。", description="SQL 分析技能。", review_status="published")
    create_skill_version_record(db_session, owner=admin, slug="policy-guard", version="1.0.2", category_slug="security-compliance", name="Policy Guard", summary="提供常见安全配置检查。", description="安全合规技能。", review_status="published")
    create_skill_version_record(db_session, owner=admin, slug="narrative-writer", version="3.0.1", category_slug="content-creation", name="Narrative Writer", summary="为内容团队生成结构与提纲。", description="内容写作辅助。", review_status="published")
    create_skill_version_record(db_session, owner=admin, slug="analytics-scout", version="0.8.0", category_slug="data-analysis", name="Analytics Scout", summary="辅助数据分析任务起步。", description="数据分析技能。", review_status="draft")

    response = client.get("/api/public/skills?page=1&page_size=3")
    assert response.status_code == 200

    payload = response.json()["data"]
    assert payload["total"] == 4
    assert payload["page"] == 1
    assert payload["page_size"] == 3
    assert len(payload["items"]) == 3
    assert all(item["published_at"] is not None for item in payload["items"])


def test_public_skills_support_filter_and_sort(client: TestClient, db_session: Session) -> None:
    admin = _admin_user(db_session)
    create_skill_version_record(
        db_session,
        owner=admin,
        slug="sql-insight",
        version="2.1.0",
        category_slug="developer-tools",
        name="SQL Insight",
        summary="帮助分析查询性能、补齐索引建议和执行计划注释。",
        description="面向数据与研发团队的 SQL 分析技能。",
        review_status="published",
        download_count=402,
    )
    create_skill_version_record(
        db_session,
        owner=admin,
        slug="policy-guard",
        version="1.0.2",
        category_slug="security-compliance",
        name="Policy Guard",
        summary="提供常见安全配置检查。",
        description="安全合规技能。",
        review_status="published",
        download_count=185,
    )

    response = client.get("/api/public/skills?category=developer-tools&q=sql&sort=downloads")
    assert response.status_code == 200

    payload = response.json()["data"]
    assert payload["total"] == 1
    assert payload["items"][0]["slug"] == "sql-insight"


def test_admin_skills_requires_authorized_role(client: TestClient, db_session: Session) -> None:
    _ensure_viewer_user(db_session)

    unauthorized_response = client.get("/api/admin/skills")
    assert unauthorized_response.status_code == 401

    viewer_tokens = _login(client, "viewer_smoke", "ViewerPass123!")
    forbidden_response = client.get(
        "/api/admin/skills",
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert forbidden_response.status_code == 403


def test_admin_skills_returns_paginated_filtered_rows(client: TestClient, db_session: Session) -> None:
    admin = _admin_user(db_session)
    create_skill_version_record(
        db_session,
        owner=admin,
        slug="narrative-writer",
        version="3.0.1",
        category_slug="content-creation",
        name="Narrative Writer",
        summary="为内容团队生成长短文结构、提纲和版本润色建议。",
        description="面向品牌和内容创作场景的写作辅助技能。",
        review_status="published",
    )
    admin_tokens = _login(client, "admin", "ChangeMe123!")

    response = client.get(
        "/api/admin/skills?category=content-creation&q=writer&page=1&page_size=5",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert response.status_code == 200

    payload = response.json()["data"]
    assert payload["total"] == 1
    assert payload["items"][0]["slug"] == "narrative-writer"
    assert payload["items"][0]["category_slug"] == "content-creation"


def test_public_upload_center_records_require_login(client: TestClient) -> None:
    response = client.get("/api/public/upload-center/records?page=1&page_size=20")
    assert response.status_code == 401


def test_system_role_contacts_require_login(client: TestClient) -> None:
    response = client.get("/api/public/system-role-contacts?role_code=admin")
    assert response.status_code == 401


def test_upload_center_records_only_show_current_users_uploads(client: TestClient, db_session: Session) -> None:
    scoped_user = _create_user_with_permissions(
        db_session,
        username="upload_operator",
        permission_codes=["skill.upload"],
    )
    other_uploader = _create_user_with_permissions(
        db_session,
        username="other_upload_operator",
        permission_codes=["skill.upload"],
    )

    visible_uploaded_skill, _ = create_skill_version_record(
        db_session,
        owner=scoped_user,
        slug="visible-uploaded-skill",
        version="1.1.0",
        category_slug="developer-tools",
        name="Visible Uploaded Skill",
        summary="visible uploaded",
        description="visible uploaded",
        review_status="submitted",
    )
    hidden_uploaded_skill, _ = create_skill_version_record(
        db_session,
        owner=other_uploader,
        slug="hidden-uploaded-skill",
        version="2.0.0",
        category_slug="productivity",
        name="Hidden Uploaded Skill",
        summary="hidden uploaded",
        description="hidden uploaded",
        review_status="approved",
    )
    db_session.commit()

    scoped_tokens = _login(client, scoped_user.username, "Pass123!")
    headers = {"Authorization": f"Bearer {scoped_tokens['access_token']}"}
    upload_center_response = client.get("/api/public/upload-center/records?page=1&page_size=20", headers=headers)
    assert upload_center_response.status_code == 200
    payload = upload_center_response.json()["data"]
    assert payload["total"] == 1
    assert payload["items"][0]["skill_slug"] == "visible-uploaded-skill"
    assert payload["items"][0]["version"] == "1.1.0"
    assert payload["items"][0]["review_status"] == "submitted"


def test_upload_center_forbidden_user_can_fetch_admin_contacts(client: TestClient, db_session: Session) -> None:
    viewer_user = _create_user_with_permissions(
        db_session,
        username="upload_forbidden_user",
        permission_codes=[],
    )
    viewer_tokens = _login(client, viewer_user.username, "Pass123!")
    headers = {"Authorization": f"Bearer {viewer_tokens['access_token']}"}

    contacts_response = client.get("/api/public/system-role-contacts?role_code=admin", headers=headers)
    assert contacts_response.status_code == 200

    admin_user = _admin_user(db_session)
    payload = contacts_response.json()["data"]
    assert payload["requested_roles"] == [{"code": "admin", "name": "管理员"}]
    assert payload["total"] == 1
    assert payload["items"][0]["display_name"] == admin_user.display_name
    assert payload["items"][0]["matched_roles"] == [{"code": "admin", "name": "管理员"}]
