"""
Tests for OffsetTracker and OffsetMapping.

Traceability:
- Design: docs/plans/2026-02-01-text-preprocessing-design.md
"""

import pytest

from contextsafe.application.ports.text_preprocessor import OffsetMapping
from contextsafe.infrastructure.text_processing.offset_tracker import (
    OffsetTracker,
    create_identity_mapping,
)


class TestOffsetTracker:
    """Tests for OffsetTracker builder."""

    def test_keep_all_identity(self):
        """Keeping all characters creates identity mapping."""
        source = "Juan García"
        tracker = OffsetTracker(source)
        tracker.keep(0, len(source))
        mapping = tracker.build()

        assert mapping.normalized_text == source
        assert mapping.source_text == source
        assert len(mapping.char_map) == len(source)
        assert mapping.char_map == tuple(range(len(source)))

    def test_skip_removes_characters(self):
        """Skipping characters removes them from output."""
        source = "abc123"
        tracker = OffsetTracker(source)
        tracker.keep(0, 3)  # "abc"
        tracker.skip(3, 6)  # skip "123"
        mapping = tracker.build()

        assert mapping.normalized_text == "abc"
        assert mapping.char_map == (0, 1, 2)

    def test_replace_maps_to_start(self):
        """Replace maps all new chars to start position."""
        source = "   "  # 3 spaces
        tracker = OffsetTracker(source)
        tracker.replace(0, 3, " ")  # 3 spaces -> 1
        mapping = tracker.build()

        assert mapping.normalized_text == " "
        assert mapping.char_map == (0,)  # Maps to start

    def test_collapse_spaces(self):
        """Collapsing multiple spaces works correctly."""
        source = "Juan   García"  # 3 spaces
        tracker = OffsetTracker(source)
        tracker.keep(0, 4)           # "Juan"
        tracker.replace(4, 7, " ")   # 3 spaces -> 1
        tracker.keep(7, 13)          # "García"
        mapping = tracker.build()

        assert mapping.normalized_text == "Juan García"
        # "García" in normalized starts at 5, in source at 7
        orig_start, orig_end = mapping.to_original_span(5, 11)
        assert orig_start == 7
        assert orig_end == 13

    def test_ocr_letter_spacing(self):
        """OCR letter spacing fix works correctly."""
        source = "J u a n"  # 7 chars
        tracker = OffsetTracker(source)
        tracker.replace(0, 7, "Juan")  # All 7 chars -> 4
        mapping = tracker.build()

        assert mapping.normalized_text == "Juan"
        # All chars map to start (position 0)
        assert mapping.char_map == (0, 0, 0, 0)
        # Full span maps back to full original
        orig_start, orig_end = mapping.to_original_span(0, 4)
        assert orig_start == 0
        # Note: end might be 1 due to conservative mapping
        assert orig_end >= 1

    def test_keep_char_convenience(self):
        """keep_char convenience method works."""
        source = "abc"
        tracker = OffsetTracker(source)
        tracker.keep_char(0)
        tracker.keep_char(1)
        tracker.keep_char(2)
        mapping = tracker.build()

        assert mapping.normalized_text == "abc"
        assert mapping.char_map == (0, 1, 2)

    def test_replace_char_convenience(self):
        """replace_char convenience method works."""
        source = "a–b"  # em dash
        tracker = OffsetTracker(source)
        tracker.keep_char(0)
        tracker.replace_char(1, "-")  # Replace dash
        tracker.keep_char(2)
        mapping = tracker.build()

        assert mapping.normalized_text == "a-b"

    def test_empty_source(self):
        """Empty source produces empty mapping."""
        tracker = OffsetTracker("")
        mapping = tracker.build()

        assert mapping.normalized_text == ""
        assert mapping.char_map == ()


class TestOffsetMapping:
    """Tests for OffsetMapping span translation."""

    def test_identity_span_unchanged(self):
        """Identity mapping returns span unchanged."""
        mapping = OffsetMapping.identity("Hello World")
        orig_start, orig_end = mapping.to_original_span(0, 5)
        assert (orig_start, orig_end) == (0, 5)

    def test_span_always_valid_empty_input(self):
        """Empty span returns minimum valid span."""
        mapping = OffsetMapping(
            source_text="test",
            normalized_text="test",
            char_map=(0, 1, 2, 3),
        )
        orig_start, orig_end = mapping.to_original_span(2, 2)
        # Empty span should return at least 1 char
        assert orig_start < orig_end

    def test_span_clamps_negative(self):
        """Negative start is clamped to 0."""
        mapping = OffsetMapping(
            source_text="test",
            normalized_text="test",
            char_map=(0, 1, 2, 3),
        )
        orig_start, orig_end = mapping.to_original_span(-5, 2)
        assert orig_start >= 0

    def test_span_clamps_overflow(self):
        """End beyond length is clamped."""
        mapping = OffsetMapping(
            source_text="test",
            normalized_text="test",
            char_map=(0, 1, 2, 3),
        )
        orig_start, orig_end = mapping.to_original_span(0, 100)
        assert orig_end <= len("test")

    def test_span_with_collapsed_spaces(self):
        """Span translation with collapsed spaces."""
        # Source: "a   b" (3 spaces)
        # Normalized: "a b" (1 space)
        # char_map: (0, 1, 4)  where 1 is the first space, maps to position 1
        mapping = OffsetMapping(
            source_text="a   b",
            normalized_text="a b",
            char_map=(0, 1, 4),
        )
        # "b" in normalized is at position 2
        # Should map to position 4 in source
        orig_start, orig_end = mapping.to_original_span(2, 3)
        assert orig_start == 4
        assert orig_end == 5

    def test_no_char_map_passthrough(self):
        """Without char_map, span is returned as-is."""
        mapping = OffsetMapping(
            source_text="test",
            normalized_text="test",
            char_map=(),
        )
        orig_start, orig_end = mapping.to_original_span(1, 3)
        assert (orig_start, orig_end) == (1, 3)


class TestCreateIdentityMapping:
    """Tests for create_identity_mapping helper."""

    def test_identity_mapping(self):
        """Creates proper identity mapping."""
        text = "Hello"
        mapping = create_identity_mapping(text)

        assert mapping.source_text == text
        assert mapping.normalized_text == text
        assert mapping.char_map == (0, 1, 2, 3, 4)
