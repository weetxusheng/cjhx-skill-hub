from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.download_log import DownloadLog
from app.models.favorite import Favorite
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.skill import Skill
from app.models.skill_like import SkillLike
from app.models.skill_user_grant import SkillUserGrant
from app.models.skill_version import SkillVersion
from app.models.user import User
from app.models.user_role import UserRole
from tests.support.factories import create_skill_version_record


def _login(client: TestClient, username: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["data"]


def _make_zip(
    *,
    slug: str,
    version: str,
    include_readme: bool = True,
    name: str = "Test Skill",
    summary: str = "test summary",
    description: str = "test description",
    category: str = "developer-tools",
) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "skill.yaml",
            (
                f"name: {name}\n"
                f"slug: {slug}\n"
                f"version: {version}\n"
                f"summary: {summary}\n"
                f"description: {description}\n"
                f"category: {category}\n"
                "tags: []\n"
                "author: test author\n"
            ),
        )
        if include_readme:
            archive.writestr("README.md", f"# {name}\n\nbody\n")
    return buffer.getvalue()


def _admin_user(db: Session) -> User:
    return db.execute(select(User).where(User.username == "admin")).scalar_one()


def _create_published_workflow_skill(db: Session) -> tuple[Skill, SkillVersion]:
    return create_skill_version_record(
        db,
        owner=_admin_user(db),
        slug="workflow-copilot",
        version="1.4.0",
        category_slug="productivity",
        name="Workflow Copilot",
        summary="为内部流程提供模板化编排与执行建议。",
        description="面向运营与产品团队的流程编排助手。",
        review_status="published",
        download_count=268,
        favorite_count=91,
        like_count=47,
    )


def _create_user_with_role(db: Session, role_code: str, username: str) -> User:
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None:
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


def test_upload_rejects_missing_readme(client: TestClient) -> None:
    admin = _login(client, "admin", "ChangeMe123!")
    files = {"file": ("invalid.zip", _make_zip(slug="invalid-readme", version="1.0.0", include_readme=False), "application/zip")}

    response = client.post("/api/admin/skills/upload", files=files, headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert response.status_code == 400
    assert "README.md" in response.json()["detail"]


def test_upload_rejects_duplicate_version(client: TestClient, db_session: Session) -> None:
    _create_published_workflow_skill(db_session)
    admin = _login(client, "admin", "ChangeMe123!")
    files = {"file": ("workflow.zip", _make_zip(slug="workflow-copilot", version="1.4.0"), "application/zip")}

    response = client.post("/api/admin/skills/upload", files=files, headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert response.status_code == 409


def test_admin_can_download_uploaded_version_package(client: TestClient, db_session: Session) -> None:
    _create_published_workflow_skill(db_session)
    admin = _login(client, "admin", "ChangeMe123!")
    files = {"file": ("pkg-dl.zip", _make_zip(slug="workflow-copilot", version="9.9.9"), "application/zip")}
    upload_response = client.post("/api/admin/skills/upload", files=files, headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert upload_response.status_code == 200
    version_id = upload_response.json()["data"]["version_id"]
    dl = client.get(f"/api/admin/versions/{version_id}/package", headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert dl.status_code == 200
    assert dl.content[:2] == b"PK"


def test_full_upload_submit_approve_publish_flow(client: TestClient, db_session: Session) -> None:
    contributor = _create_user_with_role(db_session, "contributor", "flow_contributor")
    reviewer = _create_user_with_role(db_session, "reviewer", "flow_reviewer")
    publisher = _create_user_with_role(db_session, "publisher", "flow_publisher")

    contributor_tokens = _login(client, contributor.username, "Pass123!")
    reviewer_tokens = _login(client, reviewer.username, "Pass123!")
    publisher_tokens = _login(client, publisher.username, "Pass123!")

    files = {"file": ("new-skill.zip", _make_zip(slug="ops-flow-skill", version="1.0.0"), "application/zip")}
    upload_response = client.post(
        "/api/admin/skills/upload",
        files=files,
        headers={"Authorization": f"Bearer {contributor_tokens['access_token']}"},
    )
    assert upload_response.status_code == 200
    version_id = upload_response.json()["data"]["version_id"]
    assert upload_response.json()["data"]["review_status"] == "submitted"

    approve_response = client.post(
        f"/api/admin/versions/{version_id}/approve",
        json={"comment": "approved"},
        headers={"Authorization": f"Bearer {reviewer_tokens['access_token']}"},
    )
    assert approve_response.status_code == 200

    publish_response = client.post(
        f"/api/admin/versions/{version_id}/publish",
        json={"comment": "ship it"},
        headers={"Authorization": f"Bearer {publisher_tokens['access_token']}"},
    )
    assert publish_response.status_code == 200

    public_detail = client.get("/api/public/skills/ops-flow-skill")
    assert public_detail.status_code == 200
    assert public_detail.json()["data"]["current_version"]["version"] == "1.0.0"


def test_permission_boundaries_for_review_and_publish(client: TestClient, db_session: Session) -> None:
    contributor = _create_user_with_role(db_session, "contributor", "perm_contributor")
    reviewer = _create_user_with_role(db_session, "reviewer", "perm_reviewer")
    publisher = _create_user_with_role(db_session, "publisher", "perm_publisher")

    contributor_tokens = _login(client, contributor.username, "Pass123!")
    reviewer_tokens = _login(client, reviewer.username, "Pass123!")
    publisher_tokens = _login(client, publisher.username, "Pass123!")

    files = {"file": ("perm-skill.zip", _make_zip(slug="perm-skill", version="1.0.0"), "application/zip")}
    upload_response = client.post(
        "/api/admin/skills/upload",
        files=files,
        headers={"Authorization": f"Bearer {contributor_tokens['access_token']}"},
    )
    version_id = upload_response.json()["data"]["version_id"]

    contributor_approve = client.post(
        f"/api/admin/versions/{version_id}/approve",
        json={"comment": "nope"},
        headers={"Authorization": f"Bearer {contributor_tokens['access_token']}"},
    )
    assert contributor_approve.status_code == 403

    reviewer_publish = client.post(
        f"/api/admin/versions/{version_id}/publish",
        json={"comment": "nope"},
        headers={"Authorization": f"Bearer {reviewer_tokens['access_token']}"},
    )
    assert reviewer_publish.status_code == 403

    publisher_approve = client.post(
        f"/api/admin/versions/{version_id}/approve",
        json={"comment": "nope"},
        headers={"Authorization": f"Bearer {publisher_tokens['access_token']}"},
    )
    assert publisher_approve.status_code == 403


def test_reject_requires_comment(client: TestClient, db_session: Session) -> None:
    contributor = _create_user_with_role(db_session, "contributor", "reject_contributor")
    reviewer = _create_user_with_role(db_session, "reviewer", "reject_reviewer")
    contributor_tokens = _login(client, contributor.username, "Pass123!")
    reviewer_tokens = _login(client, reviewer.username, "Pass123!")

    files = {"file": ("reject-skill.zip", _make_zip(slug="reject-skill", version="1.0.0"), "application/zip")}
    upload_response = client.post(
        "/api/admin/skills/upload",
        files=files,
        headers={"Authorization": f"Bearer {contributor_tokens['access_token']}"},
    )
    version_id = upload_response.json()["data"]["version_id"]

    reject_response = client.post(
        f"/api/admin/versions/{version_id}/reject",
        json={"comment": ""},
        headers={"Authorization": f"Bearer {reviewer_tokens['access_token']}"},
    )
    assert reject_response.status_code == 400


def test_skill_and_version_detail_capabilities_follow_scope_and_status(client: TestClient, db_session: Session) -> None:
    owner_user = _create_user_with_permissions(
        db_session,
        username="skill_owner_user",
        permission_codes=["skill.view", "skill.edit", "skill.upload", "skill.version.edit", "skill.submit", "admin.users.view"],
    )
    reviewer_user = _create_user_with_permissions(
        db_session,
        username="skill_reviewer_user",
        permission_codes=["skill.view", "skill.review"],
    )
    publisher_user = _create_user_with_permissions(
        db_session,
        username="skill_publisher_user",
        permission_codes=["skill.view", "skill.publish", "skill.archive", "skill.rollback"],
    )

    draft_skill, draft_version = create_skill_version_record(
        db_session,
        owner=owner_user,
        slug="detail-capabilities-draft",
        version="0.1.0",
        category_slug="developer-tools",
        name="Detail Capabilities Draft",
        summary="draft capabilities",
        description="draft capabilities",
        review_status="draft",
        create_default_grants=True,
    )
    _, submitted_version = create_skill_version_record(
        db_session,
        owner=owner_user,
        slug="detail-capabilities-review",
        version="0.2.0",
        category_slug="developer-tools",
        name="Detail Capabilities Review",
        summary="review capabilities",
        description="review capabilities",
        review_status="submitted",
        create_default_grants=False,
    )
    approved_skill, approved_version = create_skill_version_record(
        db_session,
        owner=owner_user,
        slug="detail-capabilities-release",
        version="0.3.0",
        category_slug="developer-tools",
        name="Detail Capabilities Release",
        summary="release capabilities",
        description="release capabilities",
        review_status="approved",
        create_default_grants=False,
    )
    archived_skill, archived_version = create_skill_version_record(
        db_session,
        owner=owner_user,
        slug="detail-capabilities-rollback",
        version="0.4.0",
        category_slug="developer-tools",
        name="Detail Capabilities Rollback",
        summary="rollback capabilities",
        description="rollback capabilities",
        review_status="archived",
        create_default_grants=False,
    )

    db_session.add_all(
        [
            SkillUserGrant(skill_id=approved_skill.id, user_id=owner_user.id, permission_scope="owner"),
            SkillUserGrant(skill_id=archived_skill.id, user_id=owner_user.id, permission_scope="owner"),
            SkillUserGrant(skill_id=submitted_version.skill_id, user_id=owner_user.id, permission_scope="owner"),
            SkillUserGrant(skill_id=submitted_version.skill_id, user_id=reviewer_user.id, permission_scope="reviewer"),
            SkillUserGrant(skill_id=approved_skill.id, user_id=publisher_user.id, permission_scope="publisher"),
            SkillUserGrant(skill_id=archived_skill.id, user_id=publisher_user.id, permission_scope="rollback"),
            SkillUserGrant(skill_id=archived_skill.id, user_id=publisher_user.id, permission_scope="viewer"),
            DownloadLog(
                skill_id=draft_skill.id,
                skill_version_id=draft_version.id,
                user_id=None,
                ip="10.0.0.1",
                user_agent="anonymous-agent",
            ),
            DownloadLog(
                skill_id=draft_skill.id,
                skill_version_id=draft_version.id,
                user_id=reviewer_user.id,
                ip="10.0.0.2",
                user_agent="named-agent",
            ),
        ]
    )
    db_session.commit()

    owner_tokens = _login(client, owner_user.username, "Pass123!")
    reviewer_tokens = _login(client, reviewer_user.username, "Pass123!")
    publisher_tokens = _login(client, publisher_user.username, "Pass123!")
    admin_tokens = _login(client, "admin", "ChangeMe123!")

    owner_skill_detail = client.get(
        f"/api/admin/skills/{draft_skill.id}",
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
    )
    assert owner_skill_detail.status_code == 200
    assert owner_skill_detail.json()["data"]["capabilities"] == {
        "edit_skill": True,
        "upload_version": True,
        "manage_grants": True,
        "view_favorite_details": True,
        "view_download_details": True,
        "view_sensitive_download_details": False,
    }

    owner_version_detail = client.get(
        f"/api/admin/versions/{draft_version.id}",
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
    )
    assert owner_version_detail.status_code == 200
    assert owner_version_detail.json()["data"]["capabilities"]["edit_content"] is True
    assert owner_version_detail.json()["data"]["capabilities"]["submit"] is True
    assert owner_version_detail.json()["data"]["capabilities"]["approve"] is False

    reviewer_version_detail = client.get(
        f"/api/admin/versions/{submitted_version.id}",
        headers={"Authorization": f"Bearer {reviewer_tokens['access_token']}"},
    )
    assert reviewer_version_detail.status_code == 200
    assert reviewer_version_detail.json()["data"]["capabilities"]["edit_content"] is True
    assert reviewer_version_detail.json()["data"]["capabilities"]["approve"] is True
    assert reviewer_version_detail.json()["data"]["capabilities"]["reject"] is True

    reviewer_patch = client.patch(
        f"/api/admin/versions/{submitted_version.id}",
        json={
            "changelog": "审核中修订",
            "install_notes": "",
            "breaking_changes": "",
            "readme_markdown": "# Detail Capabilities Review\n\npatched by reviewer\n",
            "usage_guide_json": {
                "agent": {"standard_prompt": "rp", "accelerated_prompt": "ra"},
                "human": {"standard_command": "rs", "accelerated_command": "rt", "post_install_command": "ru"},
            },
        },
        headers={"Authorization": f"Bearer {reviewer_tokens['access_token']}"},
    )
    assert reviewer_patch.status_code == 200

    publisher_version_detail = client.get(
        f"/api/admin/versions/{approved_version.id}",
        headers={"Authorization": f"Bearer {publisher_tokens['access_token']}"},
    )
    assert publisher_version_detail.status_code == 200
    assert publisher_version_detail.json()["data"]["capabilities"]["edit_content"] is True
    assert publisher_version_detail.json()["data"]["capabilities"]["publish"] is True

    publisher_patch = client.patch(
        f"/api/admin/versions/{approved_version.id}",
        json={
            "changelog": "发布前修订",
            "install_notes": "",
            "breaking_changes": "",
            "readme_markdown": "# Detail Capabilities Release\n\npatched by publisher\n",
            "usage_guide_json": {
                "agent": {"standard_prompt": "pp", "accelerated_prompt": "pa"},
                "human": {"standard_command": "ps", "accelerated_command": "pt", "post_install_command": "pu"},
            },
        },
        headers={"Authorization": f"Bearer {publisher_tokens['access_token']}"},
    )
    assert publisher_patch.status_code == 200

    rollback_version_detail = client.get(
        f"/api/admin/versions/{archived_version.id}",
        headers={"Authorization": f"Bearer {publisher_tokens['access_token']}"},
    )
    assert rollback_version_detail.status_code == 200
    assert rollback_version_detail.json()["data"]["capabilities"]["rollback"] is True

    owner_downloads = client.get(
        f"/api/admin/skills/{draft_skill.id}/downloads",
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
    )
    assert owner_downloads.status_code == 200
    owner_payload = owner_downloads.json()["data"]
    assert owner_payload[0]["ip"] is None
    assert owner_payload[0]["display_name"] is None
    assert owner_payload[1]["ip"] is None
    assert owner_payload[1]["display_name"] == reviewer_user.display_name

    admin_downloads = client.get(
        f"/api/admin/skills/{draft_skill.id}/downloads",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert admin_downloads.status_code == 200
    admin_payload = admin_downloads.json()["data"]
    assert {item["ip"] for item in admin_payload} == {"10.0.0.1", "10.0.0.2"}


def test_only_owner_can_manage_skill_grants(client: TestClient, db_session: Session) -> None:
    owner_user = _create_user_with_permissions(
        db_session,
        username="skill_grant_owner",
        permission_codes=["skill.view", "skill.edit"],
    )
    maintainer_user = _create_user_with_permissions(
        db_session,
        username="skill_grant_maintainer",
        permission_codes=["skill.view", "skill.edit"],
    )
    reviewer_role_id = db_session.execute(select(Role.id).where(Role.code == "reviewer")).scalar_one()
    skill, _ = create_skill_version_record(
        db_session,
        owner=owner_user,
        slug="owner-only-grants",
        version="1.0.0",
        category_slug="developer-tools",
        name="Owner Only Grants",
        summary="owner grants",
        description="owner grants",
        review_status="draft",
        create_default_grants=False,
    )
    db_session.add_all(
        [
            SkillUserGrant(skill_id=skill.id, user_id=owner_user.id, permission_scope="owner"),
            SkillUserGrant(skill_id=skill.id, user_id=maintainer_user.id, permission_scope="maintainer"),
        ]
    )
    db_session.commit()

    owner_tokens = _login(client, owner_user.username, "Pass123!")
    maintainer_tokens = _login(client, maintainer_user.username, "Pass123!")

    maintainer_detail = client.get(
        f"/api/admin/skills/{skill.id}",
        headers={"Authorization": f"Bearer {maintainer_tokens['access_token']}"},
    )
    assert maintainer_detail.status_code == 200
    assert maintainer_detail.json()["data"]["capabilities"]["manage_grants"] is False

    maintainer_response = client.post(
        f"/api/admin/skills/{skill.id}/role-grants",
        json={"target_ids": [str(reviewer_role_id)], "permission_scope": "reviewer"},
        headers={"Authorization": f"Bearer {maintainer_tokens['access_token']}"},
    )
    assert maintainer_response.status_code == 403

    owner_response = client.post(
        f"/api/admin/skills/{skill.id}/role-grants",
        json={"target_ids": [str(reviewer_role_id)], "permission_scope": "reviewer"},
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
    )
    assert owner_response.status_code == 200


def test_favorite_requires_login_and_download_updates_counter(client: TestClient, db_session: Session) -> None:
    skill, _ = _create_published_workflow_skill(db_session)
    before_download = skill.download_count

    favorite_response = client.post(f"/api/public/skills/{skill.id}/favorite")
    assert favorite_response.status_code == 401

    like_response = client.post(f"/api/public/skills/{skill.id}/like")
    assert like_response.status_code == 401

    download_response = client.get(f"/api/public/skills/{skill.id}/download")
    assert download_response.status_code == 200

    db_session.expire_all()
    refreshed_skill = db_session.execute(select(Skill).where(Skill.id == skill.id)).scalar_one()
    assert refreshed_skill.download_count == before_download + 1


def test_like_toggle_requires_login_and_updates_counter(client: TestClient, db_session: Session) -> None:
    skill, _ = _create_published_workflow_skill(db_session)
    admin = _login(client, "admin", "ChangeMe123!")
    before_like = skill.like_count

    like_response = client.post(
        f"/api/public/skills/{skill.id}/like",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert like_response.status_code == 200
    assert like_response.json()["data"]["liked"] is True

    duplicate_like = client.post(
        f"/api/public/skills/{skill.id}/like",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert duplicate_like.status_code == 200

    unlike_response = client.delete(
        f"/api/public/skills/{skill.id}/like",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert unlike_response.status_code == 200
    assert unlike_response.json()["data"]["liked"] is False

    db_session.expire_all()
    refreshed_skill = db_session.execute(select(Skill).where(Skill.id == skill.id)).scalar_one()
    assert refreshed_skill.like_count == before_like


def test_public_skill_detail_cache_keeps_logged_in_like_state(client: TestClient, db_session: Session) -> None:
    skill, _ = _create_published_workflow_skill(db_session)

    anonymous_response = client.get("/api/public/skills/workflow-copilot")
    assert anonymous_response.status_code == 200
    assert anonymous_response.json()["data"]["is_liked"] is False

    admin = _login(client, "admin", "ChangeMe123!")
    like_response = client.post(
        f"/api/public/skills/{skill.id}/like",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert like_response.status_code == 200

    detail_response = client.get(
        "/api/public/skills/workflow-copilot",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["is_liked"] is True


def test_publish_archives_previous_version_and_rollback_restores_history(client: TestClient, db_session: Session) -> None:
    _create_published_workflow_skill(db_session)
    admin = _login(client, "admin", "ChangeMe123!")
    files = {"file": ("workflow-next.zip", _make_zip(slug="workflow-copilot", version="1.5.0"), "application/zip")}

    upload_response = client.post("/api/admin/skills/upload", files=files, headers={"Authorization": f"Bearer {admin['access_token']}"})
    version_id = upload_response.json()["data"]["version_id"]
    client.post(f"/api/admin/versions/{version_id}/approve", json={"comment": ""}, headers={"Authorization": f"Bearer {admin['access_token']}"})
    publish_response = client.post(f"/api/admin/versions/{version_id}/publish", json={"comment": "publish"}, headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert publish_response.status_code == 200

    workflow_skill = db_session.execute(select(Skill).where(Skill.slug == "workflow-copilot")).scalar_one()
    previous_version = db_session.execute(
        select(SkillVersion).where(SkillVersion.skill_id == workflow_skill.id, SkillVersion.version == "1.4.0")
    ).scalar_one()
    assert previous_version.review_status == "archived"

    rollback_response = client.post(
        f"/api/admin/versions/{previous_version.id}/rollback",
        json={"comment": "restore stable"},
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert rollback_response.status_code == 200

    public_detail = client.get("/api/public/skills/workflow-copilot")
    assert public_detail.json()["data"]["current_version"]["version"] == "1.4.0"


def test_rollback_uses_dedicated_skill_scope(client: TestClient, db_session: Session) -> None:
    admin = _admin_user(db_session)
    archived_skill, archived_version = create_skill_version_record(
        db_session,
        owner=admin,
        slug="scoped-rollback-skill",
        version="1.0.0",
        category_slug="developer-tools",
        name="Scoped Rollback Skill",
        summary="rollback scope test",
        description="rollback scope test",
        review_status="archived",
        create_default_grants=False,
    )
    create_skill_version_record(
        db_session,
        owner=admin,
        slug="scoped-rollback-skill",
        version="1.1.0",
        category_slug="developer-tools",
        name="Scoped Rollback Skill",
        summary="rollback scope test",
        description="rollback scope test",
        review_status="published",
        create_default_grants=False,
    )
    rollback_user = _create_user_with_permissions(
        db_session,
        username="rollback_only_user",
        permission_codes=["skill.view", "skill.rollback"],
    )
    db_session.add_all(
        [
            SkillUserGrant(skill_id=archived_skill.id, user_id=admin.id, permission_scope="owner"),
            SkillUserGrant(skill_id=archived_skill.id, user_id=rollback_user.id, permission_scope="rollback"),
        ]
    )
    db_session.commit()

    rollback_tokens = _login(client, rollback_user.username, "Pass123!")
    rollback_response = client.post(
        f"/api/admin/versions/{archived_version.id}/rollback",
        json={"comment": "restore archived version"},
        headers={"Authorization": f"Bearer {rollback_tokens['access_token']}"},
    )
    assert rollback_response.status_code == 200


def test_submitted_version_does_not_override_public_skill_metadata_before_publish(client: TestClient, db_session: Session) -> None:
    _create_published_workflow_skill(db_session)
    admin = _login(client, "admin", "ChangeMe123!")
    files = {
        "file": (
            "workflow-next.zip",
            _make_zip(
                slug="workflow-copilot",
                version="1.5.0",
                name="Workflow Copilot X",
                summary="new summary that should stay hidden before publish",
                description="new description that should stay hidden before publish",
                category="content-creation",
            ),
            "application/zip",
        )
    }

    upload_response = client.post("/api/admin/skills/upload", files=files, headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert upload_response.status_code == 200

    public_detail_before = client.get("/api/public/skills/workflow-copilot")
    assert public_detail_before.status_code == 200
    before_payload = public_detail_before.json()["data"]
    assert before_payload["skill"]["name"] == "Workflow Copilot"
    assert before_payload["skill"]["summary"] == "为内部流程提供模板化编排与执行建议。"
    assert before_payload["skill"]["category_slug"] == "productivity"
    assert before_payload["current_version"]["version"] == "1.4.0"
    before_standard_prompt = before_payload["usage_guide"]["agent"]["standard_prompt"]

    version_id = upload_response.json()["data"]["version_id"]
    version_patch = client.patch(
        f"/api/admin/versions/{version_id}",
        json={
            "changelog": "guide update",
            "install_notes": "draft install notes",
            "breaking_changes": "",
            "readme_markdown": "# Workflow Copilot X\n\nupdated\n",
            "usage_guide_json": {
                "agent": {
                    "standard_prompt": "draft guide that should stay hidden",
                    "accelerated_prompt": "draft accelerated guide that should stay hidden",
                },
                "human": {
                    "standard_command": "echo draft standard",
                    "accelerated_command": "echo draft accelerated",
                    "post_install_command": "echo draft post install",
                },
            },
        },
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert version_patch.status_code == 200
    client.post(f"/api/admin/versions/{version_id}/approve", json={"comment": ""}, headers={"Authorization": f"Bearer {admin['access_token']}"})
    publish_response = client.post(f"/api/admin/versions/{version_id}/publish", json={"comment": "publish"}, headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert publish_response.status_code == 200

    public_detail_after = client.get("/api/public/skills/workflow-copilot")
    after_payload = public_detail_after.json()["data"]
    assert after_payload["skill"]["name"] == "Workflow Copilot X"
    assert after_payload["skill"]["summary"] == "new summary that should stay hidden before publish"
    assert after_payload["skill"]["category_slug"] == "content-creation"
    assert after_payload["current_version"]["version"] == "1.5.0"
    assert before_standard_prompt != "draft guide that should stay hidden"
    assert after_payload["usage_guide"]["agent"]["standard_prompt"] == "draft guide that should stay hidden"


def test_public_skill_detail_ignores_invalid_optional_token(client: TestClient, db_session: Session) -> None:
    _create_published_workflow_skill(db_session)

    response = client.get(
        "/api/public/skills/workflow-copilot",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 200


def test_review_release_and_history_queues_follow_database_state(client: TestClient, db_session: Session) -> None:
    admin_user = _admin_user(db_session)
    reviewer_user = _create_user_with_role(db_session, "reviewer", "queue_reviewer")
    create_skill_version_record(
        db_session,
        owner=admin_user,
        slug="workflow-copilot",
        version="1.6.0",
        category_slug="productivity",
        name="Workflow Copilot",
        summary="为内部流程提供模板化编排与执行建议。",
        description="新增审批会签模板。",
        review_status="submitted",
        review_comment="等待审核",
    )
    create_skill_version_record(
        db_session,
        owner=admin_user,
        slug="narrative-writer",
        version="3.1.0",
        category_slug="content-creation",
        name="Narrative Writer",
        summary="为内容团队生成长短文结构、提纲和版本润色建议。",
        description="新增企业品牌语气模板和审批前校对能力。",
        review_status="approved",
        review_comment="审核通过，待发布",
    )
    create_skill_version_record(
        db_session,
        owner=admin_user,
        slug="analytics-scout",
        version="0.9.0",
        category_slug="data-analysis",
        name="Analytics Scout",
        summary="聚合常见报表指标模板，辅助数据分析任务起步。",
        description="仍需补充指标说明。",
        review_status="rejected",
        review_comment="缺少指标说明",
    )
    admin = _login(client, "admin", "ChangeMe123!")

    pending_reviews = client.get(
        "/api/admin/reviews/pending",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert pending_reviews.status_code == 200
    review_items = pending_reviews.json()["data"]
    assert any(item["skill_slug"] == "workflow-copilot" and item["version"] == "1.6.0" for item in review_items)
    workflow_review_item = next(item for item in review_items if item["skill_slug"] == "workflow-copilot" and item["version"] == "1.6.0")
    assert workflow_review_item["assigned_reviewer_details"] == [
        {
            "target_id": workflow_review_item["assigned_reviewer_details"][0]["target_id"],
            "target_type": "role",
            "target_name": "审核员",
            "members": [reviewer_user.display_name],
        }
    ]

    pending_releases = client.get(
        "/api/admin/releases/pending",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert pending_releases.status_code == 200
    release_items = pending_releases.json()["data"]
    assert any(item["skill_slug"] == "narrative-writer" and item["version"] == "3.1.0" for item in release_items)

    history = client.get(
        "/api/admin/reviews/history",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert history.status_code == 200
    history_items = history.json()["data"]
    assert any(item["skill_name"] == "Analytics Scout" and item["action"] == "reject" for item in history_items)


def test_skill_permissions_and_stats_endpoints_return_operational_data(client: TestClient, db_session: Session) -> None:
    skill, version = _create_published_workflow_skill(db_session)
    admin_user = _admin_user(db_session)
    db_session.add(Favorite(skill_id=skill.id, user_id=admin_user.id))
    db_session.add(SkillLike(skill_id=skill.id, user_id=admin_user.id))
    db_session.commit()
    admin = _login(client, "admin", "ChangeMe123!")

    permissions_response = client.get(
        f"/api/admin/skills/{skill.id}/permissions",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert permissions_response.status_code == 200
    permission_items = permissions_response.json()["data"]
    assert any(item["target_type"] == "user" and item["permission_scope"] == "owner" for item in permission_items)
    assert any(item["target_type"] == "role" and item["permission_scope"] == "reviewer" for item in permission_items)

    stats_response = client.get(
        f"/api/admin/skills/{skill.id}/stats",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert stats_response.status_code == 200
    stats_payload = stats_response.json()["data"]
    assert stats_payload["download_count"] >= 1
    assert "recent_downloads" in stats_payload


def test_skill_level_grants_gate_skill_editing(client: TestClient, db_session: Session) -> None:
    skill, _ = _create_published_workflow_skill(db_session)
    contributor = _create_user_with_role(db_session, "contributor", "scoped_contributor")
    contributor_tokens = _login(client, contributor.username, "Pass123!")
    admin = _login(client, "admin", "ChangeMe123!")

    forbidden_patch = client.patch(
        f"/api/admin/skills/{skill.id}",
        json={
            "name": "Workflow Copilot",
            "summary": "attempt without grant",
            "description": "attempt without grant",
            "category_slug": "productivity",
        },
        headers={"Authorization": f"Bearer {contributor_tokens['access_token']}"},
    )
    assert forbidden_patch.status_code == 403

    grant_response = client.post(
        f"/api/admin/skills/{skill.id}/user-grants",
        json={"target_ids": [str(contributor.id)], "permission_scope": "maintainer"},
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert grant_response.status_code == 200

    allowed_patch = client.patch(
        f"/api/admin/skills/{skill.id}",
        json={
            "name": "Workflow Copilot",
            "summary": "maintainer can now edit",
            "description": "maintainer can now edit",
            "category_slug": "productivity",
        },
        headers={"Authorization": f"Bearer {contributor_tokens['access_token']}"},
    )
    assert allowed_patch.status_code == 200
    assert allowed_patch.json()["data"]["slug"] == "workflow-copilot"
    assert allowed_patch.json()["data"]["summary"] == "maintainer can now edit"
