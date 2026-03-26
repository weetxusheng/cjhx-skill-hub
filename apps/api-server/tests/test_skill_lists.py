from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.skill import Skill
from app.models.skill_user_grant import SkillUserGrant
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


def test_skill_lists_and_workbenches_respect_skill_grants(client: TestClient, db_session: Session) -> None:
    admin = _admin_user(db_session)
    scoped_user = _create_user_with_permissions(
        db_session,
        username="scoped_operator",
        permission_codes=["skill.view", "skill.review", "skill.publish"],
    )

    visible_published_skill, _ = create_skill_version_record(
        db_session,
        owner=admin,
        slug="visible-published-skill",
        version="1.0.0",
        category_slug="developer-tools",
        name="Visible Published Skill",
        summary="visible published",
        description="visible published",
        review_status="published",
        create_default_grants=False,
    )
    hidden_published_skill, _ = create_skill_version_record(
        db_session,
        owner=admin,
        slug="hidden-published-skill",
        version="1.0.0",
        category_slug="developer-tools",
        name="Hidden Published Skill",
        summary="hidden published",
        description="hidden published",
        review_status="published",
        create_default_grants=False,
    )
    visible_submitted_skill, _ = create_skill_version_record(
        db_session,
        owner=admin,
        slug="visible-submitted-skill",
        version="1.1.0",
        category_slug="productivity",
        name="Visible Submitted Skill",
        summary="visible submitted",
        description="visible submitted",
        review_status="submitted",
        create_default_grants=False,
    )
    hidden_submitted_skill, _ = create_skill_version_record(
        db_session,
        owner=admin,
        slug="hidden-submitted-skill",
        version="1.1.0",
        category_slug="productivity",
        name="Hidden Submitted Skill",
        summary="hidden submitted",
        description="hidden submitted",
        review_status="submitted",
        create_default_grants=False,
    )
    visible_approved_skill, _ = create_skill_version_record(
        db_session,
        owner=admin,
        slug="visible-approved-skill",
        version="2.0.0",
        category_slug="security-compliance",
        name="Visible Approved Skill",
        summary="visible approved",
        description="visible approved",
        review_status="approved",
        create_default_grants=False,
    )
    hidden_approved_skill, _ = create_skill_version_record(
        db_session,
        owner=admin,
        slug="hidden-approved-skill",
        version="2.0.0",
        category_slug="security-compliance",
        name="Hidden Approved Skill",
        summary="hidden approved",
        description="hidden approved",
        review_status="approved",
        create_default_grants=False,
    )

    db_session.add_all(
        [
            SkillUserGrant(skill_id=visible_published_skill.id, user_id=admin.id, permission_scope="owner"),
            SkillUserGrant(skill_id=hidden_published_skill.id, user_id=admin.id, permission_scope="owner"),
            SkillUserGrant(skill_id=visible_submitted_skill.id, user_id=admin.id, permission_scope="owner"),
            SkillUserGrant(skill_id=hidden_submitted_skill.id, user_id=admin.id, permission_scope="owner"),
            SkillUserGrant(skill_id=visible_approved_skill.id, user_id=admin.id, permission_scope="owner"),
            SkillUserGrant(skill_id=hidden_approved_skill.id, user_id=admin.id, permission_scope="owner"),
            SkillUserGrant(skill_id=visible_published_skill.id, user_id=scoped_user.id, permission_scope="viewer"),
            SkillUserGrant(skill_id=visible_submitted_skill.id, user_id=scoped_user.id, permission_scope="reviewer"),
            SkillUserGrant(skill_id=visible_approved_skill.id, user_id=scoped_user.id, permission_scope="publisher"),
        ]
    )
    db_session.commit()

    scoped_tokens = _login(client, scoped_user.username, "Pass123!")
    headers = {"Authorization": f"Bearer {scoped_tokens['access_token']}"}

    skills_response = client.get("/api/admin/skills?page=1&page_size=20", headers=headers)
    assert skills_response.status_code == 200
    skill_slugs = {item["slug"] for item in skills_response.json()["data"]["items"]}
    assert "visible-published-skill" in skill_slugs
    assert "visible-submitted-skill" in skill_slugs
    assert "visible-approved-skill" in skill_slugs
    assert "hidden-published-skill" not in skill_slugs
    assert "hidden-submitted-skill" not in skill_slugs
    assert "hidden-approved-skill" not in skill_slugs

    reviews_response = client.get("/api/admin/reviews/pending", headers=headers)
    assert reviews_response.status_code == 200
    review_slugs = {item["skill_slug"] for item in reviews_response.json()["data"]}
    assert review_slugs == {"visible-submitted-skill"}

    releases_response = client.get("/api/admin/releases/pending", headers=headers)
    assert releases_response.status_code == 200
    release_slugs = {item["skill_slug"] for item in releases_response.json()["data"]}
    assert release_slugs == {"visible-approved-skill"}

    history_response = client.get("/api/admin/reviews/history", headers=headers)
    assert history_response.status_code == 200
    history_skills = {item["skill_name"] for item in history_response.json()["data"]}
    assert "Visible Published Skill" in history_skills
    assert "Hidden Published Skill" not in history_skills
