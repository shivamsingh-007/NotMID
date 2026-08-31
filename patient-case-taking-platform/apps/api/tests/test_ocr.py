"""Tests for OCR provider."""
from types import SimpleNamespace

from app.ocr.base import OCRRegion, OCRResult
from app.ocr.fast_paddle_provider import _regions_from_payload, _result_payload
from app.ocr.paddle_provider import _read_block


def test_ocr_region_dataclass():
    region = OCRRegion(text="hello", confidence=0.95, bbox=(0, 0, 100, 50))
    assert region.text == "hello"
    assert region.bbox == (0, 0, 100, 50)


def test_ocr_result_dataclass():
    result = OCRResult(
        text="prescription text",
        regions=[OCRRegion(text="line1", confidence=0.9)],
        confidence=0.9,
        provider="test",
        duration_ms=100,
    )
    assert result.text == "prescription text"
    assert len(result.regions) == 1


def test_paddleocr_37_object_block_is_normalized():
    block = SimpleNamespace(content="Patient Name: Ramesh Kumar", bbox=[1, 2, 3, 4])
    content, bbox = _read_block(block)
    assert content == "Patient Name: Ramesh Kumar"
    assert bbox == [1, 2, 3, 4]


def test_paddleocr_v5_result_payload_is_normalized():
    result = SimpleNamespace(
        json={
            "res": {
                "rec_texts": ["Patient Name: Ramesh Kumar", "Age: 45"],
                "rec_scores": [0.99, 0.97],
                "rec_boxes": [[10, 20, 300, 50], [10, 60, 100, 90]],
            }
        }
    )

    regions = _regions_from_payload(_result_payload(result))

    assert [region.text for region in regions] == ["Patient Name: Ramesh Kumar", "Age: 45"]
    assert regions[0].confidence == 0.99
    assert regions[0].bbox == (10, 20, 300, 50)


def test_paddleocr_v5_skips_blank_text_and_invalid_box():
    payload = {
        "rec_texts": ["", "Rx: Metformin 500mg"],
        "rec_scores": [0.1, 0.98],
        "rec_boxes": [[1, 2, 3, 4], [1, 2, 3]],
    }

    regions = _regions_from_payload(payload)

    assert len(regions) == 1
    assert regions[0].text == "Rx: Metformin 500mg"
    assert regions[0].bbox is None
