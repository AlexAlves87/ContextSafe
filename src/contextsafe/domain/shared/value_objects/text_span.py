"""
TextSpan value object.

Represents a span of text in a document with start and end positions.

Traceability:
- Standard: consolidated_standards.yaml#factories.value_objects.TextSpan
- Invariants: INV-006 (end > start), INV-007 (start >= 0)
- Bounded Context: BC-002 (EntityDetection)
"""
from __future__ import annotations

from dataclasses import dataclass

from contextsafe.domain.shared.errors import InvalidSpanError
from contextsafe.domain.shared.types import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class TextSpan:
    """
    Value object representing a text span in a document.

    A span has:
    - start: Starting character position (0-indexed)
    - end: Ending character position (exclusive)
    - text: The actual text content in the span

    Invariants: INV-006 (end > start), INV-007 (start >= 0)
    """

    start: int
    end: int
    text: str

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError(f"Start position must be non-negative, got {self.start}")
        if self.end <= self.start:
            raise ValueError(f"End must be greater than start, got start={self.start} end={self.end}")

    @classmethod
    def create(
        cls, start: int, end: int, text: str
    ) -> Result[TextSpan, InvalidSpanError]:
        """
        Create a validated TextSpan.

        Args:
            start: Starting position (0-indexed, inclusive)
            end: Ending position (exclusive)
            text: The text content

        Returns:
            Ok[TextSpan] if valid, Err[InvalidSpanError] if invalid
        """
        if start < 0:
            return Err(InvalidSpanError.create(start, end, "Start must be >= 0"))

        if end <= start:
            return Err(InvalidSpanError.create(start, end, "End must be > start"))

        expected_length = end - start
        if len(text) != expected_length:
            return Err(
                InvalidSpanError.create(
                    start, end, f"Text length {len(text)} != span length {expected_length}"
                )
            )

        return Ok(cls(start=start, end=end, text=text))

    @property
    def length(self) -> int:
        """Get the length of the span."""
        return self.end - self.start

    def contains(self, position: int) -> bool:
        """Check if position is within this span."""
        return self.start <= position < self.end

    def overlaps(self, other: TextSpan) -> bool:
        """Check if this span overlaps with another."""
        return self.start < other.end and other.start < self.end

    def shift(self, offset: int) -> Result[TextSpan, InvalidSpanError]:
        """Create a new span shifted by offset."""
        return TextSpan.create(self.start + offset, self.end + offset, self.text)

    def __str__(self) -> str:
        """String representation."""
        return f"[{self.start}:{self.end}] '{self.text}'"

    def __eq__(self, other: object) -> bool:
        """Compare by all fields."""
        if isinstance(other, TextSpan):
            return (
                self.start == other.start
                and self.end == other.end
                and self.text == other.text
            )
        return False

    def __hash__(self) -> int:
        """Hash by all fields."""
        return hash((self.start, self.end, self.text))

    def __lt__(self, other: TextSpan) -> bool:
        """Compare by start position."""
        return self.start < other.start
