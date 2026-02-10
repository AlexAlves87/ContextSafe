"""
Anonymization service port.

Defines the interface for anonymizing text by replacing PII entities
with aliases while maintaining consistency across a project.

Traceability:
- Contract: CNT-T1-ANONYMIZATION-001
- IMPLEMENTATION_PLAN.md Phase 5
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contextsafe.application.ports.ner_service import NerDetection


@dataclass(frozen=True)
class AnonymizationResult:
    """Result of anonymizing text."""

    original_text: str
    anonymized_text: str
    replacements: list["EntityReplacement"]
    error: str | None = None

    @property
    def success(self) -> bool:
        """Check if anonymization was successful."""
        return self.error is None


@dataclass(frozen=True)
class EntityReplacement:
    """A single entity replacement made during anonymization."""

    category: str
    original_value: str
    alias: str
    start_offset: int
    end_offset: int
    confidence: float


class AnonymizationService(ABC):
    """
    Port for anonymization services.

    Implementations should:
    - Replace detected PII entities with consistent aliases
    - Maintain an alias glossary for consistency within a project
    - Support different anonymization strategies (replace, mask, hash)
    """

    @abstractmethod
    async def anonymize_text(
        self,
        text: str,
        detections: list["NerDetection"],
        project_id: str,
        level: str = "INTERMEDIATE",
    ) -> AnonymizationResult:
        """
        Anonymize text by replacing detected entities.

        The level determines HOW entities are replaced:
        - BASIC: Asterisks (*****) - no glossary
        - INTERMEDIATE: Pseudonyms (Persona_001) - with glossary
        - ADVANCED: Synthetic names (Roberto García) - with glossary

        Args:
            text: Original text to anonymize
            detections: List of detected PII entities
            project_id: Project ID for glossary consistency
            level: Anonymization level (BASIC/INTERMEDIATE/ADVANCED)

        Returns:
            AnonymizationResult with anonymized text and replacements
        """
        ...

    @abstractmethod
    async def get_or_create_alias(
        self,
        category: str,
        original_value: str,
        project_id: str,
        level: str = "INTERMEDIATE",
    ) -> str:
        """
        Get existing alias or create a new one for an entity.

        Maintains consistency: same original value always maps to same alias.

        Args:
            category: PII category (e.g., "PERSON_NAME", "DNI")
            original_value: The original entity text
            project_id: Project ID for glossary scope
            level: Anonymization level (INTERMEDIATE or ADVANCED)
                   - INTERMEDIATE: Numeric aliases for dates (Fecha_001)
                   - ADVANCED: Date shifting for dates

        Returns:
            The alias (existing or newly created)
        """
        ...

    @abstractmethod
    async def get_glossary(
        self,
        project_id: str,
    ) -> dict[str, dict[str, str]]:
        """
        Get the full alias glossary for a project.

        Returns:
            Dict mapping category -> {original_value: alias}
        """
        ...
