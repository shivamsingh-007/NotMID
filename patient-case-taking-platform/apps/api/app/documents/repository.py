"""PostgreSQL persistence for the Phase 7 document registry."""

from dataclasses import dataclass
from typing import Any, Protocol

from app.documents.registry import DocumentRegistryEntry

_INSERT_DOCUMENT = """
INSERT INTO document_registry (
    id, tenant_id, facility_id, patient_id, encounter_id, uploader_actor_id,
    purpose, consent_reference, original_filename, declared_mime,
    declared_size_bytes, idempotency_key, state, version, created_at, updated_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
)
ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
RETURNING *
"""

_GET_BY_IDEMPOTENCY_KEY = """
SELECT * FROM document_registry
WHERE tenant_id = $1 AND idempotency_key = $2
"""

_INITIATION_FIELDS = (
    "tenant_id",
    "facility_id",
    "patient_id",
    "encounter_id",
    "uploader_actor_id",
    "purpose",
    "consent_reference",
    "original_filename",
    "declared_mime",
    "declared_size_bytes",
    "idempotency_key",
)


class IdempotencyConflict(ValueError):
    """Raised when a key is reused for a different document registration."""


@dataclass(frozen=True)
class DocumentCreateResult:
    document: DocumentRegistryEntry
    created: bool


class DocumentRepository(Protocol):
    async def create(self, document: DocumentRegistryEntry) -> DocumentCreateResult: ...


class PostgresDocumentRepository:
    """Tenant-scoped registry repository backed by an asyncpg-compatible pool."""

    def __init__(self, pool: Any):
        self._pool = pool

    @staticmethod
    async def _set_tenant_context(connection: Any, document: DocumentRegistryEntry) -> None:
        await connection.execute(
            "SELECT set_config('app.tenant_id', $1, true)", str(document.tenant_id)
        )

    async def create(self, document: DocumentRegistryEntry) -> DocumentCreateResult:
        async with self._pool.acquire() as connection:
            async with connection.transaction():
                await self._set_tenant_context(connection, document)
                row = await connection.fetchrow(
                    _INSERT_DOCUMENT,
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
                    document.state.value,
                    document.version,
                    document.created_at,
                    document.updated_at,
                )
                if row is not None:
                    return DocumentCreateResult(
                        document=DocumentRegistryEntry.model_validate(dict(row)),
                        created=True,
                    )

                existing_row = await connection.fetchrow(
                    _GET_BY_IDEMPOTENCY_KEY,
                    document.tenant_id,
                    document.idempotency_key,
                )
                if existing_row is None:
                    raise RuntimeError("Document idempotency conflict could not be resolved")

                existing = DocumentRegistryEntry.model_validate(dict(existing_row))
                if any(
                    getattr(existing, field) != getattr(document, field)
                    for field in _INITIATION_FIELDS
                ):
                    raise IdempotencyConflict(
                        "Idempotency key is already used by a different document registration"
                    )
                return DocumentCreateResult(document=existing, created=False)
