"""
PiiDetected domain event.

Emitted when PII entities are detected in a document.

Traceability:
- Standard: consolidated_standards.yaml#imports.components.PiiDetected
- Bounded Context: BC-002 (EntityDetection)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from contextsafe.domain.shared.types import DomainEvent


@dataclass(frozen=True)
class PiiDetected(DomainEvent):
    """
    Event emitted when PII entities are detected.

    Contains:
    - Document identification
    - Detection summary (counts by category)
    - Processing statistics
    """

    document_id: str = ""
    project_id: str = ""
    total_entities: int = 0
    entities_by_category: Dict[str, int] = field(default_factory=dict)
    low_confidence_count: int = 0
    processing_time_ms: int = 0

    @classmethod
    def create(
        cls,
        document_id: str,
        project_id: str,
        total_entities: int,
        entities_by_category: Dict[str, int],
        low_confidence_count: int = 0,
        processing_time_ms: int = 0,
        correlation_id: str = "",
    ) -> PiiDetected:
        """Create a PiiDetected event."""
        return cls(
            document_id=document_id,
            project_id=project_id,
            total_entities=total_entities,
            entities_by_category=entities_by_category,
            low_confidence_count=low_confidence_count,
            processing_time_ms=processing_time_ms,
            correlation_id=correlation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "document_id": self.document_id,
            "project_id": self.project_id,
            "total_entities": self.total_entities,
            "entities_by_category": dict(self.entities_by_category),
            "low_confidence_count": self.low_confidence_count,
            "processing_time_ms": self.processing_time_ms,
        })
        return base
