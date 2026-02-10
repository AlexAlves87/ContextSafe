"""
AnonymizationLevel value object.

Defines the level of anonymization to apply.

Traceability:
- Standard: consolidated_standards.yaml#vocabulary.anonymization_levels
- Source: controlled_vocabulary.yaml#domain_vocabulary.anonymization_levels
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet

from contextsafe.domain.shared.errors import InvalidLevelError
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects.pii_category import PiiCategoryEnum


class AnonymizationLevelEnum(str, Enum):
    """Enumeration of anonymization levels."""

    BASIC = "BASIC"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


# Categories included in each level
LEVEL_CATEGORIES: dict[AnonymizationLevelEnum, FrozenSet[PiiCategoryEnum]] = {
    AnonymizationLevelEnum.BASIC: frozenset({
        PiiCategoryEnum.DNI_NIE,
        PiiCategoryEnum.PASSPORT,
        PiiCategoryEnum.PHONE,
        PiiCategoryEnum.BANK_ACCOUNT,
        PiiCategoryEnum.CREDIT_CARD,
        PiiCategoryEnum.SOCIAL_SECURITY,
    }),
    AnonymizationLevelEnum.INTERMEDIATE: frozenset({
        PiiCategoryEnum.PERSON_NAME,
        PiiCategoryEnum.DNI_NIE,
        PiiCategoryEnum.PASSPORT,
        PiiCategoryEnum.PHONE,
        PiiCategoryEnum.EMAIL,
        PiiCategoryEnum.BANK_ACCOUNT,
        PiiCategoryEnum.CREDIT_CARD,
        PiiCategoryEnum.DATE,
        PiiCategoryEnum.SOCIAL_SECURITY,
        PiiCategoryEnum.MEDICAL_RECORD,
    }),
    AnonymizationLevelEnum.ADVANCED: frozenset({
        PiiCategoryEnum.PERSON_NAME,
        PiiCategoryEnum.ORGANIZATION,
        PiiCategoryEnum.ADDRESS,
        PiiCategoryEnum.DNI_NIE,
        PiiCategoryEnum.PASSPORT,
        PiiCategoryEnum.PHONE,
        PiiCategoryEnum.EMAIL,
        PiiCategoryEnum.BANK_ACCOUNT,
        PiiCategoryEnum.CREDIT_CARD,
        PiiCategoryEnum.DATE,
        PiiCategoryEnum.MEDICAL_RECORD,
        PiiCategoryEnum.LICENSE_PLATE,
        PiiCategoryEnum.SOCIAL_SECURITY,
    }),
}


@dataclass(frozen=True, slots=True)
class AnonymizationLevel:
    """
    Value object representing an anonymization level.

    Each level includes specific PII categories to anonymize.
    """

    value: AnonymizationLevelEnum

    @classmethod
    def from_string(cls, value: str) -> Result[AnonymizationLevel, InvalidLevelError]:
        """
        Create an AnonymizationLevel from string.

        Args:
            value: Level name (BASIC, INTERMEDIATE, ADVANCED)

        Returns:
            Ok[AnonymizationLevel] if valid, Err[InvalidLevelError] if invalid
        """
        normalized = value.upper().strip()

        try:
            level_enum = AnonymizationLevelEnum(normalized)
            return Ok(cls(value=level_enum))
        except ValueError:
            return Err(InvalidLevelError.create(value))

    @property
    def categories(self) -> FrozenSet[PiiCategoryEnum]:
        """Get the PII categories included in this level."""
        return LEVEL_CATEGORIES.get(self.value, frozenset())

    @property
    def removes_metadata(self) -> bool:
        """Check if this level removes document metadata."""
        return self.value == AnonymizationLevelEnum.ADVANCED

    @property
    def requires_audit(self) -> bool:
        """Check if this level requires audit logging."""
        return self.value in {
            AnonymizationLevelEnum.INTERMEDIATE,
            AnonymizationLevelEnum.ADVANCED,
        }

    def includes_category(self, category: PiiCategoryEnum) -> bool:
        """Check if this level includes the given category."""
        return category in self.categories

    def __str__(self) -> str:
        """String representation."""
        return self.value.value

    def __eq__(self, other: object) -> bool:
        """Compare by value."""
        if isinstance(other, AnonymizationLevel):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Hash by value."""
        return hash(self.value)


# Convenience constants
BASIC = AnonymizationLevel(AnonymizationLevelEnum.BASIC)
INTERMEDIATE = AnonymizationLevel(AnonymizationLevelEnum.INTERMEDIATE)
ADVANCED = AnonymizationLevel(AnonymizationLevelEnum.ADVANCED)
