"""Tests for CompositeNerAdapter voting logic.

TF-001: When RoBERTa, spaCy and regex disagree on the same span,
the merge must resolve to the correct category based on weights
and GDPR risk priority.
"""
from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import ConfidenceScore, PiiCategory, TextSpan
from contextsafe.infrastructure.nlp.composite_adapter import CompositeNerAdapter


def _make_category(name: str) -> PiiCategory:
    result = PiiCategory.from_string(name)
    assert result.is_ok()
    return result.unwrap()


def _detection(
    category: str, text: str, start: int, end: int, conf: float, source: str
) -> NerDetection:
    return NerDetection(
        category=_make_category(category),
        value=text,
        span=TextSpan.create(start, end, text).unwrap(),
        confidence=ConfidenceScore(conf),
        source=source,
    )


class TestMergeDetections:
    """Tests for _merge_detections voting logic."""

    def test_three_way_discrepancy_resolved_by_regex_weight(self):
        """Regex has highest weight; DATE should win over ORGANIZATION."""
        adapter = CompositeNerAdapter(adapters=[])
        text = "firmado el 28 de octubre de 2025"
        detections = [
            _detection("ORGANIZATION", "28 de octubre de 2025", 11, 32, 0.85, "roberta"),
            _detection("DATE", "28 de octubre de 2025", 11, 32, 0.90, "spacy"),
            _detection("DATE", "28 de octubre de 2025", 11, 32, 1.0, "regex"),
        ]

        merged = adapter._merge_detections(detections, text)

        assert len(merged) == 1
        assert merged[0].category.value == "DATE"

    def test_gdpr_tiebreaker_person_beats_org_when_scores_close(self):
        """When weighted scores are within TIE_THRESHOLD (0.3), higher GDPR
        risk priority wins. PERSON_NAME (100) > ORGANIZATION (50)."""
        adapter = CompositeNerAdapter(adapters=[])
        text = "Juan Garcia trabaja en Banco"
        # Weighted scores: roberta 0.45*2.0=0.90, spacy 0.90*1.0=0.90
        # Difference = 0.0 < 0.3 -> tiebreaker applies
        detections = [
            _detection("ORGANIZATION", "Juan Garcia", 0, 11, 0.45, "roberta"),
            _detection("PERSON_NAME", "Juan Garcia", 0, 11, 0.90, "spacy"),
        ]

        merged = adapter._merge_detections(detections, text)

        assert len(merged) == 1
        assert merged[0].category.value == "PERSON_NAME"

    def test_empty_detections_returns_empty(self):
        """No detections should return empty list."""
        adapter = CompositeNerAdapter(adapters=[])
        merged = adapter._merge_detections([], "some text")
        assert merged == []
