from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.download_log import DownloadLog
from app.models.favorite import Favorite
from app.models.file_asset import FileAsset
from app.models.role import Role
from app.models.skill import Skill
from app.models.skill_like import SkillLike
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_user_grant import SkillUserGrant
from app.models.skill_version import SkillVersion
from app.models.user import User
from app.models.version_review import VersionReview
from app.services.storage import ensure_bytes
from app.services.usage_guides import build_default_usage_guide


def make_skill_zip(
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


def create_skill_version_record(
    db: Session,
    *,
    owner: User,
    slug: str,
    version: str,
    category_slug: str,
    name: str,
    summary: str,
    description: str,
    review_status: str,
    review_comment: str | None = None,
    download_count: int = 0,
    favorite_count: int = 0,
    like_count: int = 0,
    install_notes: str = "test install notes",
    changelog: str = "test changelog",
    create_default_grants: bool = True,
) -> tuple[Skill, SkillVersion]:
    category = db.execute(select(Category).where(Category.slug == category_slug)).scalar_one()
    skill = db.execute(select(Skill).where(Skill.slug == slug)).scalar_one_or_none()
    now = datetime.now(UTC)

    if skill is None:
        skill = Skill(
            name=name,
            slug=slug,
            summary=summary,
            description=description,
            owner_user_id=owner.id,
            category_id=category.id,
            icon_file_id=None,
            status="active",
            current_published_version_id=None,
            latest_version_no=version,
            view_count=0,
            download_count=download_count,
            favorite_count=favorite_count,
            like_count=like_count,
            published_at=now if review_status == "published" else None,
        )
        db.add(skill)
        db.flush()
    else:
        skill.latest_version_no = version
        skill.name = name
        skill.summary = summary
        skill.description = description
        skill.category_id = category.id

    object_prefix = f"tests/generated/{slug}"
    package_asset = FileAsset(
        bucket="skill-hub",
        object_key=f"{object_prefix}/{version}.zip",
        original_name=f"{slug}-{version}.zip",
        mime_type="application/zip",
        size_bytes=2048,
        sha256=sha256(f"pkg:{slug}:{version}".encode("utf-8")).hexdigest(),
        file_kind="package",
        created_by=owner.id,
    )
    readme_asset = FileAsset(
        bucket="skill-hub",
        object_key=f"{object_prefix}/README-{version}.md",
        original_name="README.md",
        mime_type="text/markdown",
        size_bytes=512,
        sha256=sha256(f"readme:{slug}:{version}".encode("utf-8")).hexdigest(),
        file_kind="readme",
        created_by=owner.id,
    )
    db.add_all([package_asset, readme_asset])
    db.flush()

    ensure_bytes(
        package_asset.object_key,
        make_skill_zip(
            slug=slug,
            version=version,
            name=name,
            summary=summary,
            description=description,
            category=category_slug,
        ),
    )
    ensure_bytes(readme_asset.object_key, f"# {name}\n\n{description}\n".encode("utf-8"))

    skill_version = SkillVersion(
        skill_id=skill.id,
        version=version,
        manifest_json={
            "name": name,
            "slug": slug,
            "version": version,
            "summary": summary,
            "description": description,
            "category": category_slug,
            "tags": [],
            "author": "test author",
        },
        usage_guide_json=build_default_usage_guide(
            skill_id=skill.id,
            skill_name=name,
            skill_slug=slug,
            summary=summary,
            description=description,
            install_notes=install_notes,
        ),
        changelog=changelog,
        install_notes=install_notes,
        breaking_changes="",
        readme_markdown=f"# {name}\n\n{description}\n",
        source_type="upload_zip",
        package_file_id=package_asset.id,
        readme_file_id=readme_asset.id,
        review_status=review_status,
        review_comment=review_comment,
        reviewed_by=owner.id if review_status in {"approved", "published", "rejected"} else None,
        reviewed_at=now if review_status in {"approved", "published", "rejected"} else None,
        published_by=owner.id if review_status == "published" else None,
        published_at=now if review_status == "published" else None,
        created_by=owner.id,
    )
    db.add(skill_version)
    db.flush()

    if review_status == "published":
        skill.current_published_version_id = skill_version.id
        skill.published_at = now
        db.add(
            VersionReview(
                skill_version_id=skill_version.id,
                action="publish",
                comment=review_comment or "published for test",
                operator_user_id=owner.id,
            )
        )
    elif review_status == "approved":
        db.add(
            VersionReview(
                skill_version_id=skill_version.id,
                action="approve",
                comment=review_comment or "approved for test",
                operator_user_id=owner.id,
            )
        )
    elif review_status == "submitted":
        db.add(
            VersionReview(
                skill_version_id=skill_version.id,
                action="submit",
                comment=review_comment or "submitted for test",
                operator_user_id=owner.id,
            )
        )
    elif review_status == "rejected":
        db.add_all(
            [
                VersionReview(
                    skill_version_id=skill_version.id,
                    action="submit",
                    comment="submitted for test",
                    operator_user_id=owner.id,
                ),
                VersionReview(
                    skill_version_id=skill_version.id,
                    action="reject",
                    comment=review_comment or "rejected for test",
                    operator_user_id=owner.id,
                ),
            ]
        )

    if create_default_grants:
        db.add_all(
            [
                SkillUserGrant(skill_id=skill.id, user_id=owner.id, permission_scope="owner"),
                SkillUserGrant(skill_id=skill.id, user_id=owner.id, permission_scope="maintainer"),
            ]
        )
        reviewer_role_id = db.execute(select(Role.id).where(Role.code == "reviewer")).scalar_one_or_none()
        publisher_role_id = db.execute(select(Role.id).where(Role.code == "publisher")).scalar_one_or_none()
        if reviewer_role_id:
            db.add(SkillRoleGrant(skill_id=skill.id, role_id=reviewer_role_id, permission_scope="reviewer"))
        if publisher_role_id:
            db.add(SkillRoleGrant(skill_id=skill.id, role_id=publisher_role_id, permission_scope="publisher"))

    db.commit()
    db.refresh(skill)
    db.refresh(skill_version)
    return skill, skill_version


def add_favorite(db: Session, *, skill_id, user_id) -> None:
    db.add(Favorite(skill_id=skill_id, user_id=user_id))
    db.commit()


def add_like(db: Session, *, skill_id, user_id) -> None:
    db.add(SkillLike(skill_id=skill_id, user_id=user_id))
    db.commit()


def add_download(db: Session, *, skill_id, version_id, user_id=None) -> None:
    db.add(
        DownloadLog(
            skill_id=skill_id,
            skill_version_id=version_id,
            user_id=user_id,
            ip=None,
            user_agent="pytest",
        )
    )
    db.commit()
