"""
Pseudonym strategy for Level 2 (INTERMEDIATE) anonymization.

Replaces PII with consistent aliases like Persona_001, Org_002.
This is the EXISTING behavior - refactored into the strategy pattern.

Example:
    "Pepito Pérez" → "Persona_001"
    "Ibercaja" → "Org_001"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contextsafe.infrastructure.nlp.strategies.base import (
    AnonymizationStrategy,
    ReplacementResult,
)

if TYPE_CHECKING:
    from contextsafe.application.ports.ner_service import NerDetection
    from contextsafe.infrastructure.nlp.anonymization_adapter import (
        InMemoryAnonymizationAdapter,
    )


class PseudonymStrategy(AnonymizationStrategy):
    """
    Level 2: Pseudonimización básica.

    Characteristics:
    - Generates aliases: Persona_001, Org_002, etc.
    - Creates glossary entries (reversible with mapping)
    - Consistent within project (same original → same alias)
    - Deterministic, no LLM required

    This is the CURRENT behavior of the system, now encapsulated
    as a strategy for the Strategy pattern.
    """

    def __init__(self, adapter: "InMemoryAnonymizationAdapter"):
        """
        Initialize with reference to the adapter.

        The adapter manages the glossary and alias generation.
        This strategy delegates to the adapter's existing logic.

        Args:
            adapter: The anonymization adapter with glossary management
        """
        self._adapter = adapter

    async def generate_replacement(
        self,
        detection: "NerDetection",
        project_id: str,
    ) -> ReplacementResult:
        """
        Generate pseudonym alias (Persona_001, etc).

        Delegates to the adapter's existing get_or_create_alias logic.
        """
        category = detection.category.value
        original = detection.value

        # Use adapter's existing alias generation
        # INTERMEDIATE level: dates get numeric aliases (Fecha_001)
        alias = await self._adapter.get_or_create_alias(
            category=category,
            original_value=original,
            project_id=project_id,
            level="INTERMEDIATE",
        )

        return ReplacementResult(
            original=original,
            replacement=alias,
            category=category,
            glossary_entry={
                "original_text": original,
                "alias": alias,
                "category": category,
            },
        )

    @property
    def creates_glossary_entries(self) -> bool:
        """Pseudonymization creates glossary entries for reversibility."""
        return True
