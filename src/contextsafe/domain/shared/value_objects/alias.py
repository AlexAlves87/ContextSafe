"""
Alias value object.

Represents an alias used to replace PII in documents.

Traceability:
- Standard: consolidated_standards.yaml#factories.value_objects.Alias
- Bounded Context: BC-003 (Anonymization)
- Business Rule: BR-002 (Alias Consistency)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from contextsafe.domain.shared.errors import InvalidAliasError
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects.pii_category import (
    ALIAS_PATTERNS,
    PiiCategory,
    PiiCategoryEnum,
)


# Pattern to validate alias format (auto-generated)
ALIAS_PATTERN = re.compile(r"^[A-Za-z]+_\d+$")

# Pattern for custom aliases (user-defined): alphanumeric, spaces, underscores, hyphens
CUSTOM_ALIAS_PATTERN = re.compile(r"^[\w\s\-]+$", re.UNICODE)


@dataclass(frozen=True, slots=True)
class Alias:
    """
    Value object representing an alias for PII replacement.

    Aliases are:
    - Immutable
    - Category-specific (follow category patterns)
    - Unique within a project (enforced by Glossary)
    - Must not leak PII
    """

    value: str
    category: PiiCategory

    @classmethod
    def create(
        cls, value: str, category: PiiCategory
    ) -> Result[Alias, InvalidAliasError]:
        """
        Create a validated Alias.

        Args:
            value: The alias string (e.g., "Persona_1")
            category: The PII category this alias represents

        Returns:
            Ok[Alias] if valid, Err[InvalidAliasError] if invalid
        """
        if not value or not value.strip():
            return Err(InvalidAliasError.create("", "Alias cannot be empty"))

        # Validate format matches pattern
        if not ALIAS_PATTERN.match(value):
            return Err(
                InvalidAliasError.create(
                    value, "Alias must match pattern '{Prefix}_{Number}'"
                )
            )

        # Validate prefix matches category
        expected_prefix = ALIAS_PATTERNS.get(category.value, "Alias").split("_")[0]
        actual_prefix = value.split("_")[0]

        if actual_prefix != expected_prefix:
            return Err(
                InvalidAliasError.create(
                    value,
                    f"Alias prefix '{actual_prefix}' does not match category "
                    f"'{category}' (expected '{expected_prefix}')",
                )
            )

        return Ok(cls(value=value, category=category))

    @classmethod
    def create_custom(
        cls, value: str, category: PiiCategory
    ) -> Result[Alias, InvalidAliasError]:
        """
        Create a custom user-defined alias.

        Custom aliases are more permissive than auto-generated ones.
        They can be descriptive names like "Juez", "Demandante", etc.

        Args:
            value: The custom alias string
            category: The PII category this alias represents

        Returns:
            Ok[Alias] if valid, Err[InvalidAliasError] if invalid

        Traceability:
            - BR-002 Evolution: Aliases mutable under explicit user demand
        """
        if not value or not value.strip():
            return Err(InvalidAliasError.create("", "Alias cannot be empty"))

        cleaned_value = value.strip()

        # Validate custom alias format (permissive but safe)
        if not CUSTOM_ALIAS_PATTERN.match(cleaned_value):
            return Err(
                InvalidAliasError.create(
                    value,
                    "Custom alias can only contain letters, numbers, spaces, "
                    "underscores, and hyphens",
                )
            )

        # Ensure alias is not too long
        if len(cleaned_value) > 100:
            return Err(
                InvalidAliasError.create(value, "Alias cannot exceed 100 characters")
            )

        # Ensure alias doesn't look like PII (basic check)
        if "@" in cleaned_value or cleaned_value.count(".") > 1:
            return Err(
                InvalidAliasError.create(
                    value, "Alias appears to contain PII (email pattern detected)"
                )
            )

        return Ok(cls(value=cleaned_value, category=category))

    @classmethod
    def generate(cls, category: PiiCategory, index: int) -> Result[Alias, InvalidAliasError]:
        """
        Generate an alias for a category with given index.

        Args:
            category: The PII category
            index: The unique index within the category

        Returns:
            Ok[Alias] with the generated alias
        """
        if index < 1:
            return Err(InvalidAliasError.create(str(index), "Index must be >= 1"))

        value = category.generate_alias(index)
        return cls.create(value, category)

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Compare by value and category."""
        if isinstance(other, Alias):
            return self.value == other.value and self.category == other.category
        return False

    def __hash__(self) -> int:
        """Hash by value."""
        return hash((self.value, self.category))
