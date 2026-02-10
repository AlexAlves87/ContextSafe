"""
DocumentState value object.

Represents the processing state of a document.

Traceability:
- Standard: consolidated_standards.yaml#vocabulary.document_states
- Invariant: INV-002 (valid state transitions)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet

from contextsafe.domain.shared.errors import InvalidStateError
from contextsafe.domain.shared.types import Err, Ok, Result


class DocumentStateEnum(str, Enum):
    """Enumeration of document states."""

    PENDING = "PENDING"
    INGESTED = "INGESTED"
    DETECTING = "DETECTING"
    DETECTED = "DETECTED"
    ANONYMIZING = "ANONYMIZING"
    ANONYMIZED = "ANONYMIZED"
    FAILED = "FAILED"


# Valid state transitions (INV-002)
VALID_TRANSITIONS: dict[DocumentStateEnum, FrozenSet[DocumentStateEnum]] = {
    DocumentStateEnum.PENDING: frozenset({
        DocumentStateEnum.INGESTED,
        DocumentStateEnum.FAILED,
    }),
    DocumentStateEnum.INGESTED: frozenset({
        DocumentStateEnum.DETECTING,
        DocumentStateEnum.FAILED,
    }),
    DocumentStateEnum.DETECTING: frozenset({
        DocumentStateEnum.DETECTED,
        DocumentStateEnum.FAILED,
    }),
    DocumentStateEnum.DETECTED: frozenset({
        DocumentStateEnum.ANONYMIZING,
        DocumentStateEnum.FAILED,
    }),
    DocumentStateEnum.ANONYMIZING: frozenset({
        DocumentStateEnum.ANONYMIZED,
        DocumentStateEnum.FAILED,
    }),
    DocumentStateEnum.ANONYMIZED: frozenset(),  # Terminal state
    DocumentStateEnum.FAILED: frozenset(),  # Terminal state
}


@dataclass(frozen=True, slots=True)
class DocumentState:
    """
    Value object representing document processing state.

    Implements the state machine with valid transitions.
    """

    value: DocumentStateEnum

    @classmethod
    def from_string(cls, value: str) -> Result[DocumentState, InvalidStateError]:
        """
        Create a DocumentState from string.

        Args:
            value: State name

        Returns:
            Ok[DocumentState] if valid, Err[InvalidStateError] if invalid
        """
        normalized = value.upper().strip()

        try:
            state_enum = DocumentStateEnum(normalized)
            return Ok(cls(value=state_enum))
        except ValueError:
            return Err(InvalidStateError.create(value))

    @classmethod
    def initial(cls) -> DocumentState:
        """Create the initial state (PENDING)."""
        return cls(value=DocumentStateEnum.PENDING)

    def can_transition_to(self, target: DocumentState) -> bool:
        """Check if transition to target state is valid."""
        valid_targets = VALID_TRANSITIONS.get(self.value, frozenset())
        return target.value in valid_targets

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return len(VALID_TRANSITIONS.get(self.value, frozenset())) == 0

    @property
    def is_failed(self) -> bool:
        """Check if this is the failed state."""
        return self.value == DocumentStateEnum.FAILED

    @property
    def is_completed(self) -> bool:
        """Check if document processing is complete."""
        return self.value == DocumentStateEnum.ANONYMIZED

    def __str__(self) -> str:
        """String representation."""
        return self.value.value

    def __eq__(self, other: object) -> bool:
        """Compare by value."""
        if isinstance(other, DocumentState):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Hash by value."""
        return hash(self.value)


# Convenience constants
PENDING = DocumentState(DocumentStateEnum.PENDING)
INGESTED = DocumentState(DocumentStateEnum.INGESTED)
DETECTING = DocumentState(DocumentStateEnum.DETECTING)
DETECTED = DocumentState(DocumentStateEnum.DETECTED)
ANONYMIZING = DocumentState(DocumentStateEnum.ANONYMIZING)
ANONYMIZED = DocumentState(DocumentStateEnum.ANONYMIZED)
FAILED = DocumentState(DocumentStateEnum.FAILED)
