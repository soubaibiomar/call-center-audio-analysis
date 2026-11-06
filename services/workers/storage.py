"""Private S3 objects; callers must supply a verified tenant and persisted job ID."""

import base64
import hashlib
from typing import TYPE_CHECKING
from uuid import UUID

import boto3
from botocore.config import Config

from services.workers.settings import QueueSettings

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client


class IntegrityError(RuntimeError):
    pass


class AudioStore:
    def __init__(self, settings: QueueSettings) -> None:
        self.bucket = settings.bucket
        self.client: S3Client = boto3.client(
            "s3",
            endpoint_url=settings.endpoint_url,
            aws_access_key_id=settings.access_key,
            aws_secret_access_key=settings.secret_key,
            region_name=settings.region,
            config=Config(
                signature_version="s3v4",
                connect_timeout=3,
                read_timeout=30,
                retries={"max_attempts": 2},
                s3={"addressing_style": "path"},
            ),
        )

    @staticmethod
    def key(tenant: str, job: str) -> str:
        return f"tenants/{UUID(tenant)}/jobs/{UUID(job)}/audio"

    def put(self, tenant: str, job: str, data: bytes) -> str:
        digest = hashlib.sha256(data).hexdigest()
        self.client.put_object(
            Bucket=self.bucket,
            Key=self.key(tenant, job),
            Body=data,
            ContentType="application/octet-stream",
            ContentMD5=base64.b64encode(hashlib.md5(data, usedforsecurity=False).digest()).decode(),
            Metadata={"sha256": digest},
        )
        head = self.client.head_object(Bucket=self.bucket, Key=self.key(tenant, job))
        if head["ContentLength"] != len(data) or head.get("Metadata", {}).get("sha256") != digest:
            raise IntegrityError("Object verification failed")
        return digest

    def get(self, tenant: str, job: str, digest: str, size: int) -> bytes:
        if not 0 < size <= 50 * 1024 * 1024:
            raise IntegrityError("Invalid stored audio size")
        response = self.client.get_object(Bucket=self.bucket, Key=self.key(tenant, job))
        body = response["Body"]
        try:
            data = body.read(size + 1)
        finally:
            body.close()
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise IntegrityError("Audio checksum mismatch")
        return data
