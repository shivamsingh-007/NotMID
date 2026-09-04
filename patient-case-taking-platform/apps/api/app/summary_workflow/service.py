"""Clinical summary lifecycle rules with mock-only generation."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.llm.schemas import ClinicalSummaryRequest, ClinicalSummaryResponse
from app.llm.service import LLMRouter
from app.summary_workflow.contracts import (
    SummaryAction,
    SummaryContent,
    SummaryRecord,
    SummarySourceBundle,
    SummaryStatus,
)
from app.summary_workflow.repository import SummaryRepository


class SummaryTransitionError(Exception):
    pass


class SummaryPermissionError(Exception):
    pass


class SummaryWorkflowService:
    def __init__(self, repository: SummaryRepository, llm_router: LLMRouter) -> None:
        self.repository = repository
        self.llm_router = llm_router

    async def generate(
        self,
        *,
        source: SummarySourceBundle,
        actor_id: UUID,
        actor_role: str,
        idempotency_key: str,
        parent: SummaryRecord | None = None,
    ) -> SummaryRecord:
        self._require_role(actor_role, {"doctor", "nurse"})
        replay = await self.repository.find_idempotent(
            tenant_id=source.tenant_id, idempotency_key=idempotency_key
        )
        if replay is not None:
            return replay

        generated = await self.llm_router.generate_summary(
            ClinicalSummaryRequest(
                tenant_id=source.tenant_id,
                encounter_id=source.encounter_id,
                language=source.language,
                chief_complaint=source.chief_complaint,
                confirmed_answers=source.confirmed_answers,
                transcript="",
                document_facts=source.reviewed_document_facts,
            )
        )
        generated = self._preserve_red_flags(generated, source.deterministic_red_flags)
        now = datetime.now(UTC)
        record = SummaryRecord(
            id=uuid4(),
            tenant_id=source.tenant_id,
            facility_id=source.facility_id,
            patient_id=source.patient_id,
            encounter_id=source.encounter_id,
            lineage_id=parent.lineage_id if parent else uuid4(),
            generation=parent.generation + 1 if parent else 1,
            parent_summary_id=parent.id if parent else None,
            status=SummaryStatus.DRAFT,
            content=self._content(generated),
            evidence=generated.evidence,
            confidence=generated.confidence,
            provider=generated.provider,
            degraded=generated.degraded,
            lock_version=1,
            created_by_actor_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        action = self._action(record, actor_id, actor_role, "generated", None)
        return await self.repository.create(
            record=record, action=action, idempotency_key=idempotency_key
        )

    async def edit(
        self,
        *,
        tenant_id: UUID,
        summary_id: UUID,
        actor_id: UUID,
        actor_role: str,
        expected_version: int,
        content: SummaryContent,
    ) -> SummaryRecord:
        self._require_role(actor_role, {"doctor"})
        current = await self.repository.get(tenant_id=tenant_id, summary_id=summary_id)
        self._require_status(current, {SummaryStatus.DRAFT})
        # Deterministic warning rules cannot be removed during narrative editing.
        if not set(current.content.red_flags).issubset(content.red_flags):
            raise SummaryTransitionError("Deterministic red flags cannot be removed")
        updated = current.model_copy(
            update={
                "content": content,
                "lock_version": current.lock_version + 1,
                "updated_at": datetime.now(UTC),
            },
            deep=True,
        )
        action = self._action(updated, actor_id, actor_role, "edited", current.status)
        return await self.repository.replace(
            record=updated, action=action, expected_version=expected_version
        )

    async def submit(
        self, *, tenant_id: UUID, summary_id: UUID, actor_id: UUID, actor_role: str,
        expected_version: int
    ) -> SummaryRecord:
        self._require_role(actor_role, {"doctor", "nurse"})
        return await self._transition(
            tenant_id=tenant_id, summary_id=summary_id, actor_id=actor_id,
            actor_role=actor_role, expected_version=expected_version,
            allowed={SummaryStatus.DRAFT}, target=SummaryStatus.IN_REVIEW,
            action_name="submitted",
        )

    async def reject(
        self, *, tenant_id: UUID, summary_id: UUID, actor_id: UUID, actor_role: str,
        expected_version: int, reason: str
    ) -> SummaryRecord:
        self._require_role(actor_role, {"doctor"})
        if not reason.strip() or len(reason) > 500:
            raise SummaryTransitionError("A bounded rejection reason is required")
        return await self._transition(
            tenant_id=tenant_id, summary_id=summary_id, actor_id=actor_id,
            actor_role=actor_role, expected_version=expected_version,
            allowed={SummaryStatus.DRAFT, SummaryStatus.IN_REVIEW},
            target=SummaryStatus.REJECTED, action_name="rejected",
            extra={"rejection_reason": reason.strip()},
        )

    async def sign(
        self, *, tenant_id: UUID, summary_id: UUID, actor_id: UUID, actor_role: str,
        expected_version: int
    ) -> SummaryRecord:
        self._require_role(actor_role, {"doctor"})
        current = await self.repository.get(tenant_id=tenant_id, summary_id=summary_id)
        self._require_status(current, {SummaryStatus.IN_REVIEW})
        signed_at = datetime.now(UTC)
        updated = current.model_copy(
            update={
                "status": SummaryStatus.SIGNED,
                "lock_version": current.lock_version + 1,
                "updated_at": signed_at,
                "signed_by_actor_id": actor_id,
                "signed_at": signed_at,
                "signature_sha256": self._signature(current, actor_id, signed_at),
            },
            deep=True,
        )
        action = self._action(updated, actor_id, actor_role, "signed", current.status)
        return await self.repository.replace(
            record=updated, action=action, expected_version=expected_version
        )

    async def regenerate(
        self, *, source: SummarySourceBundle, previous_summary_id: UUID,
        actor_id: UUID, actor_role: str, expected_version: int, idempotency_key: str
    ) -> SummaryRecord:
        self._require_role(actor_role, {"doctor"})
        previous = await self.repository.get(
            tenant_id=source.tenant_id, summary_id=previous_summary_id
        )
        self._require_status(previous, {SummaryStatus.DRAFT, SummaryStatus.REJECTED})
        if previous.lock_version != expected_version:
            from app.summary_workflow.repository import SummaryConflict
            raise SummaryConflict("Summary version is stale")
        replacement = await self.generate(
            source=source, actor_id=actor_id, actor_role=actor_role,
            idempotency_key=idempotency_key, parent=previous,
        )
        superseded = previous.model_copy(
            update={
                "status": SummaryStatus.SUPERSEDED,
                "lock_version": previous.lock_version + 1,
                "updated_at": datetime.now(UTC),
            },
            deep=True,
        )
        action = self._action(
            superseded, actor_id, actor_role, "regenerated", previous.status,
            metadata={"replacement_summary_id": str(replacement.id)},
        )
        await self.repository.replace(
            record=superseded, action=action, expected_version=expected_version
        )
        return replacement

    async def _transition(
        self, *, tenant_id: UUID, summary_id: UUID, actor_id: UUID, actor_role: str,
        expected_version: int, allowed: set[SummaryStatus], target: SummaryStatus,
        action_name: str, extra: dict[str, object] | None = None,
    ) -> SummaryRecord:
        current = await self.repository.get(tenant_id=tenant_id, summary_id=summary_id)
        self._require_status(current, allowed)
        values: dict[str, object] = {
            "status": target,
            "lock_version": current.lock_version + 1,
            "updated_at": datetime.now(UTC),
        }
        values.update(extra or {})
        updated = current.model_copy(update=values, deep=True)
        action = self._action(updated, actor_id, actor_role, action_name, current.status)
        return await self.repository.replace(
            record=updated, action=action, expected_version=expected_version
        )

    @staticmethod
    def _content(generated: ClinicalSummaryResponse) -> SummaryContent:
        return SummaryContent(**generated.model_dump(include=set(SummaryContent.model_fields)))

    @staticmethod
    def _preserve_red_flags(
        generated: ClinicalSummaryResponse, required: list[str]
    ) -> ClinicalSummaryResponse:
        flags = list(dict.fromkeys([*generated.red_flags, *required]))
        return generated.model_copy(update={"red_flags": flags})

    @staticmethod
    def _require_role(role: str, allowed: set[str]) -> None:
        if role not in allowed:
            raise SummaryPermissionError("Role is not allowed for this summary action")

    @staticmethod
    def _require_status(record: SummaryRecord, allowed: set[SummaryStatus]) -> None:
        if record.status not in allowed:
            raise SummaryTransitionError(
                f"Summary in '{record.status}' cannot perform this action"
            )

    @staticmethod
    def _signature(record: SummaryRecord, actor_id: UUID, signed_at: datetime) -> str:
        payload = {
            "content": record.content.model_dump(mode="json"),
            "summary_id": str(record.id),
            "generation": record.generation,
            "lock_version": record.lock_version + 1,
            "actor_id": str(actor_id),
            "signed_at": signed_at.isoformat(),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _action(
        record: SummaryRecord, actor_id: UUID, actor_role: str, action: str,
        from_status: SummaryStatus | None,
        metadata: dict[str, str | int | bool | None] | None = None,
    ) -> SummaryAction:
        return SummaryAction(
            id=uuid4(), tenant_id=record.tenant_id, summary_id=record.id,
            actor_id=actor_id, actor_role=actor_role, action=action,
            from_status=from_status, to_status=record.status,
            resulting_lock_version=record.lock_version,
            occurred_at=record.updated_at, metadata=metadata or {},
        )
