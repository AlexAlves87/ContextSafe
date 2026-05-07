"""Tests for PseudonymStrategy (INTERMEDIATE anonymization level).

Covers alias generation via InMemoryAnonymizationAdapter.
"""
import pytest

from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import ConfidenceScore, PiiCategory, TextSpan
from contextsafe.infrastructure.nlp.anonymization_adapter import (
    InMemoryAnonymizationAdapter,
)
from contextsafe.infrastructure.nlp.strategies.pseudonym import PseudonymStrategy


def _make_category(name: str) -> PiiCategory:
    result = PiiCategory.from_string(name)
    assert result.is_ok()
    return result.unwrap()


def _detection(category: str, text: str) -> NerDetection:
    return NerDetection(
        category=_make_category(category),
        value=text,
        span=TextSpan.create(0, len(text), text).unwrap(),
        confidence=ConfidenceScore(0.9),
        source="test",
    )


@pytest.mark.asyncio
async def test_pseudonym_generates_person_alias():
    """PERSON_NAME should produce Persona_001 style alias."""
    adapter = InMemoryAnonymizationAdapter()
    strategy = PseudonymStrategy(adapter)
    detection = _detection("PERSON_NAME", "Juan Garcia")

    result = await strategy.generate_replacement(detection, "proj")

    assert result.replacement.startswith("Persona_")
    assert result.glossary_entry is not None
    assert result.glossary_entry["original_text"] == "Juan Garcia"


@pytest.mark.asyncio
async def test_pseudonym_is_consistent_within_project():
    """Same original + category + project must yield same alias."""
    adapter = InMemoryAnonymizationAdapter()
    strategy = PseudonymStrategy(adapter)
    detection = _detection("PERSON_NAME", "Maria Lopez")

    result1 = await strategy.generate_replacement(detection, "proj")
    result2 = await strategy.generate_replacement(detection, "proj")

    assert result1.replacement == result2.replacement


@pytest.mark.asyncio
async def test_pseudonym_creates_glossary_entries():
    """PseudonymStrategy must declare that it creates glossary entries."""
    adapter = InMemoryAnonymizationAdapter()
    strategy = PseudonymStrategy(adapter)

    assert strategy.creates_glossary_entries is True
