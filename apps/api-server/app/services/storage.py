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
    """将对象键映射为本地存储路径。"""
    settings = get_settings()
    return settings.storage_dir / object_key


def _build_s3_client() -> BaseClient:
    """按当前配置构建 S3 客户端实例。"""
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
    """保存二进制内容到存储后端并返回元信息。

    行为:
    - object_key 使用 `subdir/uuid-原文件名` 形式，降低重名冲突风险。
    - 根据 `storage_backend` 路由到 S3 或本地文件系统。
    """
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
    """保存文本内容（UTF-8 编码）到存储后端。"""
    return save_bytes(content.encode("utf-8"), subdir=subdir, original_name=original_name, mime_type=mime_type)


def ensure_bytes(object_key: str, content: bytes) -> None:
    """确保指定 object_key 对应对象存在，不存在则写入。

    说明:
    - 适用于“幂等写入”场景，已存在时不重复覆盖。
    """
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
    """获取本地存储对象路径。

    异常:
    - 非本地存储后端时抛出 FileNotFoundError。
    - 本地对象不存在时抛出 FileNotFoundError。
    """
    settings = get_settings()
    if settings.storage_backend != "local":
        raise FileNotFoundError("local file path is not available for s3 storage")
    object_path = _resolve_object_path(object_key)
    if not object_path.exists():
        raise FileNotFoundError(object_key)
    return object_path


def delete_object(object_key: str) -> None:
    """删除存储对象。

    说明:
    - S3 删除失败时吞掉异常，保持清理过程尽量不影响主流程。
    - 本地后端仅在文件存在时执行删除。
    """
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
    """构建下载响应。

    返回:
    - S3 后端：302 跳转到预签名下载链接。
    - 本地后端：直接返回文件流响应。
    """
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
    """执行存储后端健康检查。

    返回:
    - `(True, "ok")`: 检查通过。
    - `(False, detail)`: 检查失败并附带错误详情。
    """
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
