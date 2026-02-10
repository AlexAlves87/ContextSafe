"""
Masking strategy for Level 1 (BASIC) anonymization.

Replaces PII with asterisks proportional to original length.
No glossary entries are created - this is irreversible by design.

Example:
    "Pepito Pérez" → "****** ******"
    "12345678A" → "*********"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contextsafe.infrastructure.nlp.strategies.base import (
    AnonymizationStrategy,
    ReplacementResult,
)

if TYPE_CHECKING:
    from contextsafe.application.ports.ner_service import NerDetection


class MaskingStrategy(AnonymizationStrategy):
    """
    Level 1: Ocultación básica (masking).

    Characteristics:
    - Replaces with asterisks
    - No glossary entries (irreversible)
    - Minimum cost (no LLM, no mapping)
    - Best for: quick sharing, zero risk

    The mask preserves word structure by replacing each word
    with asterisks of the same length.
    """

    def __init__(
        self,
        mask_char: str = "*",
        min_length: int = 5,
        preserve_word_structure: bool = True,
    ):
        """
        Initialize masking strategy.

        Args:
            mask_char: Character to use for masking (default: *)
            min_length: Minimum mask length to prevent length inference
            preserve_word_structure: If True, mask each word separately
        """
        self._mask_char = mask_char
        self._min_length = min_length
        self._preserve_word_structure = preserve_word_structure

    async def generate_replacement(
        self,
        detection: "NerDetection",
        project_id: str,  # Ignored - masking doesn't need project context
    ) -> ReplacementResult:
        """
        Generate asterisk mask for detection.

        The mask strategy:
        1. If preserve_word_structure: mask each word separately
           "Juan Pérez" → "**** *****"
        2. Otherwise: single mask block
           "Juan Pérez" → "**********"
        3. Minimum length applied to prevent length inference
        """
        original = detection.value

        if self._preserve_word_structure:
            # Mask each word separately to preserve structure
            words = original.split()
            masked_words = []
            for word in words:
                mask_len = max(len(word), self._min_length)
                masked_words.append(self._mask_char * mask_len)
            replacement = " ".join(masked_words)
        else:
            # Single mask block
            mask_len = max(len(original), self._min_length)
            replacement = self._mask_char * mask_len

        return ReplacementResult(
            original=original,
            replacement=replacement,
            category=detection.category.value,
            glossary_entry=None,  # Level 1 does NOT create glossary entries
        )

    @property
    def creates_glossary_entries(self) -> bool:
        """Masking does not create glossary entries - irreversible by design."""
        return False
