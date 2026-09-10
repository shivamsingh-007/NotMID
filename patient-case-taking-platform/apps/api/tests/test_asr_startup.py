"""Speech-only deployments must not require the separate OCR runtime."""

from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.main import app, lifespan


@pytest.mark.asyncio
async def test_speech_warmup_loads_both_languages_without_ocr(monkeypatch):
    hindi = AsyncMock()
    english = AsyncMock()
    monkeypatch.setattr(settings, "ASR_PROVIDER", "ai4bharat")
    monkeypatch.setattr(settings, "MODEL_WARMUP_ON_START", False)
    monkeypatch.setattr(settings, "ASR_WARMUP_ON_START", True)
    monkeypatch.setattr("app.asr.registry.get_active_provider", lambda: hindi)

    def language_provider(language):
        assert language == "en"
        return english

    def unexpected_ocr():
        raise AssertionError("OCR belongs to the document worker")

    monkeypatch.setattr("app.asr.registry.get_provider_for_language", language_provider)
    monkeypatch.setattr("app.ocr.registry.get_active_provider", unexpected_ocr)
    async with lifespan(app):
        hindi.warmup.assert_awaited_once()
        english.warmup.assert_awaited_once()


@pytest.mark.asyncio
async def test_speech_warmup_failure_prevents_startup(monkeypatch):
    provider = AsyncMock()
    provider.warmup.side_effect = RuntimeError("model unavailable")
    monkeypatch.setattr(settings, "ASR_PROVIDER", "mock")
    monkeypatch.setattr(settings, "MODEL_WARMUP_ON_START", False)
    monkeypatch.setattr(settings, "ASR_WARMUP_ON_START", True)
    monkeypatch.setattr("app.asr.registry.get_active_provider", lambda: provider)
    with pytest.raises(RuntimeError, match="model unavailable"):
        async with lifespan(app):
            pytest.fail("Startup must fail when requested warmup fails")
