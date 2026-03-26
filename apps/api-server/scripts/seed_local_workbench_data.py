from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile

from sqlalchemy import delete, select, update

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.category import Category
from app.models.download_log import DownloadLog
from app.models.favorite import Favorite
from app.models.file_asset import FileAsset
from app.models.role import Role
from app.models.skill import Skill
from app.models.skill_like import SkillLike
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_tag import SkillTag
from app.models.skill_user_grant import SkillUserGrant
from app.models.skill_version import SkillVersion
from app.models.user import User
from app.models.user_role import UserRole
from app.models.version_review import VersionReview
from app.services.storage import delete_object, ensure_bytes
from app.services.usage_guides import build_default_usage_guide

FIXTURE_SLUGS = [
    "ops-knowledge-base",
    "workflow-review-studio",
    "release-readiness-radar",
    "campaign-copy-lab",
    "draft-data-canvas",
    "rollback-drill-center",
]

FIXTURE_PREFIX = "fixtures/local-workbench"
DEFAULT_PASSWORD = "Pass123!"


def _hash_value(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _build_skill_zip(*, name: str, slug: str, version: str, summary: str, description: str, category_slug: str) -> bytes:
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
                f"category: {category_slug}\n"
                "tags: []\n"
                "author: Local Workbench Fixture\n"
            ),
        )
        archive.writestr("README.md", f"# {name}\n\n{description}\n")
    return buffer.getvalue()


def _ensure_user(session, *, username: str, display_name: str, email: str, role_codes: list[str]) -> User:
    user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None:
        user = User(
            username=username,
            password_hash=hash_password(DEFAULT_PASSWORD),
            display_name=display_name,
            email=email,
            status="active",
        )
        session.add(user)
        session.flush()
    else:
        user.display_name = display_name
        user.email = email
        user.status = "active"

    role_ids = list(session.execute(select(Role.id).where(Role.code.in_(role_codes), Role.is_active.is_(True))).scalars())
    current_role_ids = set(session.execute(select(UserRole.role_id).where(UserRole.user_id == user.id)).scalars())
    for role_id in role_ids:
        if role_id not in current_role_ids:
            session.add(UserRole(user_id=user.id, role_id=role_id))
    session.flush()
    return user


def _ensure_assets(
    session,
    *,
    owner: User,
    slug: str,
    version: str,
    name: str,
    summary: str,
    description: str,
    category_slug: str,
) -> tuple[FileAsset, FileAsset]:
    package_key = f"{FIXTURE_PREFIX}/{slug}/package-{version}.zip"
    readme_key = f"{FIXTURE_PREFIX}/{slug}/README-{version}.md"
    package_bytes = _build_skill_zip(
        name=name,
        slug=slug,
        version=version,
        summary=summary,
        description=description,
        category_slug=category_slug,
    )
    readme_text = f"# {name}\n\n{description}\n"
    ensure_bytes(package_key, package_bytes)
    ensure_bytes(readme_key, readme_text.encode("utf-8"))

    package_asset = FileAsset(
        bucket="local",
        object_key=package_key,
        original_name=f"{slug}-{version}.zip",
        mime_type="application/zip",
        size_bytes=len(package_bytes),
        sha256=_hash_value(f"pkg:{slug}:{version}"),
        file_kind="package",
        created_by=owner.id,
    )
    readme_asset = FileAsset(
        bucket="local",
        object_key=readme_key,
        original_name="README.md",
        mime_type="text/markdown",
        size_bytes=len(readme_text.encode("utf-8")),
        sha256=_hash_value(f"readme:{slug}:{version}"),
        file_kind="readme",
        created_by=owner.id,
    )
    session.add_all([package_asset, readme_asset])
    session.flush()
    return package_asset, readme_asset


def _create_version(
    session,
    *,
    skill: Skill,
    owner: User,
    version: str,
    name: str,
    summary: str,
    description: str,
    category_slug: str,
    review_status: str,
    install_notes: str,
    changelog: str,
    review_comment: str | None,
    reviewed_by: User | None = None,
    published_by: User | None = None,
    reviewed_at: datetime | None = None,
    published_at: datetime | None = None,
) -> SkillVersion:
    package_asset, readme_asset = _ensure_assets(
        session,
        owner=owner,
        slug=skill.slug,
        version=version,
        name=name,
        summary=summary,
        description=description,
        category_slug=category_slug,
    )
    version_row = SkillVersion(
        skill_id=skill.id,
        version=version,
        manifest_json={
            "name": name,
            "slug": skill.slug,
            "version": version,
            "summary": summary,
            "description": description,
            "category": category_slug,
            "tags": [],
            "author": owner.display_name,
        },
        usage_guide_json=build_default_usage_guide(
            skill_id=skill.id,
            skill_name=name,
            skill_slug=skill.slug,
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
        reviewed_by=reviewed_by.id if reviewed_by else None,
        reviewed_at=reviewed_at,
        published_by=published_by.id if published_by else None,
        published_at=published_at,
        created_by=owner.id,
    )
    session.add(version_row)
    session.flush()
    return version_row


def _add_review(session, *, version: SkillVersion, action: str, comment: str, operator: User, created_at: datetime | None = None) -> None:
    review = VersionReview(
        skill_version_id=version.id,
        action=action,
        comment=comment,
        operator_user_id=operator.id,
    )
    if created_at is not None:
        review.created_at = created_at
    session.add(review)


def _grant_defaults(session, *, skill: Skill, owner: User, reviewer_role: Role, publisher_role: Role, reviewer_user: User, publisher_user: User) -> None:
    session.add_all(
        [
            SkillUserGrant(skill_id=skill.id, user_id=owner.id, permission_scope="owner"),
            SkillUserGrant(skill_id=skill.id, user_id=owner.id, permission_scope="maintainer"),
            SkillUserGrant(skill_id=skill.id, user_id=reviewer_user.id, permission_scope="reviewer"),
            SkillUserGrant(skill_id=skill.id, user_id=publisher_user.id, permission_scope="publisher"),
            SkillRoleGrant(skill_id=skill.id, role_id=reviewer_role.id, permission_scope="reviewer"),
            SkillRoleGrant(skill_id=skill.id, role_id=publisher_role.id, permission_scope="publisher"),
        ]
    )


def _cleanup_existing_fixtures(session) -> None:
    fixture_skill_ids = list(session.execute(select(Skill.id).where(Skill.slug.in_(FIXTURE_SLUGS))).scalars())
    if fixture_skill_ids:
        session.execute(update(Skill).where(Skill.id.in_(fixture_skill_ids)).values(current_published_version_id=None, published_at=None))
        fixture_version_ids = list(session.execute(select(SkillVersion.id).where(SkillVersion.skill_id.in_(fixture_skill_ids))).scalars())
        if fixture_version_ids:
            session.execute(delete(VersionReview).where(VersionReview.skill_version_id.in_(fixture_version_ids)))
            session.execute(delete(DownloadLog).where(DownloadLog.skill_version_id.in_(fixture_version_ids)))
        session.execute(delete(SkillRoleGrant).where(SkillRoleGrant.skill_id.in_(fixture_skill_ids)))
        session.execute(delete(SkillUserGrant).where(SkillUserGrant.skill_id.in_(fixture_skill_ids)))
        session.execute(delete(Favorite).where(Favorite.skill_id.in_(fixture_skill_ids)))
        session.execute(delete(SkillLike).where(SkillLike.skill_id.in_(fixture_skill_ids)))
        session.execute(delete(DownloadLog).where(DownloadLog.skill_id.in_(fixture_skill_ids)))
        session.execute(delete(SkillTag).where(SkillTag.skill_id.in_(fixture_skill_ids)))
        session.execute(delete(SkillVersion).where(SkillVersion.skill_id.in_(fixture_skill_ids)))
        session.execute(delete(Skill).where(Skill.id.in_(fixture_skill_ids)))

    fixture_assets = list(session.execute(select(FileAsset).where(FileAsset.object_key.like(f"{FIXTURE_PREFIX}/%"))).scalars())
    for asset in fixture_assets:
        delete_object(asset.object_key)
    if fixture_assets:
        session.execute(delete(FileAsset).where(FileAsset.id.in_([asset.id for asset in fixture_assets])))
    session.flush()


def seed_local_workbench_data() -> dict[str, int]:
    with SessionLocal() as session:
        admin = session.execute(select(User).where(User.username == "admin")).scalar_one()
        contributor = _ensure_user(
            session,
            username="fixture_contributor",
            display_name="Fixture Contributor",
            email="fixture-contributor@skillhub.local",
            role_codes=["contributor"],
        )
        reviewer = _ensure_user(
            session,
            username="fixture_reviewer",
            display_name="Fixture Reviewer",
            email="fixture-reviewer@skillhub.local",
            role_codes=["reviewer"],
        )
        publisher = _ensure_user(
            session,
            username="fixture_publisher",
            display_name="Fixture Publisher",
            email="fixture-publisher@skillhub.local",
            role_codes=["publisher"],
        )
        observer = _ensure_user(
            session,
            username="fixture_observer",
            display_name="Fixture Observer",
            email="fixture-observer@skillhub.local",
            role_codes=["viewer"],
        )

        reviewer_role = session.execute(select(Role).where(Role.code == "reviewer")).scalar_one()
        publisher_role = session.execute(select(Role).where(Role.code == "publisher")).scalar_one()

        categories = {
            item.slug: item
            for item in session.execute(select(Category).where(Category.slug.in_([
                "developer-tools",
                "productivity",
                "content-creation",
                "data-analysis",
                "security-compliance",
                "communication-collaboration",
            ])).order_by(Category.slug)).scalars()
        }

        _cleanup_existing_fixtures(session)
        now = datetime.now(UTC)

        created_skills = 0

        # 1. published only
        skill = Skill(
            name="Ops Knowledge Base",
            slug="ops-knowledge-base",
            summary="沉淀运维 FAQ、故障定位和 SOP 的知识型技能。",
            description="适合值班、SRE 和支持团队快速查询故障知识库。",
            owner_user_id=contributor.id,
            category_id=categories["developer-tools"].id,
            icon_file_id=None,
            status="active",
            current_published_version_id=None,
            latest_version_no="1.2.0",
            view_count=124,
            download_count=41,
            favorite_count=9,
            like_count=12,
            published_at=now - timedelta(days=5),
        )
        session.add(skill)
        session.flush()
        _grant_defaults(session, skill=skill, owner=contributor, reviewer_role=reviewer_role, publisher_role=publisher_role, reviewer_user=reviewer, publisher_user=publisher)
        published = _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="1.2.0",
            name=skill.name,
            summary=skill.summary,
            description=skill.description,
            category_slug="developer-tools",
            review_status="published",
            install_notes="下载后按 README 指引接入内部知识检索链路。",
            changelog="补充值班 SOP 模板和故障定位章节。",
            review_comment="稳定版已上线",
            reviewed_by=reviewer,
            published_by=publisher,
            reviewed_at=now - timedelta(days=5, hours=3),
            published_at=now - timedelta(days=5),
        )
        skill.current_published_version_id = published.id
        _add_review(session, version=published, action="submit", comment="提审基础知识库版本", operator=contributor, created_at=now - timedelta(days=5, hours=6))
        _add_review(session, version=published, action="approve", comment="审核通过", operator=reviewer, created_at=now - timedelta(days=5, hours=3))
        _add_review(session, version=published, action="publish", comment="正式上线", operator=publisher, created_at=now - timedelta(days=5))
        session.add_all([
            Favorite(skill_id=skill.id, user_id=reviewer.id),
            Favorite(skill_id=skill.id, user_id=observer.id),
            SkillLike(skill_id=skill.id, user_id=reviewer.id),
            SkillLike(skill_id=skill.id, user_id=observer.id),
            DownloadLog(skill_id=skill.id, skill_version_id=published.id, user_id=reviewer.id, ip=None, user_agent="fixture"),
            DownloadLog(skill_id=skill.id, skill_version_id=published.id, user_id=observer.id, ip=None, user_agent="fixture"),
        ])
        created_skills += 1

        # 2. published + submitted
        skill = Skill(
            name="Workflow Review Studio",
            slug="workflow-review-studio",
            summary="帮助产品和运营团队校验工作流设计与审批节点。",
            description="当前线上版本可用，同时有一个新版本正在待审核。",
            owner_user_id=contributor.id,
            category_id=categories["productivity"].id,
            icon_file_id=None,
            status="active",
            current_published_version_id=None,
            latest_version_no="1.1.0",
            view_count=88,
            download_count=27,
            favorite_count=6,
            like_count=8,
            published_at=now - timedelta(days=2),
        )
        session.add(skill)
        session.flush()
        _grant_defaults(session, skill=skill, owner=contributor, reviewer_role=reviewer_role, publisher_role=publisher_role, reviewer_user=reviewer, publisher_user=publisher)
        published = _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="1.0.0",
            name=skill.name,
            summary=skill.summary,
            description=skill.description,
            category_slug="productivity",
            review_status="published",
            install_notes="当前线上稳定版。",
            changelog="初始稳定版本。",
            review_comment="已上线",
            reviewed_by=reviewer,
            published_by=publisher,
            reviewed_at=now - timedelta(days=2, hours=4),
            published_at=now - timedelta(days=2),
        )
        skill.current_published_version_id = published.id
        submitted = _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="1.1.0",
            name=skill.name,
            summary="帮助产品和运营团队校验工作流设计与审批节点。",
            description="新增会签节点检查与串并联校验规则。",
            category_slug="productivity",
            review_status="submitted",
            install_notes="待审核版本，先不要线上启用。",
            changelog="新增会签节点检查。",
            review_comment="等待审核",
        )
        _add_review(session, version=published, action="submit", comment="提审 1.0.0", operator=contributor, created_at=now - timedelta(days=2, hours=8))
        _add_review(session, version=published, action="approve", comment="审核通过 1.0.0", operator=reviewer, created_at=now - timedelta(days=2, hours=4))
        _add_review(session, version=published, action="publish", comment="上线 1.0.0", operator=publisher, created_at=now - timedelta(days=2))
        _add_review(session, version=submitted, action="submit", comment="请审核 1.1.0", operator=contributor, created_at=now - timedelta(hours=5))
        created_skills += 1

        # 3. published + approved waiting release
        skill = Skill(
            name="Release Readiness Radar",
            slug="release-readiness-radar",
            summary="帮助团队在发布前核对依赖、配置和风险项。",
            description="当前有一个已通过审核但未正式发布的新版本，方便测试待发布队列。",
            owner_user_id=contributor.id,
            category_id=categories["security-compliance"].id,
            icon_file_id=None,
            status="active",
            current_published_version_id=None,
            latest_version_no="2.1.0",
            view_count=76,
            download_count=19,
            favorite_count=4,
            like_count=5,
            published_at=now - timedelta(days=8),
        )
        session.add(skill)
        session.flush()
        _grant_defaults(session, skill=skill, owner=contributor, reviewer_role=reviewer_role, publisher_role=publisher_role, reviewer_user=reviewer, publisher_user=publisher)
        published = _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="2.0.0",
            name=skill.name,
            summary=skill.summary,
            description=skill.description,
            category_slug="security-compliance",
            review_status="published",
            install_notes="线上稳定版。",
            changelog="稳定版基线检查清单。",
            review_comment="线上稳定版",
            reviewed_by=reviewer,
            published_by=publisher,
            reviewed_at=now - timedelta(days=8, hours=3),
            published_at=now - timedelta(days=8),
        )
        skill.current_published_version_id = published.id
        approved = _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="2.1.0",
            name=skill.name,
            summary=skill.summary,
            description="新增发布前依赖扫描提示与变更项摘要。",
            category_slug="security-compliance",
            review_status="approved",
            install_notes="已审核通过，待发布。",
            changelog="新增依赖扫描提示。",
            review_comment="审核通过，待发布",
            reviewed_by=reviewer,
            reviewed_at=now - timedelta(hours=9),
        )
        _add_review(session, version=published, action="submit", comment="提审 2.0.0", operator=contributor, created_at=now - timedelta(days=8, hours=6))
        _add_review(session, version=published, action="approve", comment="审核通过 2.0.0", operator=reviewer, created_at=now - timedelta(days=8, hours=3))
        _add_review(session, version=published, action="publish", comment="上线 2.0.0", operator=publisher, created_at=now - timedelta(days=8))
        _add_review(session, version=approved, action="submit", comment="请审核 2.1.0", operator=contributor, created_at=now - timedelta(hours=12))
        _add_review(session, version=approved, action="approve", comment="审核通过，待发布", operator=reviewer, created_at=now - timedelta(hours=9))
        created_skills += 1

        # 4. rejected
        skill = Skill(
            name="Campaign Copy Lab",
            slug="campaign-copy-lab",
            summary="用于投放文案和活动页面文案的批量生成与审校。",
            description="当前最新版本被拒绝，适合验证处理记录和版本详情。",
            owner_user_id=contributor.id,
            category_id=categories["content-creation"].id,
            icon_file_id=None,
            status="active",
            current_published_version_id=None,
            latest_version_no="0.9.0",
            view_count=24,
            download_count=0,
            favorite_count=1,
            like_count=2,
            published_at=None,
        )
        session.add(skill)
        session.flush()
        _grant_defaults(session, skill=skill, owner=contributor, reviewer_role=reviewer_role, publisher_role=publisher_role, reviewer_user=reviewer, publisher_user=publisher)
        rejected = _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="0.9.0",
            name=skill.name,
            summary=skill.summary,
            description=skill.description,
            category_slug="content-creation",
            review_status="rejected",
            install_notes="需要补充品牌语气说明后再提审。",
            changelog="初版文案模板。",
            review_comment="缺少品牌语气说明",
            reviewed_by=reviewer,
            reviewed_at=now - timedelta(days=1, hours=2),
        )
        _add_review(session, version=rejected, action="submit", comment="提审 0.9.0", operator=contributor, created_at=now - timedelta(days=1, hours=6))
        _add_review(session, version=rejected, action="reject", comment="缺少品牌语气说明", operator=reviewer, created_at=now - timedelta(days=1, hours=2))
        created_skills += 1

        # 5. draft only
        skill = Skill(
            name="Draft Data Canvas",
            slug="draft-data-canvas",
            summary="帮助分析师搭建数据问题排查和图表说明的初始画布。",
            description="当前仍处于草稿态，方便测试未提审技能。",
            owner_user_id=contributor.id,
            category_id=categories["data-analysis"].id,
            icon_file_id=None,
            status="active",
            current_published_version_id=None,
            latest_version_no="0.3.0",
            view_count=11,
            download_count=0,
            favorite_count=0,
            like_count=0,
            published_at=None,
        )
        session.add(skill)
        session.flush()
        _grant_defaults(session, skill=skill, owner=contributor, reviewer_role=reviewer_role, publisher_role=publisher_role, reviewer_user=reviewer, publisher_user=publisher)
        _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="0.3.0",
            name=skill.name,
            summary=skill.summary,
            description=skill.description,
            category_slug="data-analysis",
            review_status="draft",
            install_notes="仅草稿。",
            changelog="草稿中。",
            review_comment=None,
        )
        created_skills += 1

        # 6. archived history + current published
        skill = Skill(
            name="Rollback Drill Center",
            slug="rollback-drill-center",
            summary="模拟版本发布、归档和回滚的演练技能。",
            description="方便你测试处理记录、历史版本和当前线上版本切换。",
            owner_user_id=contributor.id,
            category_id=categories["communication-collaboration"].id,
            icon_file_id=None,
            status="active",
            current_published_version_id=None,
            latest_version_no="1.1.0",
            view_count=65,
            download_count=13,
            favorite_count=3,
            like_count=4,
            published_at=now - timedelta(days=4),
        )
        session.add(skill)
        session.flush()
        _grant_defaults(session, skill=skill, owner=contributor, reviewer_role=reviewer_role, publisher_role=publisher_role, reviewer_user=reviewer, publisher_user=publisher)
        archived = _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="1.0.0",
            name=skill.name,
            summary=skill.summary,
            description="历史归档版本，用于演示归档记录。",
            category_slug="communication-collaboration",
            review_status="archived",
            install_notes="历史版本。",
            changelog="初始历史版本。",
            review_comment="已归档",
            reviewed_by=reviewer,
            published_by=publisher,
            reviewed_at=now - timedelta(days=10, hours=4),
            published_at=now - timedelta(days=10),
        )
        current = _create_version(
            session,
            skill=skill,
            owner=contributor,
            version="1.1.0",
            name=skill.name,
            summary=skill.summary,
            description=skill.description,
            category_slug="communication-collaboration",
            review_status="published",
            install_notes="当前线上版本。",
            changelog="回滚演练后的当前线上版本。",
            review_comment="当前线上版本",
            reviewed_by=reviewer,
            published_by=publisher,
            reviewed_at=now - timedelta(days=4, hours=3),
            published_at=now - timedelta(days=4),
        )
        skill.current_published_version_id = current.id
        _add_review(session, version=archived, action="submit", comment="提审 1.0.0", operator=contributor, created_at=now - timedelta(days=10, hours=8))
        _add_review(session, version=archived, action="approve", comment="审核通过 1.0.0", operator=reviewer, created_at=now - timedelta(days=10, hours=4))
        _add_review(session, version=archived, action="publish", comment="上线 1.0.0", operator=publisher, created_at=now - timedelta(days=10))
        _add_review(session, version=archived, action="archive", comment="归档 1.0.0", operator=publisher, created_at=now - timedelta(days=6))
        _add_review(session, version=current, action="submit", comment="提审 1.1.0", operator=contributor, created_at=now - timedelta(days=5, hours=8))
        _add_review(session, version=current, action="approve", comment="审核通过 1.1.0", operator=reviewer, created_at=now - timedelta(days=5, hours=4))
        _add_review(session, version=current, action="publish", comment="上线 1.1.0", operator=publisher, created_at=now - timedelta(days=5))
        _add_review(session, version=archived, action="rollback_publish", comment="保留历史回滚记录演示", operator=publisher, created_at=now - timedelta(days=4, hours=20))
        session.add_all([
            Favorite(skill_id=skill.id, user_id=observer.id),
            SkillLike(skill_id=skill.id, user_id=observer.id),
            DownloadLog(skill_id=skill.id, skill_version_id=current.id, user_id=observer.id, ip=None, user_agent="fixture"),
        ])
        created_skills += 1

        session.commit()
        return {
            "skills": created_skills,
            "published": 4,
            "submitted": 1,
            "approved": 1,
            "rejected": 1,
            "draft": 1,
            "archived_versions": 1,
            "users": 4,
        }


def main() -> None:
    result = seed_local_workbench_data()
    print(
        "seeded local workbench data:",
        f"{result['skills']} skills,",
        f"published={result['published']},",
        f"submitted={result['submitted']},",
        f"approved={result['approved']},",
        f"rejected={result['rejected']},",
        f"draft={result['draft']},",
        f"archived_versions={result['archived_versions']},",
        f"users={result['users']}",
    )


if __name__ == "__main__":
    main()
