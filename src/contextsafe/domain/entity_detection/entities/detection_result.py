"""
DetectionResult entity.

Represents a detected PII entity in a document.

Traceability:
- Standard: consolidated_standards.yaml#factories.entities.DetectionResult
- Invariant: INV-008 (low confidence requires review)
- Bounded Context: BC-002 (EntityDetection)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from contextsafe.domain.shared.errors import DetectionError
from contextsafe.domain.shared.types import Entity, Err, Ok, Result
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    DocumentId,
    EntityId,
    PiiCategory,
    TextSpan,
)


@dataclass(frozen=True, kw_only=True)
class DetectionResult(Entity[EntityId]):
    """
    A detected PII entity in a document.

    Contains:
    - The original value found
    - Its position in the document
    - The PII category
    - Confidence score from the NER model
    - Whether manual review is needed
    """

    id: EntityId = field(kw_only=False)
    document_id: DocumentId = field(kw_only=False)
    category: PiiCategory = field(kw_only=False)
    original_value: str = field(kw_only=False)
    span: TextSpan = field(kw_only=False)
    confidence: ConfidenceScore = field(kw_only=False)
    normalized_value: Optional[str] = None
    needs_review: bool = False
    reviewed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        document_id: DocumentId,
        category: PiiCategory,
        value: str,
        span: TextSpan,
        confidence: ConfidenceScore,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Result[DetectionResult, DetectionError]:
        """
        Create a DetectionResult.

        Args:
            document_id: The document where the entity was found
            category: The PII category
            value: The original text value
            span: The text position
            confidence: Detection confidence score

        Returns:
            Ok[DetectionResult] if valid, Err[DetectionError] if invalid
        """
        # Generate entity ID
        entity_id_result = EntityId.create(str(uuid4()))
        if entity_id_result.is_err():
            return Err(DetectionError("Failed to generate entity ID"))

        entity_id = entity_id_result.unwrap()

        # Check if review is needed (INV-008)
        needs_review = confidence.needs_review

        # Normalize the value (lowercase, stripped)
        normalized = value.strip().lower()

        return Ok(
            cls(
                id=entity_id,
                document_id=document_id,
                category=category,
                original_value=value,
                span=span,
                confidence=confidence,
                normalized_value=normalized,
                needs_review=needs_review,
                reviewed=False,
                metadata=metadata or {},
            )
        )

    def mark_reviewed(self, approved: bool = True) -> None:
        """Mark this detection as reviewed."""
        object.__setattr__(self, "reviewed", True)
        object.__setattr__(self, "needs_review", not approved)
        self._touch()

    def update_category(self, new_category: PiiCategory) -> None:
        """Update the category (after review)."""
        object.__setattr__(self, "category", new_category)
        self._touch()

    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence detection."""
        return self.confidence.is_high_confidence

    @property
    def is_actionable(self) -> bool:
        """Check if this detection can be processed (not needing review or already reviewed)."""
        return not self.needs_review or self.reviewed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "category": str(self.category),
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "span_start": self.span.start,
            "span_end": self.span.end,
            "span_text": self.span.text,
            "confidence": self.confidence.value,
            "needs_review": self.needs_review,
            "reviewed": self.reviewed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DetectionResult:
        """Reconstruct from dictionary."""
        entity_id = EntityId.create(data["id"]).unwrap()
        document_id = DocumentId.create(data["document_id"]).unwrap()
        category = PiiCategory.from_string(data["category"]).unwrap()
        span = TextSpan.create(
            data["span_start"], data["span_end"], data["span_text"]
        ).unwrap()
        confidence = ConfidenceScore.create(data["confidence"]).unwrap()

        return cls(
            id=entity_id,
            document_id=document_id,
            category=category,
            original_value=data["original_value"],
            span=span,
            confidence=confidence,
            normalized_value=data.get("normalized_value"),
            needs_review=data.get("needs_review", False),
            reviewed=data.get("reviewed", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )
