"""Private quarantine object-store contract tests."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.documents.registry import DocumentRegistryEntry
from app.documents.storage import ObjectVerificationError, S3DocumentStore


class _Body:
    def __init__(self, data: bytes):
        self.data = data
        self.closed = False

    def iter_chunks(self, chunk_size: int):
        for offset in range(0, len(self.data), chunk_size):
            yield self.data[offset : offset + chunk_size]

    def close(self) -> None:
        self.closed = True


class _Client:
    def __init__(self, data: bytes, content_type: str):
        self.data = data
        self.content_type = content_type
        self.presign_params: dict[str, Any] | None = None
        self.body = _Body(data)

    def generate_presigned_url(self, operation: str, **kwargs: Any) -> str:
        self.presign_params = {"operation": operation, **kwargs}
        return "https://object-store.invalid/signed-upload"

    def head_object(self, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        return {"ContentLength": len(self.data), "ContentType": self.content_type}

    def get_object(self, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        return {"Body": self.body}


def _document(*, size: int, mime: str = "image/jpeg") -> DocumentRegistryEntry:
    from uuid import uuid4

    return DocumentRegistryEntry(
        tenant_id=uuid4(),
        facility_id=uuid4(),
        patient_id=uuid4(),
        encounter_id=uuid4(),
        uploader_actor_id=uuid4(),
        purpose="treatment",
        consent_reference="consent/test-version-1",
        original_filename="prescription.jpg",
        declared_mime=mime,
        declared_size_bytes=size,
        idempotency_key="upload-attempt-1",
    )


@pytest.mark.asyncio
async def test_upload_grant_is_scoped_to_one_quarantine_object() -> None:
    data = b"\xff\xd8\xff" + b"safe-image"
    document = _document(size=len(data))
    client = _Client(data, "image/jpeg")
    presign_client = _Client(data, "image/jpeg")
    store = S3DocumentStore(
        client=client,
        presign_client=presign_client,
        bucket="clinical-private",
        grant_ttl_seconds=300,
        server_side_encryption="AES256",
    )

    grant = await store.create_upload_grant(document)

    expected_key = f"quarantine/{document.tenant_id}/{document.id}/source"
    assert grant.object_key == expected_key
    assert grant.expires_in_seconds == 300
    assert grant.required_headers["Content-Type"] == "image/jpeg"
    assert client.presign_params is None
    assert presign_client.presign_params is not None
    assert presign_client.presign_params["Params"]["Key"] == expected_key
    assert presign_client.presign_params["Params"]["ContentLength"] == len(data)
    assert grant.required_headers["x-amz-server-side-encryption"] == "AES256"


@pytest.mark.asyncio
async def test_upload_grant_requires_encryption_outside_development(monkeypatch) -> None:
    data = b"\xff\xd8\xff" + b"safe-image"
    document = _document(size=len(data))
    store = S3DocumentStore(
        client=_Client(data, "image/jpeg"),
        bucket="clinical-private",
        server_side_encryption="",
    )
    monkeypatch.setattr("app.documents.storage.settings.APP_ENV", "production")

    with pytest.raises(ObjectVerificationError, match="encryption"):
        await store.create_upload_grant(document)


@pytest.mark.asyncio
async def test_upload_grant_is_denied_after_session_expiry() -> None:
    data = b"\xff\xd8\xff" + b"safe-image"
    document = _document(size=len(data)).model_copy(
        update={"upload_expires_at": datetime.now(UTC) - timedelta(seconds=1)}
    )
    store = S3DocumentStore(
        client=_Client(data, "image/jpeg"),
        bucket="clinical-private",
    )

    with pytest.raises(ObjectVerificationError, match="expired"):
        await store.create_upload_grant(document)


@pytest.mark.asyncio
async def test_verify_upload_hashes_bytes_and_detects_mime_from_magic_bytes() -> None:
    data = b"\xff\xd8\xff" + b"safe-image"
    document = _document(size=len(data))
    client = _Client(data, "image/jpeg")
    store = S3DocumentStore(client=client, bucket="clinical-private")
    object_key = f"quarantine/{document.tenant_id}/{document.id}/source"

    verified = await store.verify_upload(document, object_key)

    assert verified.size_bytes == len(data)
    assert verified.detected_mime == "image/jpeg"
    assert verified.checksum_sha256 == hashlib.sha256(data).hexdigest()
    assert client.body.closed is True


@pytest.mark.asyncio
async def test_verify_upload_rejects_declared_mime_spoofing() -> None:
    data = b"%PDF-1.7\nsynthetic"
    document = _document(size=len(data), mime="image/jpeg")
    store = S3DocumentStore(client=_Client(data, "image/jpeg"), bucket="clinical-private")
    object_key = f"quarantine/{document.tenant_id}/{document.id}/source"

    with pytest.raises(ObjectVerificationError, match="type"):
        await store.verify_upload(document, object_key)


@pytest.mark.asyncio
async def test_verify_upload_rejects_size_mismatch_before_reading() -> None:
    data = b"\xff\xd8\xff" + b"safe-image"
    document = _document(size=len(data) + 1)
    client = _Client(data, "image/jpeg")
    store = S3DocumentStore(client=client, bucket="clinical-private")
    object_key = f"quarantine/{document.tenant_id}/{document.id}/source"

    with pytest.raises(ObjectVerificationError, match="size"):
        await store.verify_upload(document, object_key)

    assert client.body.closed is False
