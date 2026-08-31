"""Deterministic OCR provider used for local development and contract tests."""

from app.ocr.base import OCRProvider, OCRRegion, OCRResult


class MockOCRProvider(OCRProvider):
    @property
    def provider_name(self) -> str:
        return "mock"

    async def recognize(self, image_bytes: bytes, mime_type: str = "image/png") -> OCRResult:
        if not image_bytes:
            raise ValueError("Image file is empty")
        text = "Sample clinical document"
        return OCRResult(
            text=text,
            regions=[OCRRegion(text=text, confidence=1.0)],
            confidence=1.0,
            provider=self.provider_name,
            duration_ms=0,
        )
