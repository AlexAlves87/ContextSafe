"""
OffsetTracker for building OffsetMapping during normalization.

Tracks the relationship between source text positions and normalized
text positions as transformations are applied.

Traceability:
- Design: docs/plans/2026-02-01-text-preprocessing-design.md
"""
from __future__ import annotations

from contextsafe.application.ports.text_preprocessor import OffsetMapping


class OffsetTracker:
    """
    Builder for constructing OffsetMapping during normalization.

    Tracks how each character in the normalized text maps back to
    the source text. Supports three operations:
    - keep: copy characters unchanged
    - skip: remove characters from output
    - replace: replace a range with different text

    Usage:
        tracker = OffsetTracker(source_text)
        tracker.keep(0, 5)           # Copy chars 0-5 unchanged
        tracker.skip(5, 8)           # Skip chars 5-8 (deleted)
        tracker.replace(8, 15, "X")  # Replace chars 8-15 with "X"
        mapping = tracker.build()
    """

    def __init__(self, source_text: str):
        """
        Initialize tracker with source text.

        Args:
            source_text: The original text to normalize
        """
        self._source = source_text
        self._normalized_chars: list[str] = []
        self._char_map: list[int] = []

    def keep(self, start: int, end: int) -> None:
        """
        Keep characters from source (copied to normalized unchanged).

        Args:
            start: Start position in source (inclusive)
            end: End position in source (exclusive)
        """
        for i in range(start, min(end, len(self._source))):
            self._normalized_chars.append(self._source[i])
            self._char_map.append(i)

    def skip(self, start: int, end: int) -> None:
        """
        Skip characters from source (not included in normalized).

        Args:
            start: Start position in source (inclusive)
            end: End position in source (exclusive)
        """
        # No añadimos nada al output
        pass

    def replace(self, start: int, end: int, replacement: str) -> None:
        """
        Replace characters [start:end] with replacement string.

        DECISIÓN DE DISEÑO: Todos los chars del replacement mapean a `start`.

        Esto es CONSERVADOR (expansión hacia el inicio):
        - Garantiza que el span original siempre incluya el contexto
        - Puede sobre-incluir caracteres hacia la izquierda
        - Alternativa (mapear al centro) daría spans más precisos
          pero con riesgo de cortar contexto

        Para este caso de uso (NER), preferimos sobre-incluir a perder texto.

        Args:
            start: Start position in source (inclusive)
            end: End position in source (exclusive)
            replacement: String to insert instead
        """
        for char in replacement:
            self._normalized_chars.append(char)
            self._char_map.append(start)

    def keep_char(self, pos: int) -> None:
        """
        Keep a single character from source.

        Convenience method for character-by-character processing.

        Args:
            pos: Position in source
        """
        if 0 <= pos < len(self._source):
            self._normalized_chars.append(self._source[pos])
            self._char_map.append(pos)

    def replace_char(self, pos: int, replacement: str) -> None:
        """
        Replace a single character with replacement string.

        Args:
            pos: Position in source
            replacement: String to insert instead
        """
        for char in replacement:
            self._normalized_chars.append(char)
            self._char_map.append(pos)

    def skip_char(self, pos: int) -> None:
        """
        Skip a single character from source.

        Args:
            pos: Position in source
        """
        pass

    @property
    def current_position(self) -> int:
        """Get current position in normalized text."""
        return len(self._normalized_chars)

    def build(self) -> OffsetMapping:
        """
        Build the final OffsetMapping.

        Returns:
            OffsetMapping with source, normalized text, and char map
        """
        return OffsetMapping(
            source_text=self._source,
            normalized_text="".join(self._normalized_chars),
            char_map=tuple(self._char_map),
        )


def create_identity_mapping(text: str) -> OffsetMapping:
    """
    Create an identity mapping (no changes).

    Convenience function for when no normalization is needed.

    Args:
        text: The text

    Returns:
        OffsetMapping where normalized == source
    """
    return OffsetMapping.identity(text)
