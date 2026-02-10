"""
DocumentIngested domain event.

Emitted when a document has been successfully ingested and text extracted.

Traceability:
- Standard: consolidated_standards.yaml#imports.components.DocumentIngested
- Bounded Context: BC-001 (DocumentProcessing)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from contextsafe.domain.shared.types import DomainEvent


@dataclass(frozen=True)
class DocumentIngested(DomainEvent):
    """
    Event emitted when a document is successfully ingested.

    Contains:
    - Document identification
    - Extraction results (text length, format)
    - Processing metadata
    """

    document_id: str = ""
    project_id: str = ""
    filename: str = ""
    text_length: int = 0
    format_detected: str = ""

    @classmethod
    def create(
        cls,
        document_id: str,
        project_id: str,
        filename: str,
        text_length: int,
        format_detected: str,
        correlation_id: str = "",
    ) -> DocumentIngested:
        """Create a DocumentIngested event."""
        return cls(
            document_id=document_id,
            project_id=project_id,
            filename=filename,
            text_length=text_length,
            format_detected=format_detected,
            correlation_id=correlation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "document_id": self.document_id,
            "project_id": self.project_id,
            "filename": self.filename,
            "text_length": self.text_length,
            "format_detected": self.format_detected,
        })
        return base
