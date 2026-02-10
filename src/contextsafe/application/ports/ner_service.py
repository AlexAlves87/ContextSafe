"""
NerService port.

Abstract interface for Named Entity Recognition.

Traceability:
- Standard: consolidated_standards.yaml#imports.components.NerService
- Bounded Context: BC-002 (EntityDetection)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Awaitable, Callable, List

from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)

# Type alias for progress callback: (current_chunk, total_chunks, info) -> None
ProgressCallback = Callable[[int, int, str], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class NerDetection:
    """
    A single NER detection result.

    Attributes:
        category: The PII category detected
        value: The text value of the entity
        span: Start/end positions in the original text
        confidence: Confidence score of the detection
        source: Detector that produced this detection (roberta, spacy, regex, presidio)
    """

    category: PiiCategory
    value: str
    span: TextSpan
    confidence: ConfidenceScore
    source: str = "unknown"  # Detector origin: roberta, spacy, regex, presidio

    def with_category(self, new_category: PiiCategory) -> "NerDetection":
        """Create a copy with a different category (for anchor forcing)."""
        return NerDetection(
            category=new_category,
            value=self.value,
            span=self.span,
            confidence=self.confidence,
            source=self.source,
        )

    def with_span(self, new_span: TextSpan, new_value: str) -> "NerDetection":
        """Create a copy with updated span and value (for token snapping)."""
        return NerDetection(
            category=self.category,
            value=new_value,
            span=new_span,
            confidence=self.confidence,
            source=self.source,
        )


class NerService(ABC):
    """
    Port for Named Entity Recognition.

    Responsible for detecting PII entities in text.

    Implementations:
    - SpacyNerAdapter (for spaCy models)
    - LlamaCppNerAdapter (for local LLM-based NER)
    """

    @abstractmethod
    async def detect_entities(
        self,
        text: str,
        categories: List[PiiCategory] | None = None,
        min_confidence: float = 0.5,
        progress_callback: ProgressCallback | None = None,
    ) -> List[NerDetection]:
        """
        Detect PII entities in text.

        Args:
            text: The text to analyze
            categories: Optional filter for specific categories
            min_confidence: Minimum confidence threshold
            progress_callback: Optional async callback for progress updates.
                              Called with (current_step, total_steps, info_string).

        Returns:
            List of detected entities
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the NER service is available.

        Returns:
            True if service is ready, False otherwise
        """
        ...

    @abstractmethod
    async def get_model_info(self) -> dict:
        """
        Get information about the loaded model.

        Returns:
            Dict with model name, version, capabilities
        """
        ...
