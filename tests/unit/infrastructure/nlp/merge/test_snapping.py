"""Tests for BPE token snapping alignment.

TF-002: RoBERTa BPE cuts words incorrectly; snap_to_tokens must expand
to complete spaCy token boundaries.
"""
from unittest.mock import MagicMock

from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import ConfidenceScore, PiiCategory, TextSpan
from contextsafe.infrastructure.nlp.merge.snapping import snap_to_tokens


def _make_category(name: str) -> PiiCategory:
    result = PiiCategory.from_string(name)
    assert result.is_ok(), f"Invalid category: {name}"
    return result.unwrap()


def test_snap_to_tokens_fixes_bpe_cut():
    """RoBERTa detects 'an' instead of 'Juan'; snapping should expand to 'Juan'."""
    mock_token = MagicMock()
    mock_token.idx = 0
    mock_token.text = "Juan"
    mock_token.text_with_ws = "Juan "

    mock_token2 = MagicMock()
    mock_token2.idx = 5
    mock_token2.text = "Carlos"
    mock_token2.text_with_ws = "Carlos"

    mock_spacy_doc = MagicMock()
    mock_spacy_doc.__iter__ = lambda self: iter([mock_token, mock_token2])
    mock_spacy_doc.text = "Juan Carlos"

    detection = NerDetection(
        category=_make_category("PERSON_NAME"),
        value="an",
        span=TextSpan.create(2, 4, "an").unwrap(),
        confidence=ConfidenceScore(0.9),
        source="roberta",
    )

    snapped = snap_to_tokens(detection, mock_spacy_doc)

    assert snapped.value == "Juan"
    assert snapped.span.start == 0
    assert snapped.span.end == 4


def test_snap_to_tokens_no_change_for_complete_token():
    """If span already aligns perfectly, return unchanged."""
    mock_token = MagicMock()
    mock_token.idx = 0
    mock_token.text = "Maria"
    mock_token.text_with_ws = "Maria "

    mock_spacy_doc = MagicMock()
    mock_spacy_doc.__iter__ = lambda self: iter([mock_token])
    mock_spacy_doc.text = "Maria"

    detection = NerDetection(
        category=_make_category("PERSON_NAME"),
        value="Maria",
        span=TextSpan.create(0, 5, "Maria").unwrap(),
        confidence=ConfidenceScore(0.95),
        source="roberta",
    )

    snapped = snap_to_tokens(detection, mock_spacy_doc)

    assert snapped is detection  # same object, no change


def test_snap_to_tokens_ignores_non_roberta_sources():
    """Only roberta sources should be snapped."""
    detection = NerDetection(
        category=_make_category("PERSON_NAME"),
        value="Juan",
        span=TextSpan.create(0, 4, "Juan").unwrap(),
        confidence=ConfidenceScore(0.9),
        source="regex",
    )

    result = snap_to_tokens(detection, MagicMock())
    assert result is detection
