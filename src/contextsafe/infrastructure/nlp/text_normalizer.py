"""
Text normalizer for NER preprocessing.

Applies Unicode normalization optimized for Spanish legal documents.
This is the production version integrated into the NER pipeline.

Based on: ml/docs/reports/2026-02-03_1730_investigacion_text_normalization.md
Standalone tests: ml/scripts/preprocess/text_normalizer.py
"""

import re
import unicodedata

from contextsafe.application.ports.text_preprocessor import OffsetMapping
from contextsafe.infrastructure.text_processing.offset_tracker import OffsetTracker


# Zero-width and invisible characters to remove
ZERO_WIDTH_CHARS = "".join(
    chr(c) for c in list(range(0x200B, 0x2010)) + list(range(0x2060, 0x2070)) + [0xFEFF]
)
ZERO_WIDTH_PATTERN = re.compile(f"[{re.escape(ZERO_WIDTH_CHARS)}]")

# Cyrillic homoglyphs that look identical to Latin
HOMOGLYPHS = {
    # Uppercase
    "А": "A",  # Cyrillic A -> Latin A
    "В": "B",  # Cyrillic B -> Latin B
    "Е": "E",  # Cyrillic E -> Latin E
    "К": "K",  # Cyrillic K -> Latin K
    "М": "M",  # Cyrillic M -> Latin M
    "Н": "H",  # Cyrillic H -> Latin H
    "О": "O",  # Cyrillic O -> Latin O
    "Р": "P",  # Cyrillic P -> Latin P
    "С": "C",  # Cyrillic C -> Latin C
    "Т": "T",  # Cyrillic T -> Latin T
    "Х": "X",  # Cyrillic X -> Latin X
    # Lowercase
    "а": "a",  # Cyrillic a -> Latin a
    "е": "e",  # Cyrillic e -> Latin e
    "о": "o",  # Cyrillic o -> Latin o
    "р": "p",  # Cyrillic p -> Latin p
    "с": "c",  # Cyrillic c -> Latin c
    "у": "y",  # Cyrillic y -> Latin y
    "х": "x",  # Cyrillic x -> Latin x
}

SOFT_HYPHEN = "­"


class TextNormalizer:
    """
    Text normalizer for NER preprocessing in Spanish legal documents.

    Applies:
    - NFKC normalization (fullwidth -> ASCII)
    - Zero-width character removal
    - Homoglyph mapping (Cyrillic -> Latin)
    - Space normalization (NBSP -> space, collapse multiples)
    - Soft hyphen removal

    Does NOT modify:
    - Case (RoBERTa is case-sensitive)
    - Accents (important for Spanish)
    - Legitimate punctuation
    """

    def normalize(self, text: str) -> str:
        """Normalize text for NER processing."""
        return self.normalize_with_mapping(text).normalized_text

    def normalize_with_mapping(self, text: str) -> OffsetMapping:
        """
        Normalize text and return an OffsetMapping to translate spans back.

        Args:
            text: Input text to normalize.

        Returns:
            OffsetMapping with normalized text and source-position tracking.
        """
        if not text:
            return OffsetMapping.identity(text)

        tracker = OffsetTracker(text)
        prev_was_space = False

        for i, ch in enumerate(text):
            if ZERO_WIDTH_PATTERN.match(ch):
                tracker.skip_char(i)
                continue

            nfkc = unicodedata.normalize("NFKC", ch)
            nfkc = "".join(HOMOGLYPHS.get(c, c) for c in nfkc)
            nfkc = nfkc.replace(SOFT_HYPHEN, "")

            if not nfkc:
                tracker.skip_char(i)
                prev_was_space = False
                continue

            if nfkc == " ":
                if prev_was_space:
                    tracker.skip_char(i)
                    continue
                prev_was_space = True
            else:
                prev_was_space = False

            tracker.replace_char(i, nfkc)

        return tracker.build()


# Module-level instance for convenience
_normalizer = TextNormalizer()


def normalize_text(text: str) -> str:
    """
    Convenience function to normalize text.

    Args:
        text: Input text to normalize.

    Returns:
        Normalized text.
    """
    return _normalizer.normalize(text)
