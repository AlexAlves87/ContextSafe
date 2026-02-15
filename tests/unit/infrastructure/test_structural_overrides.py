"""Tests for structural pattern overrides in composite NER merge pipeline.

These overrides fix misclassifications where statistical models (RoBERTa/spaCy)
override correct deterministic detections from regex patterns.

Errors addressed:
- Error 5: "28 de octubre de 2025" classified as ORG instead of DATE
- Error 6: "548/2025-D7" classified as ORG instead of CASE_NUMBER
- Error 7: MARTORELL classified as ORG instead of LOCATION (judicial header)
"""

import pytest

from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)
from contextsafe.infrastructure.nlp.composite_adapter import CompositeNerAdapter


def _make_detection(
    value: str, category: str, start: int, end: int,
    confidence: float = 0.90, source: str = "roberta",
) -> NerDetection:
    """Helper to build NerDetection for tests."""
    return NerDetection(
        category=PiiCategory.from_string(category).unwrap(),
        value=value,
        span=TextSpan.create(start, end, value).unwrap(),
        confidence=ConfidenceScore(confidence),
        source=source,
    )


class TestDateStructuralOverride:
    """Entities matching Spanish date patterns must be reclassified to DATE."""

    def test_full_written_date_reclassified_from_org(self):
        """'28 de octubre de 2025' detected as ORG -> should become DATE."""
        text = "Auto de 28 de octubre de 2025, dictado por..."
        det = _make_detection("28 de octubre de 2025", "ORGANIZATION", 8, 29)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "DATE"

    def test_numeric_date_reclassified_from_org(self):
        """'17/07/2025' detected as ORG -> should become DATE."""
        text = "fecha 17/07/2025 del expediente"
        det = _make_detection("17/07/2025", "ORGANIZATION", 6, 16)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "DATE"

    def test_dash_date_reclassified_from_org(self):
        """'17-07-2025' detected as ORG -> should become DATE."""
        text = "notificada el 17-07-2025 a las partes"
        det = _make_detection("17-07-2025", "ORGANIZATION", 14, 24)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "DATE"

    def test_date_already_correct_not_changed(self):
        """DATE detection should not be modified."""
        text = "fecha 28 de octubre de 2025"
        det = _make_detection("28 de octubre de 2025", "DATE", 6, 27, source="regex")
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "DATE"
        assert result[0].source == "regex"  # Unchanged

    def test_short_written_date_reclassified(self):
        """'17 julio 2025' detected as ORG -> should become DATE."""
        text = "celebrado el 17 julio 2025 ante"
        det = _make_detection("17 julio 2025", "ORGANIZATION", 13, 26)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "DATE"

    def test_non_date_org_not_reclassified(self):
        """A real ORG should NOT be reclassified to DATE."""
        text = "la empresa Telefónica S.A. presentó"
        det = _make_detection("Telefónica S.A.", "ORGANIZATION", 11, 26)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "ORGANIZATION"


class TestCaseNumberStructuralOverride:
    """Entities matching case number patterns must be reclassified to CASE_NUMBER."""

    def test_case_number_with_suffix_reclassified(self):
        """'548/2025-D7' detected as ORG -> should become CASE_NUMBER."""
        text = "JUICIO VERBAL 548/2025-D7 seguido ante"
        det = _make_detection("548/2025-D7", "ORGANIZATION", 14, 25)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "CASE_NUMBER"

    def test_simple_case_number_reclassified(self):
        """'123/2024' detected as ORG -> should become CASE_NUMBER."""
        text = "Autos 123/2024 del Juzgado"
        det = _make_detection("123/2024", "ORGANIZATION", 6, 14)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "CASE_NUMBER"

    def test_case_number_already_correct(self):
        """CASE_NUMBER detection should not be modified."""
        text = "nº 548/2025-D7"
        det = _make_detection("548/2025-D7", "CASE_NUMBER", 3, 14, source="regex")
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "CASE_NUMBER"


class TestLocationJudicialHeaderOverride:
    """City names in judicial headers should be LOCATION, not ORG."""

    def test_martorell_after_judicial_number_becomes_location(self):
        """MARTORELL after 'Nº 6 DE' in judicial header -> LOCATION."""
        text = "Juzgado de Primera Instancia e Instrucción Nº 6 DE MARTORELL"
        det = _make_detection("MARTORELL", "ORGANIZATION", 51, 60)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "LOCATION"

    def test_city_after_judicial_number_lowercase(self):
        """City after 'Nº 3 de' -> LOCATION."""
        text = "Juzgado de lo Social Nº 3 de Barcelona"
        det = _make_detection("Barcelona", "ORGANIZATION", 29, 38)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "LOCATION"

    def test_real_org_not_reclassified_as_location(self):
        """An ORG that isn't in a judicial header should stay ORG."""
        text = "la empresa Endesa presentó demanda"
        det = _make_detection("Endesa", "ORGANIZATION", 11, 17)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "ORGANIZATION"

    def test_audiencia_provincial_city_becomes_location(self):
        """City after 'Audiencia Provincial de' -> LOCATION."""
        text = "Audiencia Provincial de Sevilla, Sección 2ª"
        det = _make_detection("Sevilla", "ORGANIZATION", 24, 31)
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides([det], text)
        assert result[0].category.value == "LOCATION"


class TestMultipleOverridesInSameText:
    """Multiple structural overrides can fire in the same document."""

    def test_date_and_case_number_both_fixed(self):
        """Both a date and a case number should be reclassified."""
        text = "Auto de 28 de octubre de 2025 en JUICIO VERBAL 548/2025-D7"
        dets = [
            _make_detection("28 de octubre de 2025", "ORGANIZATION", 8, 29),
            _make_detection("548/2025-D7", "ORGANIZATION", 47, 58),
        ]
        adapter = CompositeNerAdapter(adapters=[])
        result = adapter._apply_structural_overrides(dets, text)
        assert result[0].category.value == "DATE"
        assert result[1].category.value == "CASE_NUMBER"
