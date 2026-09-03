"""FastAPI dependencies for the durable document workflow."""

from fastapi import HTTPException

from app.config import settings
from app.database import get_postgres_pool
from app.documents.repository import DocumentRepository, PostgresDocumentRepository
from app.documents.storage import DocumentStore, S3DocumentStore


async def get_document_repository() -> DocumentRepository:
    if not settings.DOCUMENT_WORKFLOW_ENABLED:
        raise HTTPException(status_code=503, detail="Document workflow is not enabled")
    return PostgresDocumentRepository(await get_postgres_pool())


async def get_document_store() -> DocumentStore:
    if not settings.DOCUMENT_WORKFLOW_ENABLED:
        raise HTTPException(status_code=503, detail="Document workflow is not enabled")
    return S3DocumentStore()
