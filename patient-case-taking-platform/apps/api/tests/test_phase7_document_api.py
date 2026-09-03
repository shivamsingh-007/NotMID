"""Authorized Phase 7 document-registration API tests."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.audit.emitter import audit_emitter
from app.auth.token import create_dev_token
from app.documents.dependencies import get_document_repository
from app.documents.registry import DocumentRegistryEntry
from app.documents.repository import DocumentCreateResult, IdempotencyConflict
from app.main import app

client = TestClient(app)


class _Repository:
    def __init__(self) -> None:
        self.documents: dict[tuple[UUID, str], DocumentRegistryEntry] = {}
        self.create_calls = 0

    async def create(self, document: DocumentRegistryEntry) -> DocumentCreateResult:
        self.create_calls += 1
        key = (document.tenant_id, document.idempotency_key)
        existing = self.documents.get(key)
        if existing is None:
            self.documents[key] = document
            return DocumentCreateResult(document=document, created=True)
        if existing.original_filename != document.original_filename:
            raise IdempotencyConflict("conflicting registration")
        return DocumentCreateResult(document=existing, created=False)


@pytest.fixture
def repository() -> _Repository:
    value = _Repository()
    app.dependency_overrides[get_document_repository] = lambda: value
    yield value
    app.dependency_overrides.pop(get_document_repository, None)


def _headers(tenant_id: UUID, facility_id: UUID, *, role: str = "nurse") -> dict[str, str]:
    actor_id = uuid4()
    token = create_dev_token(
        str(actor_id),
        "document-reviewer@example.test",
        role,
        str(tenant_id),
        [str(facility_id)],
    )
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "upload-attempt-1",
    }


def _body(facility_id: UUID) -> dict[str, str | int]:
    return {
        "facility_id": str(facility_id),
        "patient_id": str(uuid4()),
        "encounter_id": str(uuid4()),
        "purpose": "treatment",
        "consent_reference": "consent/test-version-1",
        "original_filename": "prescription.jpg",
        "declared_mime": "image/jpeg",
        "declared_size_bytes": 1024,
    }


def test_authorized_registration_returns_minimal_initiated_resource(
    repository: _Repository,
) -> None:
    tenant_id = uuid4()
    facility_id = uuid4()
    audit_emitter._events.clear()

    response = client.post(
        "/api/v1/documents",
        json=_body(facility_id),
        headers=_headers(tenant_id, facility_id),
    )

    assert response.status_code == 201
    assert response.json()["tenant_id"] == str(tenant_id)
    assert response.json()["facility_id"] == str(facility_id)
    assert response.json()["state"] == "initiated"
    assert "original_filename" not in response.json()
    assert "object_key" not in response.json()
    assert repository.create_calls == 1
    assert "prescription.jpg" not in str(audit_emitter._events[-1])


def test_identical_idempotent_retry_returns_existing_resource(repository: _Repository) -> None:
    tenant_id = uuid4()
    facility_id = uuid4()
    headers = _headers(tenant_id, facility_id)
    body = _body(facility_id)

    first = client.post("/api/v1/documents", json=body, headers=headers)
    second = client.post("/api/v1/documents", json=body, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_cross_facility_registration_is_denied_before_repository_access(
    repository: _Repository,
) -> None:
    tenant_id = uuid4()
    authorized_facility = uuid4()

    response = client.post(
        "/api/v1/documents",
        json=_body(uuid4()),
        headers=_headers(tenant_id, authorized_facility),
    )

    assert response.status_code == 403
    assert repository.create_calls == 0


def test_unapproved_role_cannot_register_a_document(repository: _Repository) -> None:
    tenant_id = uuid4()
    facility_id = uuid4()

    response = client.post(
        "/api/v1/documents",
        json=_body(facility_id),
        headers=_headers(tenant_id, facility_id, role="auditor"),
    )

    assert response.status_code == 403
    assert repository.create_calls == 0


def test_conflicting_idempotency_key_returns_conflict(repository: _Repository) -> None:
    tenant_id = uuid4()
    facility_id = uuid4()
    headers = _headers(tenant_id, facility_id)
    body = _body(facility_id)
    client.post("/api/v1/documents", json=body, headers=headers)
    body["original_filename"] = "different.jpg"

    response = client.post("/api/v1/documents", json=body, headers=headers)

    assert response.status_code == 409


def test_registration_requires_an_idempotency_key(repository: _Repository) -> None:
    tenant_id = uuid4()
    facility_id = uuid4()
    headers = _headers(tenant_id, facility_id)
    headers.pop("Idempotency-Key")

    response = client.post(
        "/api/v1/documents",
        json=_body(facility_id),
        headers=headers,
    )

    assert response.status_code == 422
    assert repository.create_calls == 0


def test_document_workflow_fails_closed_when_not_enabled() -> None:
    tenant_id = uuid4()
    facility_id = uuid4()

    response = client.post(
        "/api/v1/documents",
        json=_body(facility_id),
        headers=_headers(tenant_id, facility_id),
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Document workflow is not enabled"}
