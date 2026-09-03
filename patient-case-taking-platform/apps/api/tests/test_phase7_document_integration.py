"""Live PostgreSQL and MinIO integration tests for Phase 7 document ingestion."""

import asyncio
import json
import os
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import asyncpg
import boto3
import httpx
import pytest
import pytest_asyncio

from app.documents.registry import DocumentRegistryEntry, DocumentState
from app.documents.repository import DocumentNotFound, PostgresDocumentRepository
from app.documents.storage import S3DocumentStore

pytestmark = pytest.mark.skipif(
    os.getenv("PHASE7_INTEGRATION") != "1",
    reason="set PHASE7_INTEGRATION=1 when local PostgreSQL and MinIO are running",
)

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://notmid:notmid-local-only@localhost:5432/notmid",
)
MIGRATION = Path(__file__).parents[1] / "migrations" / "0001_phase7_documents.up.sql"


def _document() -> DocumentRegistryEntry:
    return DocumentRegistryEntry(
        tenant_id=uuid4(),
        facility_id=uuid4(),
        patient_id=uuid4(),
        encounter_id=uuid4(),
        uploader_actor_id=uuid4(),
        purpose="treatment",
        consent_reference="consent/synthetic-version-1",
        original_filename="synthetic-prescription.jpg",
        declared_mime="image/jpeg",
        declared_size_bytes=16,
        idempotency_key="integration-upload-1",
    )


@pytest_asyncio.fixture
async def postgres_repository() -> AsyncIterator[tuple[PostgresDocumentRepository, str]]:
    suffix = uuid4().hex
    schema = f"phase7_{suffix}"
    role = f"phase7_role_{suffix}"
    admin = await asyncpg.connect(DATABASE_URL)
    pool = None
    try:
        await admin.execute(f'CREATE SCHEMA "{schema}"')
        await admin.execute(f'SET search_path TO "{schema}"')
        await admin.execute(MIGRATION.read_text(encoding="utf-8"))
        await admin.execute(f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOBYPASSRLS')
        await admin.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"')
        await admin.execute(f'GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA "{schema}" TO "{role}"')

        async def initialize(connection: asyncpg.Connection) -> None:
            await connection.execute(f'SET ROLE "{role}"')
            await connection.execute(f'SET search_path TO "{schema}"')

        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2, setup=initialize)
        assert pool is not None
        yield PostgresDocumentRepository(pool), schema
    finally:
        if pool is not None:
            await pool.close()
        await admin.execute("RESET ROLE")
        await admin.execute("SET search_path TO public")
        await admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        await admin.execute(f'DROP ROLE IF EXISTS "{role}"')
        await admin.close()


@pytest.mark.asyncio
async def test_postgres_repository_enforces_rls_and_idempotent_registration(
    postgres_repository: tuple[PostgresDocumentRepository, str],
) -> None:
    repository, _schema = postgres_repository
    document = _document()

    created = await repository.create(document)
    replay = await repository.create(document.model_copy(update={"id": uuid4()}))

    assert created.created is True
    assert replay.created is False
    assert replay.document.id == document.id
    with pytest.raises(DocumentNotFound):
        await repository.get(uuid4(), document.id)


@pytest.mark.asyncio
async def test_postgres_finalize_commits_quarantine_state_and_safe_outbox(
    postgres_repository: tuple[PostgresDocumentRepository, str],
) -> None:
    repository, schema = postgres_repository
    document = _document()
    await repository.create(document)
    object_key = f"quarantine/{document.tenant_id}/{document.id}/source"

    finalized = await repository.finalize_upload(
        tenant_id=document.tenant_id,
        document_id=document.id,
        expected_version=1,
        object_key=object_key,
        checksum_sha256="a" * 64,
        detected_mime="image/jpeg",
    )

    assert finalized.state is DocumentState.QUARANTINED
    assert finalized.version == 3
    admin = await asyncpg.connect(DATABASE_URL)
    try:
        row = await admin.fetchrow(f'SELECT * FROM "{schema}".document_outbox')
    finally:
        await admin.close()
    assert row is not None
    assert row["event_type"] == "DocumentUploaded.v1"
    serialized = json.dumps(dict(row), default=str)
    assert document.original_filename not in serialized
    assert str(document.patient_id) not in serialized


@pytest.mark.asyncio
async def test_minio_presigned_upload_is_verified_from_stored_bytes() -> None:
    endpoint = os.getenv("TEST_S3_ENDPOINT", "http://127.0.0.1:9000")
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.getenv("TEST_S3_ACCESS_KEY", "notmid-local"),
        aws_secret_access_key=os.getenv(
            "TEST_S3_SECRET_KEY", "notmid-local-only-change-me"
        ),
        region_name="us-east-1",
    )
    bucket = f"phase7-{uuid4().hex}"
    await asyncio.to_thread(client.create_bucket, Bucket=bucket)
    data = b"\xff\xd8\xffsynthetic-jpeg"
    document = _document().model_copy(update={"declared_size_bytes": len(data)})
    store = S3DocumentStore(client=client, bucket=bucket, server_side_encryption="")
    try:
        grant = await store.create_upload_grant(document)
        async with httpx.AsyncClient() as http:
            response = await http.put(grant.url, content=data, headers=grant.required_headers)
        assert response.status_code == 200, response.text

        verified = await store.verify_upload(document, grant.object_key)
        assert verified.detected_mime == "image/jpeg"
        assert verified.size_bytes == len(data)
    finally:
        await asyncio.to_thread(
            client.delete_object,
            Bucket=bucket,
            Key=f"quarantine/{document.tenant_id}/{document.id}/source",
        )
        await asyncio.to_thread(client.delete_bucket, Bucket=bucket)
