"""Live PostgreSQL and MinIO integration tests for Phase 7 document ingestion."""

import asyncio
import json
import os
from datetime import UTC, datetime
from typing import AsyncIterator
from uuid import uuid4

import asyncpg
import boto3
import httpx
import pytest
import pytest_asyncio

from app.documents.authorization import (
    ConsentAuthorizationDenied,
    PostgresDocumentPurposeAuthorizer,
)
from app.documents.cleanup import PostgresAbandonedUploadCleaner
from app.documents.registry import DocumentRegistryEntry, DocumentState
from app.documents.repository import DocumentNotFound, PostgresDocumentRepository
from app.documents.scan_repository import PostgresDocumentScanRepository
from app.documents.scan_service import DocumentScanService
from app.documents.scanning import ClamAVScanner, MalwareScanOutcome
from app.documents.storage import S3DocumentStore
from app.migrations import apply_migrations

pytestmark = pytest.mark.skipif(
    os.getenv("PHASE7_INTEGRATION") != "1",
    reason="set PHASE7_INTEGRATION=1 when local PostgreSQL and MinIO are running",
)

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://notmid:notmid-local-only@localhost:5432/notmid",
)
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


@pytest.mark.asyncio
async def test_migration_runner_applies_once_in_an_isolated_schema() -> None:
    schema = f"phase7_runner_{uuid4().hex}"
    connection = await asyncpg.connect(DATABASE_URL)
    try:
        await connection.execute(f'CREATE SCHEMA "{schema}"')
        await connection.execute(f'SET search_path TO "{schema}"')

        first_count = await apply_migrations(connection)
        second_count = await apply_migrations(connection)
        tables = await connection.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = $1",
            schema,
        )

        assert first_count == 4
        assert second_count == 0
        assert {row["tablename"] for row in tables} == {
            "document_registry",
            "document_outbox",
            "consent_artifact",
            "document_scan_run",
            "schema_migration",
        }
    finally:
        await connection.execute("SET search_path TO public")
        await connection.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        await connection.close()


@pytest_asyncio.fixture
async def postgres_repository() -> AsyncIterator[
    tuple[PostgresDocumentRepository, str, asyncpg.Pool]
]:
    suffix = uuid4().hex
    schema = f"phase7_{suffix}"
    role = f"phase7_role_{suffix}"
    admin = await asyncpg.connect(DATABASE_URL)
    pool = None
    try:
        await admin.execute(f'CREATE SCHEMA "{schema}"')
        await admin.execute(f'SET search_path TO "{schema}"')
        await apply_migrations(admin)
        await admin.execute(f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOBYPASSRLS')
        await admin.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"')
        await admin.execute(f'GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA "{schema}" TO "{role}"')

        async def initialize(connection: asyncpg.Connection) -> None:
            await connection.execute(f'SET ROLE "{role}"')
            await connection.execute(f'SET search_path TO "{schema}"')

        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2, setup=initialize)
        assert pool is not None
        yield PostgresDocumentRepository(pool), schema, pool
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
    postgres_repository: tuple[PostgresDocumentRepository, str, asyncpg.Pool],
) -> None:
    repository, _schema, _pool = postgres_repository
    document = _document()

    created = await repository.create(document)
    replay = await repository.create(document.model_copy(update={"id": uuid4()}))

    assert created.created is True
    assert replay.created is False
    assert replay.document.id == document.id
    with pytest.raises(DocumentNotFound):
        await repository.get(uuid4(), document.id)


@pytest.mark.asyncio
async def test_postgres_consent_authorization_is_active_and_tenant_scoped() -> None:
    suffix = uuid4().hex
    schema = f"phase7_consent_{suffix}"
    role = f"phase7_consent_role_{suffix}"
    tenant_id = uuid4()
    patient_id = uuid4()
    encounter_id = uuid4()
    consent_id = uuid4()
    admin = await asyncpg.connect(DATABASE_URL)
    pool = None
    try:
        await admin.execute(f'CREATE SCHEMA "{schema}"')
        await admin.execute(f'SET search_path TO "{schema}"')
        await apply_migrations(admin)
        await admin.execute(
            """
            INSERT INTO consent_artifact (
                id, tenant_id, patient_id, encounter_id, purpose, scope, status
            ) VALUES ($1, $2, $3, $4, 'treatment', '{"document_upload": true}', 'granted')
            """,
            consent_id,
            tenant_id,
            patient_id,
            encounter_id,
        )
        await admin.execute(f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOBYPASSRLS')
        await admin.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"')
        await admin.execute(f'GRANT SELECT ON consent_artifact TO "{role}"')

        async def initialize(connection: asyncpg.Connection) -> None:
            await connection.execute(f'SET ROLE "{role}"')
            await connection.execute(f'SET search_path TO "{schema}"')

        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2, setup=initialize)
        authorizer = PostgresDocumentPurposeAuthorizer(pool)
        scope = {
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "purpose": "treatment",
            "consent_reference": str(consent_id),
        }

        await authorizer.authorize(**scope)
        with pytest.raises(ConsentAuthorizationDenied):
            await authorizer.authorize(**(scope | {"tenant_id": uuid4()}))
    finally:
        if pool is not None:
            await pool.close()
        await admin.execute("RESET ROLE")
        await admin.execute("SET search_path TO public")
        await admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        await admin.execute(f'DROP ROLE IF EXISTS "{role}"')
        await admin.close()


@pytest.mark.asyncio
async def test_abandoned_upload_cleanup_is_durable_and_emits_safe_event() -> None:
    schema = f"phase7_cleanup_{uuid4().hex}"
    document = _document()
    admin = await asyncpg.connect(DATABASE_URL)
    pool = None
    try:
        await admin.execute(f'CREATE SCHEMA "{schema}"')
        await admin.execute(f'SET search_path TO "{schema}"')
        await apply_migrations(admin)
        await admin.execute(
            """
            INSERT INTO document_registry (
                id, tenant_id, facility_id, patient_id, encounter_id,
                uploader_actor_id, purpose, consent_reference, original_filename,
                declared_mime, declared_size_bytes, idempotency_key,
                upload_expires_at, state, version, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                CURRENT_TIMESTAMP - INTERVAL '1 minute', 'initiated', 1,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """,
            document.id,
            document.tenant_id,
            document.facility_id,
            document.patient_id,
            document.encounter_id,
            document.uploader_actor_id,
            document.purpose,
            document.consent_reference,
            document.original_filename,
            document.declared_mime,
            document.declared_size_bytes,
            document.idempotency_key,
        )

        async def initialize(connection: asyncpg.Connection) -> None:
            await connection.execute(f'SET search_path TO "{schema}"')

        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2, setup=initialize)
        expired = await PostgresAbandonedUploadCleaner(pool).expire(
            now=datetime.now(UTC),
            limit=10,
        )

        assert [item.document_id for item in expired] == [document.id]
        row = await admin.fetchrow(
            "SELECT state, version FROM document_registry WHERE id = $1", document.id
        )
        event = await admin.fetchrow(
            "SELECT event_type, payload FROM document_outbox WHERE aggregate_id = $1",
            document.id,
        )
        assert row is not None and dict(row) == {"state": "cancelled", "version": 2}
        assert event is not None and event["event_type"] == "DocumentUploadExpired.v1"
        assert str(document.patient_id) not in str(dict(event))
    finally:
        if pool is not None:
            await pool.close()
        await admin.execute("SET search_path TO public")
        await admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        await admin.close()


@pytest.mark.asyncio
async def test_postgres_finalize_commits_quarantine_state_and_safe_outbox(
    postgres_repository: tuple[PostgresDocumentRepository, str, asyncpg.Pool],
) -> None:
    repository, schema, _pool = postgres_repository
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
        async with httpx.AsyncClient() as http:
            anonymous = await http.get(f"{endpoint}/{bucket}/{grant.object_key}")
        assert anonymous.status_code == 403
    finally:
        await asyncio.to_thread(
            client.delete_object,
            Bucket=bucket,
            Key=f"quarantine/{document.tenant_id}/{document.id}/source",
        )
        await asyncio.to_thread(client.delete_bucket, Bucket=bucket)


@pytest.mark.asyncio
async def test_clamav_detects_eicar_and_accepts_clean_synthetic_bytes() -> None:
    scanner = ClamAVScanner(
        host=os.getenv("TEST_CLAMAV_HOST", "127.0.0.1"),
        port=int(os.getenv("TEST_CLAMAV_PORT", "3310")),
        timeout_seconds=30,
    )
    eicar = (
        b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!"
        b"$H+H*"
    )

    clean = await scanner.scan(b"MediKiosk synthetic clean fixture")
    infected = await scanner.scan(eicar)

    assert clean.outcome is MalwareScanOutcome.CLEAN
    assert infected.outcome is MalwareScanOutcome.INFECTED
    assert infected.threat_name


@pytest.mark.asyncio
async def test_clean_document_scan_persists_run_and_promotes_private_source(
    postgres_repository: tuple[PostgresDocumentRepository, str, asyncpg.Pool],
) -> None:
    repository, schema, pool = postgres_repository
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
    bucket = f"phase7-scan-{uuid4().hex}"
    await asyncio.to_thread(client.create_bucket, Bucket=bucket)
    data = b"\xff\xd8\xffMediKiosk synthetic clean image"
    document = _document().model_copy(
        update={
            "declared_size_bytes": len(data),
            "idempotency_key": f"scan-{uuid4()}",
        }
    )
    store = S3DocumentStore(client=client, bucket=bucket, server_side_encryption="")
    try:
        await repository.create(document)
        grant = await store.create_upload_grant(document)
        async with httpx.AsyncClient() as http:
            upload = await http.put(grant.url, content=data, headers=grant.required_headers)
        assert upload.status_code == 200
        verified = await store.verify_upload(document, grant.object_key)
        quarantined = await repository.finalize_upload(
            tenant_id=document.tenant_id,
            document_id=document.id,
            expected_version=1,
            object_key=verified.object_key,
            checksum_sha256=verified.checksum_sha256,
            detected_mime=verified.detected_mime,
        )
        scanner = ClamAVScanner(
            host=os.getenv("TEST_CLAMAV_HOST", "127.0.0.1"),
            port=int(os.getenv("TEST_CLAMAV_PORT", "3310")),
            timeout_seconds=30,
        )
        await DocumentScanService(
            PostgresDocumentScanRepository(pool),
            store,
            scanner,
        ).process(
            tenant_id=document.tenant_id,
            document_id=document.id,
            expected_version=quarantined.version,
        )

        completed = await repository.get(document.tenant_id, document.id)
        assert completed.state is DocumentState.SCAN_PASSED
        assert completed.processing_object_key is not None
        head = await asyncio.to_thread(
            client.head_object,
            Bucket=bucket,
            Key=completed.processing_object_key,
        )
        assert head["ContentLength"] == len(data)
        admin = await asyncpg.connect(DATABASE_URL)
        try:
            scan = await admin.fetchrow(
                f'SELECT status, outcome, engine_version FROM "{schema}".document_scan_run'
            )
        finally:
            await admin.close()
        assert scan is not None
        assert dict(scan)["status"] == "completed"
        assert dict(scan)["outcome"] == "clean"
    finally:
        objects = await asyncio.to_thread(client.list_objects_v2, Bucket=bucket)
        for item in objects.get("Contents", []):
            await asyncio.to_thread(client.delete_object, Bucket=bucket, Key=item["Key"])
        await asyncio.to_thread(client.delete_bucket, Bucket=bucket)
