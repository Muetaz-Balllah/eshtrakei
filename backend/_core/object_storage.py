import logging
from functools import lru_cache
from pathlib import Path

from backend.config import get_settings
from backend.errors import AppError

logger = logging.getLogger(__name__)


def object_storage_enabled() -> bool:
    settings = get_settings()
    return bool(settings.storage_endpoint_url and settings.storage_access_key_id and settings.storage_secret_access_key)


@lru_cache
def _client():
    import boto3
    from botocore.config import Config

    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.storage_region or "eu-central-1",
        endpoint_url=settings.storage_endpoint_url,
        aws_access_key_id=settings.storage_access_key_id,
        aws_secret_access_key=settings.storage_secret_access_key,
        config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
    )


def put_object(key: str, content: bytes, content_type: str) -> None:
    settings = get_settings()
    try:
        _client().put_object(Bucket=settings.storage_bucket, Key=key, Body=content, ContentType=content_type)
    except Exception as exc:
        logger.exception("object upload failed for %s", key)
        raise AppError(503, "storage_unavailable", "تعذر حفظ الملف") from exc


def get_object(key: str) -> bytes | None:
    from botocore.exceptions import ClientError

    settings = get_settings()
    try:
        response = _client().get_object(Bucket=settings.storage_bucket, Key=key)
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = exc.response.get("Error", {}).get("Code", "")
        if status == 404 or code in {"NoSuchKey", "404", "NotFound"}:
            return None
        logger.exception("object read failed for %s", key)
        raise AppError(503, "storage_unavailable", "تعذر قراءة الملف") from exc
    return response["Body"].read()


def read_bytes(stored: str) -> bytes | None:
    path = Path(stored)
    if path.is_file():
        return path.read_bytes()
    if object_storage_enabled():
        return get_object(stored)
    return None
