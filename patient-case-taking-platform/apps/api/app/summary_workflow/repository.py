"""Repository boundary and in-memory reference implementation for Phase 8."""

from collections import defaultdict
from typing import Protocol
from uuid import UUID

from app.summary_workflow.contracts import SummaryAction, SummaryRecord


class SummaryNotFound(Exception):
    pass


class SummaryConflict(Exception):
    pass


class SummaryRepository(Protocol):
    async def create(
        self, *, record: SummaryRecord, action: SummaryAction, idempotency_key: str
    ) -> SummaryRecord: ...

    async def get(self, *, tenant_id: UUID, summary_id: UUID) -> SummaryRecord: ...

    async def list_for_encounter(
        self, *, tenant_id: UUID, encounter_id: UUID
    ) -> list[SummaryRecord]: ...

    async def replace(
        self, *, record: SummaryRecord, action: SummaryAction, expected_version: int
    ) -> SummaryRecord: ...

    async def history(
        self, *, tenant_id: UUID, summary_id: UUID
    ) -> list[SummaryAction]: ...

    async def find_idempotent(
        self, *, tenant_id: UUID, idempotency_key: str
    ) -> SummaryRecord | None: ...


class InMemorySummaryRepository:
    """Tenant-scoped repository used by domain and HTTP contract tests."""

    def __init__(self) -> None:
        self._records: dict[tuple[UUID, UUID], SummaryRecord] = {}
        self._actions: dict[tuple[UUID, UUID], list[SummaryAction]] = defaultdict(list)
        self._idempotency: dict[tuple[UUID, str], UUID] = {}

    async def create(
        self, *, record: SummaryRecord, action: SummaryAction, idempotency_key: str
    ) -> SummaryRecord:
        replay = await self.find_idempotent(
            tenant_id=record.tenant_id, idempotency_key=idempotency_key
        )
        if replay is not None:
            return replay
        key = (record.tenant_id, record.id)
        if key in self._records:
            raise SummaryConflict("Summary already exists")
        self._records[key] = record.model_copy(deep=True)
        self._actions[key].append(action.model_copy(deep=True))
        self._idempotency[(record.tenant_id, idempotency_key)] = record.id
        return record.model_copy(deep=True)

    async def get(self, *, tenant_id: UUID, summary_id: UUID) -> SummaryRecord:
        record = self._records.get((tenant_id, summary_id))
        if record is None:
            raise SummaryNotFound("Summary not found")
        return record.model_copy(deep=True)

    async def list_for_encounter(
        self, *, tenant_id: UUID, encounter_id: UUID
    ) -> list[SummaryRecord]:
        records = [
            record.model_copy(deep=True)
            for (record_tenant, _), record in self._records.items()
            if record_tenant == tenant_id and record.encounter_id == encounter_id
        ]
        return sorted(records, key=lambda item: (item.generation, item.created_at))

    async def replace(
        self, *, record: SummaryRecord, action: SummaryAction, expected_version: int
    ) -> SummaryRecord:
        key = (record.tenant_id, record.id)
        current = self._records.get(key)
        if current is None:
            raise SummaryNotFound("Summary not found")
        if current.lock_version != expected_version:
            raise SummaryConflict("Summary version is stale")
        self._records[key] = record.model_copy(deep=True)
        self._actions[key].append(action.model_copy(deep=True))
        return record.model_copy(deep=True)

    async def history(
        self, *, tenant_id: UUID, summary_id: UUID
    ) -> list[SummaryAction]:
        await self.get(tenant_id=tenant_id, summary_id=summary_id)
        return [item.model_copy(deep=True) for item in self._actions[(tenant_id, summary_id)]]

    async def find_idempotent(
        self, *, tenant_id: UUID, idempotency_key: str
    ) -> SummaryRecord | None:
        summary_id = self._idempotency.get((tenant_id, idempotency_key))
        if summary_id is None:
            return None
        return await self.get(tenant_id=tenant_id, summary_id=summary_id)

