"""Fail-closed OCR provider routing policy tests."""

import pytest

from app.config import settings
from app.ocr.registry import get_active_provider, set_active_provider


def test_complex_layout_provider_requires_explicit_approval(monkeypatch) -> None:
    set_active_provider(None)
    monkeypatch.setattr(settings, "OCR_PROVIDER", "paddleocr_vl")
    monkeypatch.setattr(settings, "OCR_ALLOW_COMPLEX_LAYOUT_PROVIDER", False)

    with pytest.raises(RuntimeError, match="not approved"):
        get_active_provider()

    set_active_provider(None)
