"""聚合业务 API 子路由：认证、公共、后台管理（前缀在挂载时指定）。"""

from fastapi import APIRouter

from app.api.routes.admin_audit_logs import router as admin_audit_logs_router
from app.api.routes.admin_categories import router as admin_categories_router
from app.api.routes.admin_reviews import router as admin_reviews_router
from app.api.routes.admin_releases import router as admin_releases_router
from app.api.routes.admin_roles import router as admin_roles_router
from app.api.routes.admin_skills import router as admin_skills_router
from app.api.routes.admin_users import router as admin_users_router
from app.api.routes.admin_versions import router as admin_versions_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.public_categories import router as public_categories_router
from app.api.routes.public_skills import router as public_skills_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(public_categories_router, prefix="/public", tags=["public"])
api_router.include_router(public_skills_router, prefix="/public", tags=["public"])
api_router.include_router(admin_categories_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_skills_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_versions_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_reviews_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_releases_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_users_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_audit_logs_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_roles_router, prefix="/admin", tags=["admin"])
