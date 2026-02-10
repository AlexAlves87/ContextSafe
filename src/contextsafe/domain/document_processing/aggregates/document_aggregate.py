"""
DocumentAggregate - Aggregate root for document processing.

Controls the document lifecycle and state transitions.

Traceability:
- Standard: consolidated_standards.yaml#factories.aggregates.DocumentAggregate
- Invariant: INV-002 (valid state transitions)
- Bounded Context: BC-001 (DocumentProcessing)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional
from uuid import uuid4

from contextsafe.domain.document_processing.entities.document import Document
from contextsafe.domain.shared.errors import DocumentError, StateTransitionError
from contextsafe.domain.shared.types import AggregateRoot, DomainEvent, Err, Ok, Result
from contextsafe.domain.shared.value_objects import (
    AnonymizationLevel,
    DocumentId,
    DocumentState,
    DocumentStateEnum,
    ANONYMIZED,
    ANONYMIZING,
    DETECTED,
    DETECTING,
    FAILED,
    INGESTED,
    INTERMEDIATE,
    PENDING,
    ProjectId,
)


@dataclass(kw_only=True)
class DocumentAggregate(AggregateRoot[DocumentId]):
    """
    Aggregate root for document processing.

    Controls:
    - Document lifecycle (state machine)
    - Text extraction results
    - Detection results
    - Anonymization output
    """

    id: DocumentId = field(kw_only=False)
    document: Document = field(kw_only=False)
    state: DocumentState = field(default_factory=lambda: PENDING)
    extracted_text: Optional[str] = None
    anonymized_text: Optional[str] = None
    anonymization_level: Optional[AnonymizationLevel] = None
    detection_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    _pending_events: List[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls,
        project_id: ProjectId,
        content: bytes,
        filename: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Result[DocumentAggregate, DocumentError]:
        """
        Create a new DocumentAggregate.

        Args:
            project_id: Project this document belongs to
            content: Document content as bytes
            filename: Original filename

        Returns:
            Ok[DocumentAggregate] if valid, Err[DocumentError] if invalid
        """
        # Create the document entity
        doc_result = Document.create(project_id, content, filename, metadata)
        if doc_result.is_err():
            return Err(doc_result.unwrap_err())

        document = doc_result.unwrap()

        aggregate = cls(
            id=document.id,
            document=document,
            state=PENDING,
        )

        # Emit creation event (will be defined in events module)
        # aggregate._raise_event(DocumentCreated(...))

        return Ok(aggregate)

    def transition_to(
        self, new_state: DocumentState
    ) -> Result[None, StateTransitionError]:
        """
        Transition to a new state.

        Args:
            new_state: Target state

        Returns:
            Ok[None] if valid transition, Err[StateTransitionError] if invalid
        """
        if not self.state.can_transition_to(new_state):
            return Err(
                StateTransitionError.create(str(self.state), str(new_state))
            )

        object.__setattr__(self, "state", new_state)
        self._touch()
        return Ok(None)

    def mark_ingested(self, extracted_text: str) -> Result[None, DocumentError]:
        """
        Mark document as ingested with extracted text.

        Args:
            extracted_text: The text extracted from the document

        Returns:
            Ok[None] if successful
        """
        result = self.transition_to(INGESTED)
        if result.is_err():
            return Err(DocumentError(str(result.unwrap_err())))

        object.__setattr__(self, "extracted_text", extracted_text)
        self.document.set_extracted_text(extracted_text)

        # Emit event
        # self._raise_event(DocumentIngested(...))

        return Ok(None)

    def start_detection(self) -> Result[None, DocumentError]:
        """Start PII detection phase."""
        result = self.transition_to(DETECTING)
        if result.is_err():
            return Err(DocumentError(str(result.unwrap_err())))
        return Ok(None)

    def complete_detection(self, detection_count: int) -> Result[None, DocumentError]:
        """
        Complete PII detection phase.

        Args:
            detection_count: Number of PII entities detected
        """
        result = self.transition_to(DETECTED)
        if result.is_err():
            return Err(DocumentError(str(result.unwrap_err())))

        object.__setattr__(self, "detection_count", detection_count)

        # Emit event
        # self._raise_event(PiiDetected(...))

        return Ok(None)

    def start_anonymization(
        self, level: AnonymizationLevel
    ) -> Result[None, DocumentError]:
        """
        Start anonymization phase.

        Args:
            level: Anonymization level to apply
        """
        result = self.transition_to(ANONYMIZING)
        if result.is_err():
            return Err(DocumentError(str(result.unwrap_err())))

        object.__setattr__(self, "anonymization_level", level)
        return Ok(None)

    def complete_anonymization(
        self, anonymized_text: str
    ) -> Result[None, DocumentError]:
        """
        Complete anonymization with result.

        Args:
            anonymized_text: The anonymized document text
        """
        result = self.transition_to(ANONYMIZED)
        if result.is_err():
            return Err(DocumentError(str(result.unwrap_err())))

        object.__setattr__(self, "anonymized_text", anonymized_text)

        # Emit event
        # self._raise_event(DocumentAnonymized(...))

        return Ok(None)

    def fail(self, error_message: str) -> None:
        """
        Mark document as failed.

        Args:
            error_message: Description of the failure
        """
        object.__setattr__(self, "state", FAILED)
        object.__setattr__(self, "error_message", error_message)
        self._touch()

        # Emit event
        # self._raise_event(ProcessingFailed(...))

    @property
    def is_completed(self) -> bool:
        """Check if processing is complete."""
        return self.state.is_completed

    @property
    def is_failed(self) -> bool:
        """Check if processing failed."""
        return self.state.is_failed

    @property
    def can_be_exported(self) -> bool:
        """Check if document can be exported."""
        return self.is_completed and self.anonymized_text is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "document": self.document.to_dict(),
            "state": str(self.state),
            "extracted_text": self.extracted_text,
            "anonymized_text": self.anonymized_text,
            "anonymization_level": str(self.anonymization_level) if self.anonymization_level else None,
            "detection_count": self.detection_count,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentAggregate:
        """Reconstruct from dictionary."""
        doc_id = DocumentId.create(data["id"]).unwrap()
        document = Document.from_dict(data["document"])
        state = DocumentState.from_string(data["state"]).unwrap()
        level = (
            AnonymizationLevel.from_string(data["anonymization_level"]).unwrap()
            if data.get("anonymization_level")
            else None
        )

        return cls(
            id=doc_id,
            document=document,
            state=state,
            extracted_text=data.get("extracted_text"),
            anonymized_text=data.get("anonymized_text"),
            anonymization_level=level,
            detection_count=data.get("detection_count", 0),
            error_message=data.get("error_message"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
        )
