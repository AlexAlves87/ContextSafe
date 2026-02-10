"""
Confidence zone classification for entity triage.

Classifies detected entities into three review zones:
- GREEN: High confidence, quick verification
- AMBER: Medium confidence, critical review required
- RED: Low confidence / potential false negatives, must confirm non-PII

Traceability:
- Requirement: AI Act Art. 14 (human oversight for high-risk systems)
- Design: Propuesta Mejoras Arquitectónicas v2.1, Módulo B §3.3
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from contextsafe.domain.shared.value_objects.confidence_score import (
    ConfidenceScore,
)
from contextsafe.domain.shared.value_objects.pii_category import (
    PiiCategory,
    PiiCategoryEnum,
)

# Zone thresholds
GREEN_THRESHOLD = 0.85
AMBER_THRESHOLD = 0.40

# Categories where checksum validation is possible
CHECKSUM_CATEGORIES = frozenset({
    PiiCategoryEnum.DNI_NIE,
    PiiCategoryEnum.IBAN,
    PiiCategoryEnum.SOCIAL_SECURITY,
    PiiCategoryEnum.CREDIT_CARD,
    PiiCategoryEnum.NIG,
})


class ConfidenceZoneEnum(str, Enum):
    """Triage zones for entity review."""

    GREEN = "GREEN"    # Confidence > 0.85 AND valid checksum (if applicable)
    AMBER = "AMBER"    # Confidence 0.40-0.85 OR invalid checksum
    RED = "RED"        # Confidence < 0.40 (potential false negatives)


@dataclass(frozen=True, slots=True)
class ConfidenceZone:
    """
    Value object representing a detection's review zone.

    Combines confidence score with optional checksum validation
    to determine the appropriate level of human review.
    """

    zone: ConfidenceZoneEnum
    reason: str

    @classmethod
    def classify(
        cls,
        confidence: ConfidenceScore,
        category: PiiCategory,
        checksum_valid: Optional[bool] = None,
    ) -> ConfidenceZone:
        """
        Classify a detection into a review zone.

        Args:
            confidence: Detection confidence score.
            category: PII category of the detection.
            checksum_valid: True if checksum verified, False if invalid,
                           None if not applicable.

        Returns:
            ConfidenceZone with zone and reason.
        """
        has_checksum_category = category.value in CHECKSUM_CATEGORIES

        # RED: Low confidence
        if confidence.value < AMBER_THRESHOLD:
            return cls(
                zone=ConfidenceZoneEnum.RED,
                reason=f"Low confidence ({confidence})",
            )

        # AMBER: Medium confidence OR checksum failure
        if confidence.value < GREEN_THRESHOLD:
            return cls(
                zone=ConfidenceZoneEnum.AMBER,
                reason=f"Medium confidence ({confidence})",
            )

        # High confidence but invalid checksum → AMBER
        if has_checksum_category and checksum_valid is False:
            return cls(
                zone=ConfidenceZoneEnum.AMBER,
                reason=f"High confidence but invalid checksum ({category})",
            )

        # GREEN: High confidence (and valid checksum if applicable)
        return cls(
            zone=ConfidenceZoneEnum.GREEN,
            reason=f"High confidence ({confidence})",
        )

    @property
    def requires_individual_review(self) -> bool:
        """True if entity must be individually reviewed (AMBER/RED)."""
        return self.zone != ConfidenceZoneEnum.GREEN

    @property
    def is_critical(self) -> bool:
        """True if entity is in the red zone."""
        return self.zone == ConfidenceZoneEnum.RED

    def __str__(self) -> str:
        return f"{self.zone.value}: {self.reason}"
