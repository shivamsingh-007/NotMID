"""Live PostgreSQL evidence for the patient-owned portal boundary."""

import os
from typing import AsyncIterator
from uuid import uuid4

import asyncpg
import pytest
import pytest_asyncio

from app.documents.registry import DocumentRegistryEntry
from app.documents.repository import PostgresDocumentRepository
from app.llm.providers import MockClinicalProvider
from app.llm.service import LLMRouter
from app.migrations import apply_migrations
from app.patient_portal.consent_repository import PostgresPatientConsentRepository
from app.patient_portal.contracts import (
    PatientConsentCreate,
    PatientIntakeSubmissionCreate,
)
from app.patient_portal.intake_repository import (
    PatientIntakeAuthorizationDenied,
    PatientIntakeConflict,
    PostgresPatientIntakeRepository,
)
from app.patient_portal.service import PatientIdentity, PatientPortalService
from app.summary_workflow.contracts import SummaryContent, SummarySourceBundle
from app.summary_workflow.repository import PostgresSummaryRepository
from app.summary_workflow.service import SummaryWorkflowService

pytestmark = pytest.mark.skipif(
    os.getenv("PATIENT_PORTAL_INTEGRATION") != "1",
    reason="set PATIENT_PORTAL_INTEGRATION=1 when local PostgreSQL is running",
)

DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://notmid:notmid-local-only@localhost:5432/notmid",
)


@pytest_asyncio.fixture
async def repositories() -> AsyncIterator[tuple[asyncpg.Pool, str]]:
    suffix = uuid4().hex
    schema = f"patient_portal_{suffix}"
    role = f"patient_portal_role_{suffix}"
    admin = await asyncpg.connect(DATABASE_URL)
    pool = None
    try:
        await admin.execute(f'CREATE SCHEMA "{schema}"')
        await admin.execute(f'SET search_path TO "{schema}"')
        await apply_migrations(admin)
        await admin.execute(f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOBYPASSRLS')
        await admin.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"')
        await admin.execute(
            f'GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA "{schema}" TO "{role}"'
        )

        async def initialize(connection: asyncpg.Connection) -> None:
            await connection.execute(f'SET ROLE "{role}"')
            await connection.execute(f'SET search_path TO "{schema}"')

        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2, setup=initialize)
        assert pool is not None
        yield pool, schema
    finally:
        if pool is not None:
            await pool.close()
        await admin.execute("RESET ROLE")
        await admin.execute("SET search_path TO public")
        await admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        await admin.execute(f'DROP ROLE IF EXISTS "{role}"')
        await admin.close()


class _EmptyTimeline:
    async def list_timeline(self, **_kwargs):
        return []

    async def count_timeline(self, **_kwargs):
        return 0


@pytest.mark.asyncio
async def test_patient_portal_is_self_scoped_consent_gated_and_idempotent(repositories):
    pool, _schema = repositories
    tenant_id, facility_id, patient_id, other_patient_id = (uuid4() for _ in range(4))
    encounter_id, session_id = uuid4(), uuid4()
    identity = PatientIdentity(
        tenant_id=tenant_id,
        patient_id=patient_id,
        facility_ids={facility_id},
    )

    consents = PostgresPatientConsentRepository(pool)
    consent = await consents.create(
        identity,
        PatientConsentCreate(encounter_id=encounter_id, document_upload=True),
    )
    assert [item.id for item in await consents.list_for_patient(identity)] == [consent.id]

    content = SummaryContent(
        chief_complaint="Chest discomfort",
        history_of_present_illness=["Started this morning"],
        relevant_negatives=["No fainting reported"],
        document_facts=[],
        red_flags=[],
        uncertainties=["Exact onset time needs confirmation"],
    )
    command = PatientIntakeSubmissionCreate(
        facility_id=facility_id,
        encounter_id=encounter_id,
        session_id=session_id,
        consent_id=consent.id,
        language="en",
        chief_complaint="Chest discomfort",
        confirmed_answers={"site": "central"},
        summary_draft=content,
        decision="accepted",
        provider="mock",
    )
    intakes = PostgresPatientIntakeRepository(pool)
    created = await intakes.create(identity, command, "patient-intake-1")
    replay = await intakes.create(identity, command, "patient-intake-1")
    assert replay.id == created.id
    with pytest.raises(PatientIntakeConflict):
        await intakes.create(
            identity,
            command.model_copy(update={"chief_complaint": "Changed complaint"}),
            "patient-intake-1",
        )
    with pytest.raises(PatientIntakeAuthorizationDenied):
        await intakes.create(
            identity,
            command.model_copy(update={"consent_id": uuid4(), "encounter_id": uuid4()}),
            "missing-consent",
        )

    documents = PostgresDocumentRepository(pool)
    own_document = DocumentRegistryEntry(
        tenant_id=tenant_id,
        facility_id=facility_id,
        patient_id=patient_id,
        encounter_id=encounter_id,
        uploader_actor_id=patient_id,
        purpose="treatment",
        consent_reference=str(consent.id),
        original_filename="prescription.pdf",
        declared_mime="application/pdf",
        declared_size_bytes=128,
        idempotency_key="patient-document-1",
    )
    other_document = own_document.model_copy(
        update={
            "id": uuid4(),
            "patient_id": other_patient_id,
            "idempotency_key": "other-patient-document",
        }
    )
    await documents.create(own_document)
    await documents.create(other_document)
    visible_documents = await documents.list_for_patient(
        tenant_id=tenant_id,
        patient_id=patient_id,
        facility_ids={facility_id},
    )
    assert [item.id for item in visible_documents] == [own_document.id]

    summaries = PostgresSummaryRepository(pool)
    workflow = SummaryWorkflowService(summaries, LLMRouter(MockClinicalProvider()))
    source = SummarySourceBundle(
        tenant_id=tenant_id,
        facility_id=facility_id,
        patient_id=patient_id,
        encounter_id=encounter_id,
        chief_complaint="Chest discomfort",
        confirmed_answers={"site": "central"},
    )
    doctor_id = uuid4()
    draft = await workflow.generate(
        source=source,
        actor_id=doctor_id,
        actor_role="doctor",
        idempotency_key="patient-report-1",
    )
    submitted = await workflow.submit(
        tenant_id=tenant_id,
        summary_id=draft.id,
        actor_id=doctor_id,
        actor_role="doctor",
        expected_version=draft.lock_version,
    )
    signed = await workflow.sign(
        tenant_id=tenant_id,
        summary_id=draft.id,
        actor_id=doctor_id,
        actor_role="doctor",
        expected_version=submitted.lock_version,
    )
    portal = PatientPortalService(summaries, _EmptyTimeline())
    reports = await portal.list_reports(identity)
    assert [item.id for item in reports] == [signed.id]
    dashboard = await portal.dashboard(identity)
    assert dashboard.signed_report_count == 1
    assert dashboard.reviewed_timeline_count == 0
    assert await portal.list_reports(
        PatientIdentity(tenant_id, other_patient_id, {facility_id})
    ) == []
    detail = await portal.get_report(identity, signed.id)
    assert detail.content.chief_complaint == "Chest discomfort"
    download = await portal.render_report_download(identity, signed.id)
    assert "MEDIKIOSK SIGNED PATIENT REPORT" in download
    assert signed.signature_sha256 in download
