from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy.engine.url import make_url

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://xusheng@127.0.0.1:5432/skill_hub_test")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("POSTGRES_HOST", "127.0.0.1")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "skill_hub_test")
os.environ.setdefault("POSTGRES_USER", "xusheng")
os.environ.setdefault("POSTGRES_PASSWORD", "")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("S3_ENDPOINT", "http://127.0.0.1:9000")
os.environ.setdefault("S3_ACCESS_KEY", "local-dev")
os.environ.setdefault("S3_SECRET_KEY", "local-dev")
os.environ.setdefault("S3_BUCKET", "skill-hub")
os.environ.setdefault("S3_REGION", "us-east-1")
os.environ.setdefault("S3_SECURE", "false")
os.environ.setdefault("JWT_SECRET", "change-me")
os.environ.setdefault("JWT_ACCESS_EXPIRE_MINUTES", "30")
os.environ.setdefault("JWT_REFRESH_EXPIRE_DAYS", "7")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("LOG_FORMAT", "json")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("FILE_STORAGE_PATH", "./storage")
os.environ.setdefault("ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:4173,http://127.0.0.1:4174")
os.environ.setdefault("CORS_ORIGINS", "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:4173,http://127.0.0.1:4174")
BACKEND_DIR = Path(__file__).resolve().parents[1]


def ensure_database_exists(database_url: str) -> None:
    url = make_url(database_url)
    database_name = url.database
    admin_dsn = url.set(drivername="postgresql", database="postgres").render_as_string(hide_password=False)
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("select 1 from pg_database where datname = %s", (database_name,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("create database {}").format(sql.Identifier(database_name)))


ensure_database_exists(TEST_DATABASE_URL)


def upgrade_database() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(config, "head")


upgrade_database()

from app.main import app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.audit_log import AuditLog  # noqa: E402
from app.models.download_log import DownloadLog  # noqa: E402
from app.models.favorite import Favorite  # noqa: E402
from app.models.file_asset import FileAsset  # noqa: E402
from app.models.refresh_token import RefreshToken  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.role_permission import RolePermission  # noqa: E402
from app.models.skill import Skill  # noqa: E402
from app.models.skill_like import SkillLike  # noqa: E402
from app.models.skill_role_grant import SkillRoleGrant  # noqa: E402
from app.models.skill_tag import SkillTag  # noqa: E402
from app.models.skill_user_grant import SkillUserGrant  # noqa: E402
from app.models.skill_version import SkillVersion  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_role import UserRole  # noqa: E402
from app.models.version_review import VersionReview  # noqa: E402
from sqlalchemy import delete, select, update  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session():
    with SessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
def reset_database_state():
    with SessionLocal() as session:
        admin_user = session.execute(select(User).where(User.username == "admin")).scalar_one()
        non_system_role_ids = list(session.execute(select(Role.id).where(Role.is_system.is_(False))).scalars())
        session.execute(delete(VersionReview))
        session.execute(delete(DownloadLog))
        session.execute(delete(Favorite))
        session.execute(delete(SkillLike))
        session.execute(delete(SkillRoleGrant))
        session.execute(delete(SkillUserGrant))
        session.execute(delete(SkillTag))
        session.execute(update(Skill).values(current_published_version_id=None, published_at=None))
        session.execute(delete(Skill))
        session.execute(delete(SkillVersion))
        session.execute(delete(FileAsset))
        session.execute(delete(AuditLog))
        session.execute(delete(RefreshToken))
        session.execute(delete(UserRole).where(UserRole.user_id != admin_user.id))
        session.execute(delete(User).where(User.id != admin_user.id))
        if non_system_role_ids:
            session.execute(delete(RolePermission).where(RolePermission.role_id.in_(non_system_role_ids)))
            session.execute(delete(UserRole).where(UserRole.role_id.in_(non_system_role_ids)))
            session.execute(delete(Role).where(Role.id.in_(non_system_role_ids)))
        session.commit()
    yield
