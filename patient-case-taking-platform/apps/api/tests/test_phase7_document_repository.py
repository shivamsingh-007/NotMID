"""Phase 7 PostgreSQL document repository behavior."""

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any
from uuid import uuid4

import pytest

from app.documents.registry import DocumentRegistryEntry
from app.documents.repository import IdempotencyConflict, PostgresDocumentRepository


class _AsyncContext(AbstractAsyncContextManager):
    def __init__(self, value: Any):
        self.value = value

    async def __aenter__(self) -> Any:
        return self.value

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class _Connection:
    def __init__(self, rows: list[dict[str, Any] | None]):
        self.rows = rows
        self.tenant_context: str | None = None

    def transaction(self) -> _AsyncContext:
        return _AsyncContext(self)

    async def execute(self, query: str, tenant_id: str) -> None:
        assert "set_config('app.tenant_id'" in query
        self.tenant_context = tenant_id

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        del query, args
        return self.rows.pop(0)


class _Pool:
    def __init__(self, connection: _Connection):
        self.connection = connection

    def acquire(self) -> _AsyncContext:
        return _AsyncContext(self.connection)


def _document() -> DocumentRegistryEntry:
    return DocumentRegistryEntry(
        tenant_id=uuid4(),
        facility_id=uuid4(),
        patient_id=uuid4(),
        encounter_id=uuid4(),
        uploader_actor_id=uuid4(),
        purpose="treatment",
        consent_reference="consent/test-version-1",
        original_filename="prescription.jpg",
        declared_mime="image/jpeg",
        declared_size_bytes=1024,
        idempotency_key="upload-attempt-1",
    )


@pytest.mark.asyncio
async def test_create_sets_transaction_local_tenant_context() -> None:
    document = _document()
    connection = _Connection([document.model_dump()])
    repository = PostgresDocumentRepository(_Pool(connection))

    result = await repository.create(document)

    assert result.created is True
    assert result.document == document
    assert connection.tenant_context == str(document.tenant_id)


@pytest.mark.asyncio
async def test_create_replays_an_identical_idempotent_registration() -> None:
    document = _document()
    connection = _Connection([None, document.model_dump()])
    repository = PostgresDocumentRepository(_Pool(connection))

    result = await repository.create(document)

    assert result.created is False
    assert result.document == document


@pytest.mark.asyncio
async def test_create_rejects_conflicting_idempotency_key_reuse() -> None:
    document = _document()
    existing = document.model_copy(update={"original_filename": "different.jpg"})
    connection = _Connection([None, existing.model_dump()])
    repository = PostgresDocumentRepository(_Pool(connection))

    with pytest.raises(IdempotencyConflict):
        await repository.create(document)
