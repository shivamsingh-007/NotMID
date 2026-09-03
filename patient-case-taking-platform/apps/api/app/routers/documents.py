"""Authorized document-registry endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.audit.emitter import audit_emitter
from app.auth.dependencies import get_current_user
from app.auth.token import TokenPayload
from app.documents.dependencies import get_document_repository
from app.documents.registry import DocumentRegistryEntry
from app.documents.repository import DocumentRepository, IdempotencyConflict
from app.schemas.document import DocumentInitiateRequest, DocumentResponse

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
_UPLOAD_ROLES = frozenset({"doctor", "nurse", "receptionist"})


def _authorized_ids(user: TokenPayload, facility_id: UUID) -> tuple[UUID, UUID]:
    if user.role not in _UPLOAD_ROLES:
        raise HTTPException(status_code=403, detail="Document registration role required")
    try:
        tenant_id = UUID(user.tenant_id)
        actor_id = UUID(user.user_id)
        facility_ids = {UUID(value) for value in user.facility_ids}
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=403, detail="Invalid authorization scope") from exc
    if facility_id not in facility_ids:
        raise HTTPException(status_code=403, detail="Facility access denied")
    return tenant_id, actor_id


@router.post("", response_model=DocumentResponse)
async def initiate_document(
    body: DocumentInitiateRequest,
    response: Response,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=128,
    ),
    user: TokenPayload = Depends(get_current_user),
    repository: DocumentRepository = Depends(get_document_repository),
) -> DocumentRegistryEntry:
    tenant_id, actor_id = _authorized_ids(user, body.facility_id)
    document = DocumentRegistryEntry(
        tenant_id=tenant_id,
        facility_id=body.facility_id,
        patient_id=body.patient_id,
        encounter_id=body.encounter_id,
        uploader_actor_id=actor_id,
        purpose=body.purpose,
        consent_reference=body.consent_reference,
        original_filename=body.original_filename,
        declared_mime=body.declared_mime,
        declared_size_bytes=body.declared_size_bytes,
        idempotency_key=idempotency_key,
    )
    try:
        result = await repository.create(document)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail="Idempotency key conflict") from exc

    response.status_code = 201 if result.created else 200
    audit_emitter.emit(
        tenant_id=tenant_id,
        facility_id=body.facility_id,
        actor_id=actor_id,
        actor_type="staff",
        actor_role=user.role,
        action="document_register" if result.created else "document_register_replay",
        resource_type="document",
        resource_id=result.document.id,
        purpose=body.purpose,
        audit_metadata={"state": result.document.state.value},
    )
    return result.document
