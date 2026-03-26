from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(ROOT_DIR / ".env.example")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Skill Hub API"
    api_prefix: str = "/api"
    app_env: Literal["development", "test", "production"] = Field(alias="APP_ENV", default="development")
    debug: bool = Field(alias="DEBUG", default=False)
    log_level: str = Field(alias="LOG_LEVEL", default="INFO")
    log_format: Literal["json"] = Field(alias="LOG_FORMAT", default="json")
    app_base_url: str = Field(alias="APP_BASE_URL", default="http://127.0.0.1:8000")
    database_url: str = Field(
        default="postgresql+psycopg://xusheng@127.0.0.1:5432/skill_hub",
        alias="DATABASE_URL",
    )
    test_database_url: str = Field(
        default="postgresql+psycopg://xusheng@127.0.0.1:5432/skill_hub_test",
        alias="TEST_DATABASE_URL",
    )
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_port: int = Field(alias="POSTGRES_PORT")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    redis_url: str = Field(alias="REDIS_URL")
    s3_endpoint: str = Field(alias="S3_ENDPOINT")
    s3_access_key: str = Field(alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(alias="S3_SECRET_KEY")
    s3_bucket: str = Field(alias="S3_BUCKET")
    s3_region: str = Field(alias="S3_REGION", default="us-east-1")
    s3_secure: bool = Field(alias="S3_SECURE", default=False)
    s3_presign_expire_seconds: int = Field(alias="S3_PRESIGN_EXPIRE_SECONDS", default=300)
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_access_expire_minutes: int = Field(alias="JWT_ACCESS_EXPIRE_MINUTES", default=30)
    jwt_refresh_expire_days: int = Field(alias="JWT_REFRESH_EXPIRE_DAYS", default=7)
    allowed_origins: str = Field(
        default="http://127.0.0.1:5173,http://127.0.0.1:5174",
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "CORS_ORIGINS"),
    )
    storage_backend: Literal["local", "s3"] = Field(alias="STORAGE_BACKEND", default="local")
    file_storage_path: str = Field(alias="FILE_STORAGE_PATH", default="./storage")
    request_id_header: str = Field(alias="REQUEST_ID_HEADER", default="X-Request-ID")
    login_rate_limit: str = Field(alias="LOGIN_RATE_LIMIT", default="10/minute")
    upload_rate_limit: str = Field(alias="UPLOAD_RATE_LIMIT", default="20/hour")
    download_rate_limit: str = Field(alias="DOWNLOAD_RATE_LIMIT", default="120/hour")
    categories_cache_ttl_seconds: int = Field(alias="CATEGORIES_CACHE_TTL_SECONDS", default=60)
    skill_detail_cache_ttl_seconds: int = Field(alias="SKILL_DETAIL_CACHE_TTL_SECONDS", default=60)

    @property
    def storage_dir(self) -> Path:
        path = Path(self.file_storage_path)
        return path if path.is_absolute() else BACKEND_DIR / path

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        if self.is_production:
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if self.jwt_secret == "change-me":
                raise ValueError("JWT_SECRET must not use the default value in production")
            if not self.cors_origin_list:
                raise ValueError("ALLOWED_ORIGINS must not be empty in production")
            if self.storage_backend != "s3":
                raise ValueError("STORAGE_BACKEND must be 's3' in production")
        return self


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.database_url.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must point to a PostgreSQL database")
    if settings.storage_backend == "local":
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
