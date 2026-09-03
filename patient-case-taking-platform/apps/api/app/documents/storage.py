"""Private quarantine storage adapter for source documents."""

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.documents.registry import DocumentRegistryEntry, DocumentState

_READ_CHUNK_BYTES = 64 * 1024


class ObjectVerificationError(ValueError):
    """Raised when a quarantined object does not match its registration."""


@dataclass(frozen=True)
class UploadGrant:
    url: str
    object_key: str
    expires_in_seconds: int
    required_headers: dict[str, str]


@dataclass(frozen=True)
class VerifiedUpload:
    object_key: str
    size_bytes: int
    checksum_sha256: str
    detected_mime: str


def detect_supported_mime(data: bytes) -> str:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ObjectVerificationError("Uploaded object type is unsupported or unreadable")


class S3DocumentStore:
    def __init__(
        self,
        *,
        client: Any | None = None,
        bucket: str | None = None,
        grant_ttl_seconds: int | None = None,
    ) -> None:
        self._provided_client = client
        self._bucket = bucket or settings.S3_BUCKET
        self._grant_ttl_seconds = (
            grant_ttl_seconds or settings.DOCUMENT_UPLOAD_GRANT_TTL_SECONDS
        )

    def _client(self) -> Any:
        if self._provided_client is not None:
            return self._provided_client
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )

    @staticmethod
    def object_key(document: DocumentRegistryEntry) -> str:
        return f"quarantine/{document.tenant_id}/{document.id}/source"

    async def create_upload_grant(self, document: DocumentRegistryEntry) -> UploadGrant:
        if document.state is not DocumentState.INITIATED:
            raise ObjectVerificationError("Only initiated documents can receive an upload grant")
        object_key = self.object_key(document)
        required_headers = {
            "Content-Type": document.declared_mime,
            "Content-Length": str(document.declared_size_bytes),
            "x-amz-server-side-encryption": "AES256",
            "x-amz-meta-document-id": str(document.id),
        }
        params = {
            "Bucket": self._bucket,
            "Key": object_key,
            "ContentType": document.declared_mime,
            "ContentLength": document.declared_size_bytes,
            "ServerSideEncryption": "AES256",
            "Metadata": {"document-id": str(document.id)},
        }
        url = await asyncio.to_thread(
            self._client().generate_presigned_url,
            "put_object",
            Params=params,
            ExpiresIn=self._grant_ttl_seconds,
            HttpMethod="PUT",
        )
        return UploadGrant(url, object_key, self._grant_ttl_seconds, required_headers)

    async def verify_upload(
        self, document: DocumentRegistryEntry, object_key: str
    ) -> VerifiedUpload:
        expected_key = self.object_key(document)
        if object_key != expected_key:
            raise ObjectVerificationError("Object is outside the registered quarantine scope")

        client = self._client()
        head = await asyncio.to_thread(
            client.head_object,
            Bucket=self._bucket,
            Key=object_key,
        )
        if head.get("ContentLength") != document.declared_size_bytes:
            raise ObjectVerificationError("Uploaded object size does not match registration")
        if head.get("ContentType") != document.declared_mime:
            raise ObjectVerificationError("Uploaded content type does not match registration")

        response = await asyncio.to_thread(
            client.get_object,
            Bucket=self._bucket,
            Key=object_key,
        )
        body = response["Body"]
        digest = hashlib.sha256()
        prefix = bytearray()
        total = 0
        try:
            for chunk in body.iter_chunks(chunk_size=_READ_CHUNK_BYTES):
                total += len(chunk)
                if total > document.declared_size_bytes:
                    raise ObjectVerificationError("Uploaded object exceeds registered size")
                if len(prefix) < 16:
                    prefix.extend(chunk[: 16 - len(prefix)])
                digest.update(chunk)
        finally:
            body.close()

        if total != document.declared_size_bytes:
            raise ObjectVerificationError("Uploaded object size changed during verification")
        detected_mime = detect_supported_mime(bytes(prefix))
        if detected_mime != document.declared_mime:
            raise ObjectVerificationError("Detected object type does not match registration")
        return VerifiedUpload(object_key, total, digest.hexdigest(), detected_mime)
