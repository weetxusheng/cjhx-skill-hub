"""SQLAlchemy ORM 模型聚合导出，供迁移与仓储层统一引用。"""

from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.department import Department
from app.models.download_log import DownloadLog
from app.models.file_asset import FileAsset
from app.models.favorite import Favorite
from app.models.permission import Permission
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.skill import Skill
from app.models.skill_like import SkillLike
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_tag import SkillTag
from app.models.skill_user_grant import SkillUserGrant
from app.models.skill_version import SkillVersion
from app.models.tag import Tag
from app.models.user import User
from app.models.user_role import UserRole
from app.models.version_review import VersionReview

__all__ = [
    "AuditLog",
    "Category",
    "Department",
    "DownloadLog",
    "FileAsset",
    "Favorite",
    "Permission",
    "RefreshToken",
    "Role",
    "RolePermission",
    "Skill",
    "SkillLike",
    "SkillRoleGrant",
    "SkillTag",
    "SkillUserGrant",
    "SkillVersion",
    "Tag",
    "User",
    "UserRole",
    "VersionReview",
]
