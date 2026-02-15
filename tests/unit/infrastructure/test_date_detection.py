"""Tests for date detection without surrounding context keywords."""

import pytest

from contextsafe.infrastructure.nlp.regex_adapter import RegexNerAdapter


class TestDateDetectionWithoutContext:
    """Dates should be detected even without context keywords like 'fecha' nearby."""

    @pytest.fixture
    def adapter(self):
        return RegexNerAdapter()

    @pytest.mark.asyncio
    async def test_detects_written_date_in_isolation(self, adapter):
        """'4 de diciembre de 2024' should be detected as DATE."""
        text = "Martorell, a 4 de diciembre de 2024."
        detections = await adapter.detect_entities(text)
        date_dets = [d for d in detections if d.category.value == "DATE"]
        assert len(date_dets) >= 1
        assert "4 de diciembre de 2024" in date_dets[0].value

    @pytest.mark.asyncio
    async def test_detects_single_digit_day(self, adapter):
        """Single-digit day '9 de diciembre' should be detected."""
        text = "firmado el 9 de diciembre de 2024 por el Letrado"
        detections = await adapter.detect_entities(text)
        date_dets = [d for d in detections if d.category.value == "DATE"]
        assert len(date_dets) >= 1
        assert "9 de diciembre de 2024" in date_dets[0].value

    @pytest.mark.asyncio
    async def test_detects_date_in_suplico_section(self, adapter):
        """Dates in SUPLICO section should be detected."""
        text = "SUPLICO al Juzgado que desde el 4 de diciembre de 2024 se proceda"
        detections = await adapter.detect_entities(text)
        date_dets = [d for d in detections if d.category.value == "DATE"]
        assert len(date_dets) >= 1

    @pytest.mark.asyncio
    async def test_detects_all_months(self, adapter):
        """All Spanish months should be recognized."""
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        for month in months:
            text = f"el 15 de {month} de 2024 se celebró"
            detections = await adapter.detect_entities(text)
            date_dets = [d for d in detections if d.category.value == "DATE"]
            assert len(date_dets) >= 1, f"Failed to detect date with month '{month}'"

    @pytest.mark.asyncio
    async def test_detects_numeric_date(self, adapter):
        """Numeric format dates should be detected."""
        text = "con fecha 04/12/2024 se notificó"
        detections = await adapter.detect_entities(text)
        date_dets = [d for d in detections if d.category.value == "DATE"]
        assert len(date_dets) >= 1


class TestSpanishDateRecognizerNoContext:
    """SpanishDateRecognizer should work without context keywords."""

    def test_default_context_is_empty(self):
        """Default context should be empty so dates match without keywords."""
        from contextsafe.infrastructure.nlp.recognizers.spanish_dates import (
            SpanishDateRecognizer,
        )
        recognizer = SpanishDateRecognizer()
        # The recognizer should work with empty context (no requirement)
        assert recognizer.context == [] or recognizer.context is None or len(recognizer.context) == 0
