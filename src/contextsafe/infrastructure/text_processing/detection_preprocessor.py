"""
DetectionPreprocessor implementation.

Phase 2 normalization: temporary, for NER detection only.

Traceability:
- Design: docs/plans/2026-02-01-text-preprocessing-design.md
"""
from __future__ import annotations

from contextsafe.application.ports.text_preprocessor import (
    DetectionPreprocessor,
    OffsetMapping,
)
from contextsafe.domain.document_processing.services import text_normalization as norm
from contextsafe.infrastructure.text_processing.offset_tracker import OffsetTracker


class DefaultDetectionPreprocessor(DetectionPreprocessor):
    """
    Default implementation of Phase 2 preprocessing.

    Applies normalization that:
    - MAY change text length
    - IS temporary (only for NER, not stored)
    - Tracks offsets for span translation back to original

    Operations:
    - Collapse multiple spaces
    - Normalize typographic quotes
    - Normalize typographic dashes
    - Fix OCR letter spacing (J u a n -> Juan)
    - Fix OCR linebreaks within words
    """

    def preprocess(self, text: str) -> OffsetMapping:
        """
        Apply Phase 2 normalization with offset tracking.

        Args:
            text: Text (already Phase 1 normalized)

        Returns:
            OffsetMapping with normalized text and position map
        """
        tracker = OffsetTracker(text)
        pos = 0
        length = len(text)

        while pos < length:
            char = text[pos]

            # Rule 1: Collapse multiple spaces -> single space
            if char == " ":
                space_start = pos
                while pos < length and text[pos] == " ":
                    pos += 1
                # Multiple spaces -> 1 space
                tracker.replace(space_start, pos, " ")
                continue

            # Rule 2: Normalize typographic quotes
            if char in norm.QUOTE_MAP:
                tracker.replace_char(pos, norm.QUOTE_MAP[char])
                pos += 1
                continue

            # Rule 3: Normalize typographic dashes
            if char in "–—−\u2010\u2011\u2012\u2013\u2014\u2015":
                tracker.replace_char(pos, "-")
                pos += 1
                continue

            # Rule 4: Fix linebreak within word (letter\nletter -> letter letter)
            if char == "\n" and pos > 0 and pos < length - 1:
                prev_char = text[pos - 1]
                next_char = text[pos + 1]
                if prev_char.isalpha() and next_char.isalpha():
                    tracker.replace_char(pos, " ")
                    pos += 1
                    continue

            # Rule 5: Check for OCR letter spacing (e.g., "J u a n")
            # Look ahead for pattern: letter space letter space letter...
            if char.isalpha() and pos + 2 < length:
                if text[pos + 1] == " " and text[pos + 2].isalpha():
                    # Check if this is a sequence of spaced letters
                    spaced_letters = self._find_spaced_letters(text, pos)
                    if spaced_letters and len(spaced_letters) >= 3:
                        # Join the letters
                        end_pos = pos + (len(spaced_letters) * 2) - 1
                        joined = "".join(spaced_letters)
                        tracker.replace(pos, end_pos, joined)
                        pos = end_pos
                        continue

            # Default: keep character unchanged
            tracker.keep_char(pos)
            pos += 1

        return tracker.build()

    def _find_spaced_letters(self, text: str, start: int) -> list[str] | None:
        """
        Find sequence of single letters separated by spaces.

        Pattern: "J u a n" -> ["J", "u", "a", "n"]

        Only returns if:
        - At least 3 letters in sequence
        - All lowercase (to avoid breaking "A B C" acronyms)

        Args:
            text: Source text
            start: Starting position

        Returns:
            List of letters if pattern found, None otherwise
        """
        letters = []
        pos = start
        length = len(text)

        while pos < length:
            char = text[pos]

            if char.isalpha():
                letters.append(char)
                pos += 1

                # Check for space followed by letter
                if pos < length and text[pos] == " ":
                    if pos + 1 < length and text[pos + 1].isalpha():
                        pos += 1  # Skip space, continue
                    else:
                        break  # End of sequence
                else:
                    break
            else:
                break

        # Only return if 3+ letters and all lowercase
        # (to avoid breaking acronyms like "A B C")
        if len(letters) >= 3:
            # Check if mostly lowercase (allow first letter uppercase)
            lowercase_count = sum(1 for c in letters if c.islower())
            if lowercase_count >= len(letters) - 1:
                return letters

        return None
