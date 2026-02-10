"""
Base class for anonymization strategies.

Each level of anonymization implements this interface:
- Level 1 (BASIC): MaskingStrategy - asterisks, no glossary
- Level 2 (INTERMEDIATE): PseudonymStrategy - Persona_001, with glossary
- Level 3 (ADVANCED): SyntheticStrategy - synthetic names, with glossary
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contextsafe.application.ports.ner_service import NerDetection


@dataclass
class ReplacementResult:
    """
    Result of generating a replacement for a detection.

    Attributes:
        original: The original PII text
        replacement: The replacement text (asterisks, alias, or synthetic)
        category: The PII category
        glossary_entry: Dict for glossary (None for masking level)
    """

    original: str
    replacement: str
    category: str
    glossary_entry: dict | None = None


class AnonymizationStrategy(ABC):
    """
    Base strategy for anonymization.

    Each level implements this interface differently:
    - Level 1 (Masking): Returns asterisks, no glossary
    - Level 2 (Pseudonym): Returns Persona_001, updates glossary
    - Level 3 (Synthetic): Returns synthetic name, updates glossary

    The strategy ONLY handles replacement generation.
    Glossary management and text manipulation are handled by the adapter.
    """

    @abstractmethod
    async def generate_replacement(
        self,
        detection: "NerDetection",
        project_id: str,
    ) -> ReplacementResult:
        """
        Generate a replacement for a single detection.

        Args:
            detection: The PII detection to replace
            project_id: Project context for consistency (ignored in masking)

        Returns:
            ReplacementResult with the replacement text
        """
        ...

    @property
    @abstractmethod
    def creates_glossary_entries(self) -> bool:
        """
        Whether this strategy creates glossary entries.

        - Masking (Level 1): False - no reversibility
        - Pseudonym (Level 2): True - maintains mapping
        - Synthetic (Level 3): True - maintains mapping
        """
        ...

    @property
    def level_name(self) -> str:
        """Human-readable name for this level."""
        return self.__class__.__name__.replace("Strategy", "")
