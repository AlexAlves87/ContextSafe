"""
ConfidenceScore value object.

Represents the confidence level of a PII detection.

Traceability:
- Standard: consolidated_standards.yaml#factories.value_objects.ConfidenceScore
- Invariant: INV-005 (0.0 <= value <= 1.0)
- Bounded Context: BC-002 (EntityDetection)
"""
from __future__ import annotations

from dataclasses import dataclass

from contextsafe.domain.shared.errors import InvalidScoreError
from contextsafe.domain.shared.types import Err, Ok, Result


# Default threshold for requiring manual review
REVIEW_THRESHOLD = 0.7


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    """
    Value object representing detection confidence.

    Score is between 0.0 (no confidence) and 1.0 (full confidence).
    Detections below threshold require manual review.

    Invariant: INV-005 (0.0 <= value <= 1.0)
    """

    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(f"Score must be in [0.0, 1.0], got {self.value}")

    @classmethod
    def create(cls, value: float) -> Result[ConfidenceScore, InvalidScoreError]:
        """
        Create a validated ConfidenceScore.

        Args:
            value: Confidence value between 0.0 and 1.0

        Returns:
            Ok[ConfidenceScore] if valid, Err[InvalidScoreError] if invalid
        """
        if value < 0.0 or value > 1.0:
            return Err(InvalidScoreError.create(value))

        return Ok(cls(value=value))

    @classmethod
    def full(cls) -> ConfidenceScore:
        """Create a full confidence score (1.0)."""
        return cls(value=1.0)

    @classmethod
    def zero(cls) -> ConfidenceScore:
        """Create a zero confidence score (0.0)."""
        return cls(value=0.0)

    @property
    def needs_review(self) -> bool:
        """Check if this score is below the review threshold."""
        return self.value < REVIEW_THRESHOLD

    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence score (>= 0.9)."""
        return self.value >= 0.9

    @property
    def percentage(self) -> int:
        """Get the score as a percentage (0-100)."""
        return int(self.value * 100)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.percentage}%"

    def __eq__(self, other: object) -> bool:
        """Compare by value."""
        if isinstance(other, ConfidenceScore):
            return abs(self.value - other.value) < 0.0001
        return False

    def __hash__(self) -> int:
        """Hash by rounded value."""
        return hash(round(self.value, 4))

    def __lt__(self, other: ConfidenceScore) -> bool:
        """Compare scores."""
        return self.value < other.value

    def __le__(self, other: ConfidenceScore) -> bool:
        """Compare scores."""
        return self.value <= other.value

    def __gt__(self, other: ConfidenceScore) -> bool:
        """Compare scores."""
        return self.value > other.value

    def __ge__(self, other: ConfidenceScore) -> bool:
        """Compare scores."""
        return self.value >= other.value
