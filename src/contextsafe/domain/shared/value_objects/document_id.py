"""
DocumentId value object.

Immutable identifier for documents.

Traceability:
- Standard: consolidated_standards.yaml#factories.value_objects.DocumentId
- Bounded Context: BC-001 (DocumentProcessing)
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from contextsafe.domain.shared.errors import InvalidIdError
from contextsafe.domain.shared.types import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class DocumentId:
    """
    Unique identifier for a document.

    Value object that encapsulates document ID validation.
    """

    value: str

    @classmethod
    def create(cls, value: str) -> Result[DocumentId, InvalidIdError]:
        """
        Create a validated DocumentId.

        Args:
            value: UUID string

        Returns:
            Ok[DocumentId] if valid, Err[InvalidIdError] if invalid
        """
        if not value or not value.strip():
            return Err(InvalidIdError.create("", "non-empty UUID"))

        try:
            # Validate UUID format
            UUID(value)
        except ValueError:
            return Err(InvalidIdError.create(value, "UUID"))

        return Ok(cls(value=value))

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Compare by value."""
        if isinstance(other, DocumentId):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Hash by value."""
        return hash(self.value)
