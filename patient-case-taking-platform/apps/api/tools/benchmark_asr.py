"""Measure ASR latency, real-time factor, and WER from a labeled JSONL manifest."""

import argparse
import asyncio
import json
import math
import re
import statistics
import time
import unicodedata
import wave
from pathlib import Path

from app.asr.registry import get_provider_for_language

PUNCTUATION = re.compile(r"[^\w\s\u0900-\u097f]", re.UNICODE)


def normalize(text: str) -> list[str]:
    value = unicodedata.normalize("NFC", text).lower().replace("॥", " ").replace("।", " ")
    return PUNCTUATION.sub(" ", value).split()


def word_error_rate(reference: str, hypothesis: str) -> float:
    expected = normalize(reference)
    actual = normalize(hypothesis)
    if not expected:
        return 0.0 if not actual else 1.0
    previous = list(range(len(actual) + 1))
    for row, expected_word in enumerate(expected, start=1):
        current = [row]
        for column, actual_word in enumerate(actual, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (expected_word != actual_word),
                )
            )
        previous = current
    return previous[-1] / len(expected)


def audio_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


def nearest_rank_percentile(values: list[float], percentile: float) -> float:
    """Return the nearest-rank percentile, including the tail for small samples."""
    if not values:
        raise ValueError("Cannot calculate a percentile from an empty sample")
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


async def run(manifest: Path, output: Path) -> dict:
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line]
    results = []
    for row in rows:
        path = (manifest.parent / row["audio"]).resolve()
        provider = get_provider_for_language(row["language"])
        started = time.perf_counter()
        transcription = await provider.transcribe_file(path.read_bytes(), row["language"])
        latency = time.perf_counter() - started
        duration = audio_duration(path)
        results.append(
            {
                **row,
                "hypothesis": transcription.text,
                "provider": transcription.provider,
                "duration_s": round(duration, 3),
                "latency_s": round(latency, 3),
                "rtf": round(latency / duration, 3),
                "wer": round(word_error_rate(row["reference"], transcription.text), 4),
            }
        )
    warm_results = results[1:] or results
    summary = {
        "sample_count": len(results),
        "mean_wer": round(statistics.mean(item["wer"] for item in results), 4),
        "cold_start_latency_s": results[0]["latency_s"],
        "all_sample_p95_latency_s": round(
            nearest_rank_percentile([item["latency_s"] for item in results], 0.95), 3
        ),
        "warm_p95_latency_s": round(
            nearest_rank_percentile(
                [item["latency_s"] for item in warm_results], 0.95
            ),
            3,
        ),
        "warm_mean_rtf": round(
            statistics.mean(item["rtf"] for item in warm_results), 3
        ),
        "results": results,
    }
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("asr-benchmark-results.json"))
    arguments = parser.parse_args()
    # ASCII-safe console JSON also works in Windows legacy-codepage terminals;
    # the output artifact above preserves the original UTF-8 text.
    print(json.dumps(asyncio.run(run(arguments.manifest, arguments.output)), ensure_ascii=True))
