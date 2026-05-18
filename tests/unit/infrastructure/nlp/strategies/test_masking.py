"""Tests for MaskingStrategy (BASIC anonymization level).

Covers asterisk replacement with and without word structure preservation.
"""
import pytest

from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import ConfidenceScore, PiiCategory, TextSpan
from contextsafe.infrastructure.nlp.strategies.masking import MaskingStrategy


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


@pytest.mark.asyncio()
async def test_masking_preserves_word_structure():
    """Default masking splits words and masks each separately."""
    strategy = MaskingStrategy(min_length=4)
    detection = _detection("PERSON_NAME", "Juan Perez")

    result = await strategy.generate_replacement(detection, "proj")

    assert result.replacement == "**** *****"
    assert result.glossary_entry is None


@pytest.mark.asyncio()
async def test_masking_single_block_when_disabled():
    """With preserve_word_structure=False, create single mask block."""
    strategy = MaskingStrategy(preserve_word_structure=False)
    detection = _detection("PERSON_NAME", "Juan Perez")

    result = await strategy.generate_replacement(detection, "proj")

    assert result.replacement == "**********"


@pytest.mark.asyncio()
async def test_masking_respects_min_length():
    """Short words are padded to min_length to prevent length inference."""
    strategy = MaskingStrategy(min_length=5)
    detection = _detection("PERSON_NAME", "Ana")

    result = await strategy.generate_replacement(detection, "proj")

    assert result.replacement == "*****"
