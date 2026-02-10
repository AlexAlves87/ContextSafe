"""
Base Domain Event class.

Domain events represent something that happened in the domain.
They are immutable facts that can be published and subscribed to.

Traceability:
- Pattern: Domain-Driven Design (Evans)
- Standard: consolidated_standards.yaml#imports.components.DomainEvent
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """
    Base class for all domain events.

    Domain events are:
    - Immutable (frozen dataclass)
    - Named in past tense (e.g., DocumentIngested, PiiDetected)
    - Carry all data needed to describe what happened
    - Include metadata for tracing and correlation
    """

    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str = field(default="")
    causation_id: str = field(default="")
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        """Get the event type name (class name)."""
        return self.__class__.__name__

    def with_correlation(self, correlation_id: str) -> DomainEvent:
        """Create a copy with correlation ID set."""
        return self.__class__(
            occurred_at=self.occurred_at,
            event_id=self.event_id,
            correlation_id=correlation_id,
            causation_id=self.causation_id,
            metadata=self.metadata,
        )

    def with_causation(self, causation_id: str) -> DomainEvent:
        """Create a copy with causation ID set."""
        return self.__class__(
            occurred_at=self.occurred_at,
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            causation_id=causation_id,
            metadata=self.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "occurred_at": self.occurred_at.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "metadata": self.metadata,
        }
