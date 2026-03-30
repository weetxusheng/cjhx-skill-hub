from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.config import get_settings
from app.core.security import hash_password
from app.main import app
from app.models.role import Role
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_user_grant import SkillUserGrant
from app.models.user import User
from app.models.user_role import UserRole
from tests.support.factories import create_skill_version_record


def _login(client: TestClient, username: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["data"]


def _create_user_with_role(db: Session, role_code: str, username: str) -> User:
    user = User(
        username=username,
        password_hash=hash_password("Pass123!"),
        display_name=username,
        email=f"{username}@skillhub.local",
        status="active",
    )
    db.add(user)
    db.flush()
    role_id = db.execute(select(Role.id).where(Role.code == role_code)).scalar_one()
    db.add(UserRole(user_id=user.id, role_id=role_id))
    db.commit()
    db.refresh(user)
    return user


def test_health_live_and_ready_endpoints(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    live_response = client.get("/health/live")
    assert live_response.status_code == 200
    assert live_response.json()["data"]["status"] == "ok"

    monkeypatch.setattr(
        "app.api.routes.health.readiness_status",
        lambda: (False, {"database": {"status": "error", "detail": "down"}}),
    )
    ready_response = client.get("/health/ready")
    assert ready_response.status_code == 503
    assert ready_response.json()["data"]["status"] == "degraded"


def test_admin_category_crud_and_audit_export(client: TestClient) -> None:
    admin = _login(client, "admin", "ChangeMe123!")
    headers = {"Authorization": f"Bearer {admin['access_token']}"}

    create_response = client.post(
        "/api/admin/categories",
        json={
            "name": "测试分类",
            "slug": "test-category",
            "icon": "ToolOutlined",
            "description": "for production test",
            "sort_order": 99,
            "is_visible": True,
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    category_id = create_response.json()["data"]["id"]

    patch_response = client.patch(
        f"/api/admin/categories/{category_id}",
        json={
            "name": "测试分类-已更新",
            "slug": "test-category",
            "icon": "ToolOutlined",
            "description": "updated",
            "sort_order": 101,
            "is_visible": False,
        },
        headers=headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["is_visible"] is False

    export_response = client.get("/api/admin/audit-logs/export", headers=headers)
    assert export_response.status_code == 200
    assert "category.update" in export_response.text

    delete_response = client.delete(f"/api/admin/categories/{category_id}", headers=headers)
    assert delete_response.status_code == 200


def test_admin_can_disable_user_and_old_tokens_stop_working(client: TestClient, db_session: Session) -> None:
    managed_user = _create_user_with_role(db_session, "viewer", "managed_user")
    managed_tokens = _login(client, managed_user.username, "Pass123!")
    admin = _login(client, "admin", "ChangeMe123!")
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    roles_response = client.post(
        f"/api/admin/users/{managed_user.id}/roles",
        json={"roles": ["viewer", "contributor"]},
        headers=admin_headers,
    )
    assert roles_response.status_code == 200
    assert sorted(roles_response.json()["data"]["roles"]) == ["contributor", "viewer"]

    disable_response = client.post(f"/api/admin/users/{managed_user.id}/disable", headers=admin_headers)
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["status"] == "disabled"

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {managed_tokens['access_token']}"})
    assert me_response.status_code == 401

    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": managed_tokens["refresh_token"]})
    assert refresh_response.status_code == 401


def test_custom_role_permissions_flow(client: TestClient, db_session: Session) -> None:
    admin = _login(client, "admin", "ChangeMe123!")
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    create_role_response = client.post(
        "/api/admin/roles",
        json={"code": "ops-curator", "name": "运营策展", "description": "只看技能，不管治理"},
        headers=admin_headers,
    )
    assert create_role_response.status_code == 200
    role_id = create_role_response.json()["data"]["id"]

    permissions_response = client.post(
        f"/api/admin/roles/{role_id}/permissions",
        json={"permission_codes": ["admin.dashboard.view", "skill.view"]},
        headers=admin_headers,
    )
    assert permissions_response.status_code == 200
    assert permissions_response.json()["data"]["permission_codes"] == ["admin.dashboard.view", "skill.view"]

    user = _create_user_with_role(db_session, "viewer", "custom_role_user")
    assign_roles_response = client.post(
        f"/api/admin/users/{user.id}/roles",
        json={"roles": ["ops-curator"]},
        headers=admin_headers,
    )
    assert assign_roles_response.status_code == 200

    custom_tokens = _login(client, user.username, "Pass123!")
    custom_headers = {"Authorization": f"Bearer {custom_tokens['access_token']}"}

    me_response = client.get("/api/auth/me", headers=custom_headers)
    assert me_response.status_code == 200
    assert me_response.json()["data"]["roles"] == ["ops-curator"]
    assert sorted(me_response.json()["data"]["permissions"]) == ["admin.dashboard.view", "skill.view"]

    list_skills_response = client.get("/api/admin/skills", headers=custom_headers)
    assert list_skills_response.status_code == 200

    categories_response = client.get("/api/admin/categories", headers=custom_headers)
    assert categories_response.status_code == 403


def test_admin_users_roles_and_audit_logs_support_pagination_and_options(client: TestClient, db_session: Session) -> None:
    _create_user_with_role(db_session, "viewer", "paged_user_one")
    _create_user_with_role(db_session, "viewer", "paged_user_two")
    admin = _login(client, "admin", "ChangeMe123!")
    headers = {"Authorization": f"Bearer {admin['access_token']}"}
    category_suffix = uuid4().hex[:8]
    category_slug = f"paged-category-{category_suffix}"

    category_response = client.post(
        "/api/admin/categories",
        json={
            "name": f"分页测试分类-{category_suffix}",
            "slug": category_slug,
            "icon": "ToolOutlined",
            "description": "for pagination test",
            "sort_order": 88,
            "is_visible": True,
        },
        headers=headers,
    )
    assert category_response.status_code == 200

    users_response = client.get("/api/admin/users?page=1&page_size=2", headers=headers)
    assert users_response.status_code == 200
    users_payload = users_response.json()["data"]
    assert users_payload["page"] == 1
    assert users_payload["page_size"] == 2
    assert users_payload["total"] >= 2
    assert len(users_payload["items"]) == 2

    user_options = client.get("/api/admin/users/options?status=active", headers=headers)
    assert user_options.status_code == 200
    assert any(item["username"] == "paged_user_one" for item in user_options.json()["data"])

    roles_response = client.get("/api/admin/roles?page=1&page_size=2", headers=headers)
    assert roles_response.status_code == 200
    roles_payload = roles_response.json()["data"]
    assert roles_payload["page"] == 1
    assert roles_payload["page_size"] == 2
    assert roles_payload["total"] >= 2
    assert len(roles_payload["items"]) == 2

    role_options = client.get("/api/admin/roles/options", headers=headers)
    assert role_options.status_code == 200
    assert any(item["code"] == "admin" for item in role_options.json()["data"])

    audit_response = client.get("/api/admin/audit-logs?page=1&page_size=1&target_type=category", headers=headers)
    assert audit_response.status_code == 200
    audit_payload = audit_response.json()["data"]
    assert audit_payload["page"] == 1
    assert audit_payload["page_size"] == 1
    assert audit_payload["total"] >= 1
    assert len(audit_payload["items"]) == 1
    assert audit_payload["items"][0]["target_type"] == "category"


def test_admin_can_view_user_skill_grants_from_user_management(client: TestClient, db_session: Session) -> None:
    admin = _login(client, "admin", "ChangeMe123!")
    headers = {"Authorization": f"Bearer {admin['access_token']}"}
    admin_user = db_session.execute(select(User).where(User.username == "admin")).scalar_one()

    managed_user = _create_user_with_role(db_session, "viewer", f"user_grants_{uuid4().hex[:6]}")
    inherited_role = Role(
        code=f"ops-reviewer-{uuid4().hex[:6]}",
        name="运营审核",
        description="for inherited skill grants",
        is_system=False,
        is_active=True,
    )
    db_session.add(inherited_role)
    db_session.flush()
    db_session.add(UserRole(user_id=managed_user.id, role_id=inherited_role.id))

    direct_skill, _ = create_skill_version_record(
        db_session,
        owner=admin_user,
        slug=f"user-direct-{uuid4().hex[:6]}",
        version="1.0.0",
        category_slug="developer-tools",
        name="User Direct Skill",
        summary="direct grant",
        description="direct grant",
        review_status="draft",
        create_default_grants=False,
    )
    inherited_skill, _ = create_skill_version_record(
        db_session,
        owner=admin_user,
        slug=f"user-inherited-{uuid4().hex[:6]}",
        version="1.0.0",
        category_slug="productivity",
        name="User Inherited Skill",
        summary="role grant",
        description="role grant",
        review_status="submitted",
        create_default_grants=False,
    )
    hybrid_skill, _ = create_skill_version_record(
        db_session,
        owner=admin_user,
        slug=f"user-hybrid-{uuid4().hex[:6]}",
        version="1.0.0",
        category_slug="content-creation",
        name="User Hybrid Skill",
        summary="hybrid grant",
        description="hybrid grant",
        review_status="approved",
        create_default_grants=False,
    )
    db_session.add_all(
        [
            SkillUserGrant(skill_id=direct_skill.id, user_id=managed_user.id, permission_scope="maintainer"),
            SkillUserGrant(skill_id=hybrid_skill.id, user_id=managed_user.id, permission_scope="viewer"),
            SkillRoleGrant(skill_id=inherited_skill.id, role_id=inherited_role.id, permission_scope="reviewer"),
            SkillRoleGrant(skill_id=hybrid_skill.id, role_id=inherited_role.id, permission_scope="publisher"),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/admin/users/{managed_user.id}/skill-grants", headers=headers)
    assert response.status_code == 200
    payload = response.json()["data"]

    by_skill = {item["skill_name"]: item for item in payload}
    assert by_skill["User Direct Skill"]["direct_scopes"] == ["maintainer"]
    assert by_skill["User Direct Skill"]["inherited_scopes"] == []
    assert by_skill["User Inherited Skill"]["direct_scopes"] == []
    assert by_skill["User Inherited Skill"]["inherited_scopes"] == ["reviewer"]
    assert by_skill["User Inherited Skill"]["inherited_roles"] == [inherited_role.name]
    assert by_skill["User Hybrid Skill"]["effective_scopes"] == ["publisher", "viewer"]
    assert by_skill["User Hybrid Skill"]["direct_scopes"] == ["viewer"]
    assert by_skill["User Hybrid Skill"]["inherited_scopes"] == ["publisher"]


def test_upload_failure_cleans_temporary_objects(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = get_settings()
    upload_pkg_dir = settings.storage_dir / settings.skill_package_upload_subdir
    readme_dir = settings.storage_dir / settings.skill_readme_subdir
    packages_before = {item.name for item in upload_pkg_dir.glob("*")} if upload_pkg_dir.exists() else set()
    readmes_before = {item.name for item in readme_dir.glob("*")} if readme_dir.exists() else set()
    admin = _login(client, "admin", "ChangeMe123!")

    def explode(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.services.skill_upload.write_audit_log", explode)
    from io import BytesIO
    from zipfile import ZipFile

    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "skill.yaml",
            "name: Rollback Skill\nslug: rollback-skill\nversion: 1.0.0\nsummary: demo\ndescription: demo\ncategory: developer-tools\ntags: []\nauthor: qa\n",
        )
        archive.writestr("README.md", "# rollback\n")
    files = {"file": ("rollback-skill.zip", buffer.getvalue(), "application/zip")}

    with TestClient(app, raise_server_exceptions=False) as non_raising_client:
        response = non_raising_client.post(
            "/api/admin/skills/upload",
            files=files,
            headers={"Authorization": f"Bearer {admin['access_token']}"},
        )
    assert response.status_code == 500

    packages_after = {item.name for item in upload_pkg_dir.glob("*")} if upload_pkg_dir.exists() else set()
    readmes_after = {item.name for item in readme_dir.glob("*")} if readme_dir.exists() else set()
    assert packages_after == packages_before
    assert readmes_after == readmes_before
