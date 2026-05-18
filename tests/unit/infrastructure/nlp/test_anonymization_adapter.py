"""Tests for InMemoryAnonymizationAdapter.

TF-003: When DNI_NIE (risk 95) and ORGANIZATION (risk 50) overlap,
the DNI must survive and be anonymized.
"""
import pytest

from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import ConfidenceScore, PiiCategory, TextSpan
from contextsafe.infrastructure.nlp.anonymization_adapter import (
    InMemoryAnonymizationAdapter,
)


def _make_category(name: str) -> PiiCategory:
    result = PiiCategory.from_string(name)
    assert result.is_ok()
    return result.unwrap()


def _detection(category: str, text: str, start: int, end: int, conf: float) -> NerDetection:
    return NerDetection(
        category=_make_category(category),
        value=text,
        span=TextSpan.create(start, end, text).unwrap(),
        confidence=ConfidenceScore(conf),
        source="test",
    )


@pytest.mark.asyncio()
async def test_gdpr_priority_survives_overlap():
    """DNI_NIE inside ORGANIZATION span must still be anonymized."""
    adapter = InMemoryAnonymizationAdapter()
    text = "Empresa 12345678Z presento"
    detections = [
        _detection("ORGANIZATION", "Empresa 12345678Z", 0, 17, 0.8),
        _detection("DNI_NIE", "12345678Z", 8, 17, 1.0),
    ]

    result = await adapter.anonymize_text(text, detections, "proj")

    assert "12345678Z" not in result.anonymized_text
    assert "ID_" in result.anonymized_text or "DNI_" in result.anonymized_text


@pytest.mark.asyncio()
async def test_longer_span_does_not_override_higher_risk():
    """A longer span with lower GDPR priority must not hide a shorter high-risk span."""
    adapter = InMemoryAnonymizationAdapter()
    text = "Contacto: Juan Garcia, 612345678"
    detections = [
        _detection("PERSON_NAME", "Juan Garcia", 10, 21, 0.95),
        _detection("PHONE", "612345678", 23, 32, 0.99),
    ]

    result = await adapter.anonymize_text(text, detections, "proj")

    assert "612345678" not in result.anonymized_text
    assert "Juan Garcia" not in result.anonymized_text
