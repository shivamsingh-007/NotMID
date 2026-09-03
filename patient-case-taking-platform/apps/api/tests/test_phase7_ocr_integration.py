"""Live MongoDB integration evidence for protected OCR artifacts."""

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.documents.ocr_artifact import DocumentOcrArtifact
from app.documents.ocr_artifact_store import MongoOcrArtifactStore, OcrArtifactConflict
from app.ocr.base import OCRRegion, OCRResult

pytestmark = pytest.mark.skipif(
    os.getenv("PHASE7_INTEGRATION") != "1",
    reason="set PHASE7_INTEGRATION=1 when local MongoDB is running",
)


@pytest.mark.asyncio
async def test_mongodb_artifact_is_idempotent_immutable_and_tenant_scoped() -> None:
    client = AsyncIOMotorClient(os.getenv("TEST_MONGODB_URL", "mongodb://127.0.0.1:27017"))
    database_name = f"phase7_ocr_{uuid4().hex}"
    collection = client[database_name]["document_ocr_artifacts"]
    store = MongoOcrArtifactStore(collection)
    artifact = DocumentOcrArtifact.from_result(
        tenant_id=uuid4(),
        document_id=uuid4(),
        page_artifact_id=uuid4(),
        ocr_run_id=uuid4(),
        page_number=1,
        width=120,
        height=60,
        source_checksum_sha256="a" * 64,
        page_checksum_sha256="b" * 64,
        preprocessing_version="normalize.v1",
        result=OCRResult(
            text="Synthetic prescription",
            regions=[
                OCRRegion(
                    text="Synthetic prescription",
                    confidence=None,
                    bbox=(1, 2, 110, 30),
                )
            ],
            confidence=None,
            provider="mock",
            model_version="mock-ocr-v1",
            language_pack_version="synthetic-en-v1",
            duration_ms=1,
        ),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    try:
        await store.ensure_indexes()
        assert await store.save(artifact) is True
        assert await store.save(artifact) is False
        assert await store.get(artifact.tenant_id, artifact.artifact_id) == artifact
        assert await store.get(uuid4(), artifact.artifact_id) is None
        with pytest.raises(OcrArtifactConflict):
            await store.save(
                artifact.model_copy(update={"normalized_text": "conflicting replay"})
            )
    finally:
        await client.drop_database(database_name)
        client.close()
