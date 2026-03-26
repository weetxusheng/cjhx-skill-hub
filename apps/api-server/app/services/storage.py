from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import tempfile
from uuid import uuid4

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from fastapi.responses import FileResponse, RedirectResponse

from app.core.config import get_settings


@dataclass(slots=True)
class StoredFile:
    bucket: str
    object_key: str
    original_name: str
    mime_type: str
    size_bytes: int
    sha256_hex: str


def _resolve_object_path(object_key: str) -> Path:
    settings = get_settings()
    return settings.storage_dir / object_key


def _build_s3_client() -> BaseClient:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        use_ssl=settings.s3_secure,
    )


def save_bytes(content: bytes, *, subdir: str, original_name: str, mime_type: str) -> StoredFile:
    safe_name = original_name.replace("/", "-")
    object_key = f"{subdir}/{uuid4()}-{safe_name}"
    settings = get_settings()
    if settings.storage_backend == "s3":
        client = _build_s3_client()
        client.put_object(Bucket=settings.s3_bucket, Key=object_key, Body=content, ContentType=mime_type)
        bucket = settings.s3_bucket
    else:
        object_path = _resolve_object_path(object_key)
        object_path.parent.mkdir(parents=True, exist_ok=True)
        object_path.write_bytes(content)
        bucket = "local"
    return StoredFile(
        bucket=bucket,
        object_key=object_key,
        original_name=original_name,
        mime_type=mime_type,
        size_bytes=len(content),
        sha256_hex=sha256(content).hexdigest(),
    )


def save_text(content: str, *, subdir: str, original_name: str, mime_type: str = "text/markdown") -> StoredFile:
    return save_bytes(content.encode("utf-8"), subdir=subdir, original_name=original_name, mime_type=mime_type)


def ensure_bytes(object_key: str, content: bytes) -> None:
    settings = get_settings()
    if settings.storage_backend == "s3":
        client = _build_s3_client()
        try:
            client.head_object(Bucket=settings.s3_bucket, Key=object_key)
            return
        except ClientError:
            client.put_object(Bucket=settings.s3_bucket, Key=object_key, Body=content)
            return
    object_path = _resolve_object_path(object_key)
    if object_path.exists():
        return
    object_path.parent.mkdir(parents=True, exist_ok=True)
    object_path.write_bytes(content)


def get_object_path(object_key: str) -> Path:
    settings = get_settings()
    if settings.storage_backend != "local":
        raise FileNotFoundError("local file path is not available for s3 storage")
    object_path = _resolve_object_path(object_key)
    if not object_path.exists():
        raise FileNotFoundError(object_key)
    return object_path


def delete_object(object_key: str) -> None:
    settings = get_settings()
    if settings.storage_backend == "s3":
        client = _build_s3_client()
        try:
            client.delete_object(Bucket=settings.s3_bucket, Key=object_key)
        except (ClientError, BotoCoreError):
            return
        return
    object_path = _resolve_object_path(object_key)
    if object_path.exists():
        object_path.unlink()


def build_download_response(*, object_key: str, original_name: str, mime_type: str):
    settings = get_settings()
    if settings.storage_backend == "s3":
        client = _build_s3_client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": object_key, "ResponseContentDisposition": f'attachment; filename="{original_name}"'},
            ExpiresIn=settings.s3_presign_expire_seconds,
        )
        return RedirectResponse(url=url, status_code=302)
    path = get_object_path(object_key)
    return FileResponse(path, media_type=mime_type, filename=original_name)


def storage_ready_check() -> tuple[bool, str]:
    settings = get_settings()
    if settings.storage_backend == "s3":
        client = _build_s3_client()
        probe_key = f".health/{uuid4()}"
        try:
            client.head_bucket(Bucket=settings.s3_bucket)
            client.put_object(Bucket=settings.s3_bucket, Key=probe_key, Body=b"ok", ContentType="text/plain")
            client.delete_object(Bucket=settings.s3_bucket, Key=probe_key)
            return True, "ok"
        except (ClientError, BotoCoreError) as exc:
            return False, str(exc)

    try:
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=settings.storage_dir, delete=True) as handle:
            handle.write(b"ok")
            handle.flush()
        return True, "ok"
    except OSError as exc:
        return False, str(exc)
