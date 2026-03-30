from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
import re
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
import yaml

from app.models.category import Category
from app.models.file_asset import FileAsset
from app.models.role import Role
from app.models.skill import Skill
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_user_grant import SkillUserGrant
from app.models.skill_version import SkillVersion
from app.models.user import User
from app.models.version_review import VersionReview
from app.schemas.skill import UploadSkillResponse
from app.services.audit import write_audit_log
from app.services.cache import delete_cached_json
from app.core.config import get_settings
from app.services.storage import delete_object, save_bytes
from app.services.usage_guides import build_default_usage_guide

MAX_UPLOAD_SIZE = 50 * 1024 * 1024
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
REQUIRED_MANIFEST_KEYS = {"name", "slug", "version", "summary", "description", "category", "tags", "author"}


@dataclass(slots=True)
class ParsedSkillArchive:
    manifest: dict
    readme_markdown: str
    package_bytes: bytes


def _normalize_top_level_names(zip_file: ZipFile) -> dict[str, bytes]:
    """提取 ZIP 根目录文件并返回 `{文件名: 文件内容}` 映射。

    安全约束:
    - 禁止绝对路径与目录穿越（`..`）。
    - 仅接受 ZIP 根目录文件，忽略子目录文件。
    """
    collected: dict[str, bytes] = {}
    for info in zip_file.infolist():
        if info.is_dir():
            continue
        path = PurePosixPath(info.filename)
        if path.is_absolute() or ".." in path.parts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ZIP 包含非法路径")
        if len(path.parts) != 1:
            continue
        collected[path.name] = zip_file.read(info)
    return collected


def _parse_manifest(raw_manifest: bytes) -> dict:
    """解析并校验 `skill.yaml` 清单。

    校验内容:
    - UTF-8 编码与 YAML 语法合法。
    - 顶层结构必须为对象。
    - 必需字段齐全。
    - version 满足 semver。
    - tags 必须为数组。
    """
    try:
        manifest = yaml.safe_load(raw_manifest.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="skill.yaml 必须是 UTF-8 编码") from exc
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="skill.yaml 解析失败") from exc

    if not isinstance(manifest, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="skill.yaml 必须是对象结构")
    missing_keys = sorted(REQUIRED_MANIFEST_KEYS - set(manifest.keys()))
    if missing_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"skill.yaml 缺少字段: {', '.join(missing_keys)}",
        )
    if not SEMVER_RE.match(str(manifest["version"])):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="version 必须是合法 semver")
    if not isinstance(manifest["tags"], list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tags 必须是数组")
    return manifest


def parse_skill_archive(upload: UploadFile, package_bytes: bytes) -> ParsedSkillArchive:
    """解析上传 ZIP 技能包并提取 manifest + README。

    规则:
    - 仅支持 `.zip` 扩展名。
    - 大小不超过 50MB。
    - 根目录必须包含 `skill.yaml` 与 `README.md`。
    """
    if not upload.filename or not upload.filename.endswith(".zip"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 .zip 技能包")
    if len(package_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能包超过 50MB 限制")

    try:
        with ZipFile(BytesIO(package_bytes)) as zip_file:
            top_level_files = _normalize_top_level_names(zip_file)
    except BadZipFile as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ZIP 文件损坏或格式非法") from exc

    if "skill.yaml" not in top_level_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能包根目录缺少 skill.yaml")
    if "README.md" not in top_level_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能包根目录缺少 README.md")

    manifest = _parse_manifest(top_level_files["skill.yaml"])
    readme_markdown = top_level_files["README.md"].decode("utf-8")
    return ParsedSkillArchive(manifest=manifest, readme_markdown=readme_markdown, package_bytes=package_bytes)


def _get_or_create_asset(
    db: Session,
    *,
    content: bytes,
    subdir: str,
    original_name: str,
    mime_type: str,
    file_kind: str,
    created_by,
) -> tuple[FileAsset, str | None]:
    """基于内容哈希获取或创建文件资产。

    返回:
    - `(asset, created_object_key)`
      - 若命中去重资产，则 `created_object_key=None`。
      - 若新写入存储对象，则返回新 object_key（用于失败回滚时清理）。
    """
    stored = save_bytes(content, subdir=subdir, original_name=original_name, mime_type=mime_type)
    existing = db.execute(
        select(FileAsset).where(FileAsset.sha256 == stored.sha256_hex, FileAsset.file_kind == file_kind)
    ).scalar_one_or_none()
    if existing is not None:
        if existing.object_key != stored.object_key:
            delete_object(stored.object_key)
        return existing, None
    asset = FileAsset(
        bucket=stored.bucket,
        object_key=stored.object_key,
        original_name=stored.original_name,
        mime_type=stored.mime_type,
        size_bytes=stored.size_bytes,
        sha256=stored.sha256_hex,
        file_kind=file_kind,
        created_by=created_by,
    )
    db.add(asset)
    db.flush()
    return asset, stored.object_key


def upload_skill_package(db: Session, *, actor: User, upload: UploadFile, package_bytes: bytes) -> UploadSkillResponse:
    """上传技能包并创建技能版本（必要时创建新技能）。

    核心流程:
    1) 解析 ZIP 与 manifest。
    2) 校验分类与版本冲突。
    3) 以内容哈希去重写入 package/readme 资产。
    4) 新技能自动初始化 owner/maintainer 授权与 reviewer/publisher 角色授权。
    5) 创建 `submitted` 版本（直接进入待审核队列），写审核流水与审计日志并提交。

    失败回滚:
    - 事务回滚后，清理本次新增的存储对象，避免“库里失败但对象残留”。
    """
    parsed = parse_skill_archive(upload, package_bytes)
    category = db.execute(select(Category).where(Category.slug == parsed.manifest["category"])).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类 slug 不存在")

    existing_skill = db.execute(select(Skill).where(Skill.slug == parsed.manifest["slug"])).scalar_one_or_none()
    if existing_skill is not None:
        existing_version = db.execute(
            select(SkillVersion).where(
                SkillVersion.skill_id == existing_skill.id,
                SkillVersion.version == parsed.manifest["version"],
            )
        ).scalar_one_or_none()
        if existing_version is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该技能版本已存在")

    created_skill = False
    created_object_keys: list[str] = []
    storage_paths = get_settings()
    try:
        package_asset, package_object_key = _get_or_create_asset(
            db,
            content=parsed.package_bytes,
            subdir=storage_paths.skill_package_upload_subdir,
            original_name=upload.filename or "skill-package.zip",
            mime_type="application/zip",
            file_kind="package",
            created_by=actor.id,
        )
        if package_object_key is not None:
            created_object_keys.append(package_object_key)
        readme_asset, readme_object_key = _get_or_create_asset(
            db,
            content=parsed.readme_markdown.encode("utf-8"),
            subdir=storage_paths.skill_readme_subdir,
            original_name="README.md",
            mime_type="text/markdown",
            file_kind="readme",
            created_by=actor.id,
        )
        if readme_object_key is not None:
            created_object_keys.append(readme_object_key)

        skill = existing_skill
        if skill is None:
            skill = Skill(
                name=parsed.manifest["name"],
                slug=parsed.manifest["slug"],
                summary=parsed.manifest["summary"],
                description=parsed.manifest["description"],
                owner_user_id=actor.id,
                category_id=category.id,
                icon_file_id=None,
                status="active",
                current_published_version_id=None,
                latest_version_no=parsed.manifest["version"],
                view_count=0,
                download_count=0,
                favorite_count=0,
                like_count=0,
                published_at=None,
            )
            db.add(skill)
            db.flush()
            created_skill = True
            role_ids = {
                code: role_id
                for code, role_id in db.execute(
                    select(Role.code, Role.id).where(Role.code.in_(["reviewer", "publisher"]), Role.is_active.is_(True))
                ).all()
            }
            db.add_all(
                [
                    SkillUserGrant(skill_id=skill.id, user_id=actor.id, permission_scope="owner"),
                    SkillUserGrant(skill_id=skill.id, user_id=actor.id, permission_scope="maintainer"),
                ]
            )
            if "reviewer" in role_ids:
                db.add(SkillRoleGrant(skill_id=skill.id, role_id=role_ids["reviewer"], permission_scope="reviewer"))
            if "publisher" in role_ids:
                db.add(SkillRoleGrant(skill_id=skill.id, role_id=role_ids["publisher"], permission_scope="publisher"))
        else:
            existing_grant = db.execute(
                select(SkillUserGrant).where(
                    SkillUserGrant.skill_id == skill.id,
                    SkillUserGrant.user_id == actor.id,
                    SkillUserGrant.permission_scope == "maintainer",
                )
            ).scalar_one_or_none()
            if existing_grant is None:
                db.add(SkillUserGrant(skill_id=skill.id, user_id=actor.id, permission_scope="maintainer"))

        version = SkillVersion(
            skill_id=skill.id,
            version=str(parsed.manifest["version"]),
            manifest_json=parsed.manifest,
            usage_guide_json=build_default_usage_guide(
                skill_id=skill.id,
                skill_name=str(parsed.manifest["name"]),
                skill_slug=str(parsed.manifest["slug"]),
                summary=str(parsed.manifest["summary"]),
                description=str(parsed.manifest["description"]),
                install_notes="",
            ),
            changelog="",
            install_notes="",
            breaking_changes="",
            readme_markdown=parsed.readme_markdown,
            source_type="upload_zip",
            package_file_id=package_asset.id,
            readme_file_id=readme_asset.id,
            review_status="submitted",
            review_comment=None,
            reviewed_by=None,
            reviewed_at=None,
            published_by=None,
            published_at=None,
            created_by=actor.id,
        )
        db.add(version)
        db.flush()
        db.add(
            VersionReview(
                skill_version_id=version.id,
                action="submit",
                comment="上传后自动进入审核",
                operator_user_id=actor.id,
            )
        )

        write_audit_log(
            db,
            actor_user_id=actor.id,
            action="skill.upload",
            target_type="skill_version",
            target_id=version.id,
            after_json={"skill_id": str(skill.id), "version": version.version, "created_skill": created_skill},
        )
        db.commit()
    except Exception:
        db.rollback()
        for object_key in created_object_keys:
            delete_object(object_key)
        raise
    delete_cached_json("public:categories", f"public:skill-detail:{skill.slug}")
    return UploadSkillResponse(
        skill_id=skill.id,
        version_id=version.id,
        created_skill=created_skill,
        review_status="submitted",
        parsed_manifest=parsed.manifest,
    )
