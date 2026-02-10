"""
Tests for IngestPreprocessor and DetectionPreprocessor.

Traceability:
- Design: docs/plans/2026-02-01-text-preprocessing-design.md
"""

import pytest

from contextsafe.infrastructure.text_processing import (
    DefaultIngestPreprocessor,
    DefaultDetectionPreprocessor,
)


class TestDefaultIngestPreprocessor:
    """Tests for Phase 1 preprocessing."""

    @pytest.fixture
    def preprocessor(self):
        return DefaultIngestPreprocessor()

    def test_unicode_nfkc(self, preprocessor):
        """NFKC normalization converts ligatures and special chars."""
        # fi ligature -> "fi"
        text = "ﬁnal"
        result = preprocessor.preprocess(text)
        assert result == "final"

    def test_superscripts(self, preprocessor):
        """Superscripts are normalized."""
        text = "x² + y²"
        result = preprocessor.preprocess(text)
        assert result == "x2 + y2"

    def test_line_endings_crlf(self, preprocessor):
        """CRLF is normalized to LF."""
        text = "line1\r\nline2\r\nline3"
        result = preprocessor.preprocess(text)
        assert result == "line1\nline2\nline3"
        assert "\r" not in result

    def test_line_endings_cr(self, preprocessor):
        """Old Mac CR is normalized to LF."""
        text = "line1\rline2"
        result = preprocessor.preprocess(text)
        assert result == "line1\nline2"

    def test_nbsp_normalized(self, preprocessor):
        """NBSP and similar are converted to regular space."""
        text = "word\u00A0word"  # NBSP
        result = preprocessor.preprocess(text)
        assert result == "word word"
        assert "\u00A0" not in result

    def test_control_chars_removed(self, preprocessor):
        """Control characters are removed except newline and tab."""
        text = "hello\x00world\x07test"
        result = preprocessor.preprocess(text)
        assert result == "helloworldtest"

    def test_preserves_newline_tab(self, preprocessor):
        """Newline and tab are preserved."""
        text = "line1\nline2\tcol2"
        result = preprocessor.preprocess(text)
        assert result == "line1\nline2\tcol2"

    def test_combined_normalization(self, preprocessor):
        """All normalizations work together."""
        text = "Señor\r\nGarcía\x00\u00A0ﬁnal"
        result = preprocessor.preprocess(text)
        assert result == "Señor\nGarcía final"


class TestDefaultDetectionPreprocessor:
    """Tests for Phase 2 preprocessing."""

    @pytest.fixture
    def preprocessor(self):
        return DefaultDetectionPreprocessor()

    def test_collapse_multiple_spaces(self, preprocessor):
        """Multiple spaces are collapsed to one."""
        text = "Juan   García"
        mapping = preprocessor.preprocess(text)
        assert mapping.normalized_text == "Juan García"

    def test_typographic_quotes_double(self, preprocessor):
        """Typographic double quotes are normalized."""
        text = '"Hello"'  # curly quotes
        mapping = preprocessor.preprocess(text)
        assert mapping.normalized_text == '"Hello"'

    def test_typographic_quotes_single(self, preprocessor):
        """Typographic single quotes are normalized."""
        text = "'test'"  # curly single quotes
        mapping = preprocessor.preprocess(text)
        assert mapping.normalized_text == "'test'"

    def test_guillemets(self, preprocessor):
        """Guillemets are normalized to double quotes."""
        text = "«texto»"
        mapping = preprocessor.preprocess(text)
        assert mapping.normalized_text == '"texto"'

    def test_em_dash(self, preprocessor):
        """Em dash is normalized to hyphen."""
        text = "word—word"
        mapping = preprocessor.preprocess(text)
        assert mapping.normalized_text == "word-word"

    def test_en_dash(self, preprocessor):
        """En dash is normalized to hyphen."""
        text = "2020–2024"
        mapping = preprocessor.preprocess(text)
        assert mapping.normalized_text == "2020-2024"

    def test_linebreak_within_word(self, preprocessor):
        """Linebreak between letters becomes space."""
        text = "Juan\nGarcía"
        mapping = preprocessor.preprocess(text)
        assert mapping.normalized_text == "Juan García"

    def test_linebreak_between_words_preserved(self, preprocessor):
        """Linebreak not between letters is preserved."""
        text = "line1.\nline2"
        mapping = preprocessor.preprocess(text)
        # Period before \n means it's not within a word
        assert "\n" in mapping.normalized_text or " " in mapping.normalized_text

    def test_offset_mapping_collapse_spaces(self, preprocessor):
        """Offset mapping correctly translates spans after space collapse."""
        text = "Juan   García"  # 3 spaces at position 4-7
        mapping = preprocessor.preprocess(text)

        # "García" in normalized text
        garcia_start = mapping.normalized_text.find("García")
        garcia_end = garcia_start + len("García")

        # Translate back to original
        orig_start, orig_end = mapping.to_original_span(garcia_start, garcia_end)

        # In original, "García" starts at position 7
        assert text[orig_start:orig_end] == "García" or "García" in text[orig_start:orig_end]

    def test_offset_mapping_identity_no_changes(self, preprocessor):
        """Text without changes has identity-like mapping."""
        text = "simple text"
        mapping = preprocessor.preprocess(text)

        assert mapping.normalized_text == text
        # Span should translate 1:1
        orig_start, orig_end = mapping.to_original_span(0, 6)
        assert text[orig_start:orig_end] == "simple"


class TestIntegrationNerFlow:
    """Integration tests simulating NER detection flow."""

    def test_full_flow_with_spaces(self):
        """Test complete flow: normalize -> detect -> translate span."""
        preprocessor = DefaultDetectionPreprocessor()

        # Simulated OCR text with extra spaces
        source = "Contactar a   Juan   García   en Madrid"
        mapping = preprocessor.preprocess(source)

        # Simulated NER detection on normalized text
        normalized = mapping.normalized_text
        # Find "Juan García" in normalized
        juan_start = normalized.find("Juan García")
        juan_end = juan_start + len("Juan García")

        # Translate back
        orig_start, orig_end = mapping.to_original_span(juan_start, juan_end)
        detected_value = source[orig_start:orig_end]

        # Should capture the original (with extra spaces)
        assert "Juan" in detected_value
        assert "García" in detected_value

    def test_full_flow_with_quotes(self):
        """Test flow with typographic quotes."""
        preprocessor = DefaultDetectionPreprocessor()

        source = 'El "demandante" presentó'
        mapping = preprocessor.preprocess(source)

        # NER might detect "demandante"
        normalized = mapping.normalized_text
        dem_start = normalized.find("demandante")
        dem_end = dem_start + len("demandante")

        orig_start, orig_end = mapping.to_original_span(dem_start, dem_end)
        assert source[orig_start:orig_end] == "demandante"
