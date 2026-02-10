"""
DocumentAnonymized domain event.

Emitted when a document has been successfully anonymized.

Traceability:
- Standard: consolidated_standards.yaml#imports.components.DocumentAnonymized
- Bounded Context: BC-003 (Anonymization)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from contextsafe.domain.shared.types import DomainEvent


@dataclass(frozen=True)
class DocumentAnonymized(DomainEvent):
    """
    Event emitted when a document is successfully anonymized.

    Contains:
    - Document identification
    - Anonymization statistics
    - Processing metadata
    """

    document_id: str = ""
    project_id: str = ""
    anonymization_level: str = ""
    entities_replaced: int = 0
    unique_aliases_used: int = 0
    original_length: int = 0
    anonymized_length: int = 0
    processing_time_ms: int = 0

    @classmethod
    def create(
        cls,
        document_id: str,
        project_id: str,
        anonymization_level: str,
        entities_replaced: int,
        unique_aliases_used: int = 0,
        original_length: int = 0,
        anonymized_length: int = 0,
        processing_time_ms: int = 0,
        correlation_id: str = "",
    ) -> DocumentAnonymized:
        """Create a DocumentAnonymized event."""
        return cls(
            document_id=document_id,
            project_id=project_id,
            anonymization_level=anonymization_level,
            entities_replaced=entities_replaced,
            unique_aliases_used=unique_aliases_used,
            original_length=original_length,
            anonymized_length=anonymized_length,
            processing_time_ms=processing_time_ms,
            correlation_id=correlation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "document_id": self.document_id,
            "project_id": self.project_id,
            "anonymization_level": self.anonymization_level,
            "entities_replaced": self.entities_replaced,
            "unique_aliases_used": self.unique_aliases_used,
            "original_length": self.original_length,
            "anonymized_length": self.anonymized_length,
            "processing_time_ms": self.processing_time_ms,
        })
        return base
