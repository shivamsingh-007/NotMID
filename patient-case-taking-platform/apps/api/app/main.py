import asyncio
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_postgres_pool
from app.routers import (
    asr,
    audit,
    auth,
    ayush,
    clinical,
    clinical_summaries,
    consent,
    document_operations,
    document_reviews,
    documents,
    encounters,
    facilities,
    fhir,
    health,
    intake_sessions,
    llm,
    ocr,
    patient_portal,
    patients,
    reviewed_documents,
    summary_workflows,
    triage,
    tts,
)


async def _warm_provider(get_provider: Callable):
    provider = get_provider()
    warmup = getattr(provider, "warmup", None)
    if warmup is not None:
        await warmup()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.MODEL_WARMUP_ON_START:
        from app.asr.registry import get_active_provider as get_asr_provider
        from app.asr.registry import get_provider_for_language
        from app.ocr.registry import get_active_provider as get_ocr_provider

        # Run independent model initialization concurrently. When enabled, a
        # failed warmup deliberately fails readiness instead of moving the cold
        # start or dependency error into a patient's request.
        warmups = [
            _warm_provider(get_asr_provider),
            _warm_provider(get_ocr_provider),
        ]
        if settings.ASR_PROVIDER != "mock":
            warmups.append(_warm_provider(lambda: get_provider_for_language("en")))
        await asyncio.gather(*warmups)
    try:
        yield
    finally:
        await close_postgres_pool()


app = FastAPI(
    title="MediKiosk Clinical Platform API",
    version="0.1.0",
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/redoc" if settings.APP_ENV == "development" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

app.include_router(health.router)
app.include_router(asr.router)  # ASR always available (not behind demo gate)
app.include_router(documents.router)  # Fails closed unless durable workflow is enabled.
app.include_router(document_reviews.router)
app.include_router(reviewed_documents.router)
app.include_router(document_operations.router)
app.include_router(summary_workflows.router)  # Durable; fails closed unless enabled.
app.include_router(tts.router)  # Offline deterministic mock; unsupported providers fail closed.
app.include_router(patient_portal.router)  # Authenticated patient-self projections only.

# These in-memory routes are useful for contract and UI prototyping, but they do
# not yet provide Clerk verification, durable persistence, tenant isolation, or
# a compliance-grade audit trail. Fail closed unless a developer explicitly
# enables the demo surface.
if settings.ENABLE_DEMO_ROUTES:
    app.include_router(auth.router)
    app.include_router(patients.router)
    app.include_router(facilities.router)
    app.include_router(encounters.router)
    app.include_router(intake_sessions.router)
    app.include_router(llm.router)
    app.include_router(triage.router)
    app.include_router(consent.router)
    app.include_router(audit.router)
    app.include_router(clinical_summaries.router)
    app.include_router(ayush.router)
    app.include_router(fhir.router)
    app.include_router(clinical.router)
    app.include_router(ocr.router)
