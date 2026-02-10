"""
Base Aggregate Root class for domain aggregates.

Aggregates are clusters of entities and value objects with a root entity.
All access to the aggregate goes through the root.

Traceability:
- Pattern: Domain-Driven Design (Evans)
- Standard: consolidated_standards.yaml#imports.components.AggregateRoot
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, List, TypeVar

from contextsafe.domain.shared.types.base_event import DomainEvent

IdType = TypeVar("IdType")


@dataclass(kw_only=True)
class AggregateRoot(Generic[IdType]):
    """
    Base class for all aggregate roots.

    Aggregate roots:
    - Control access to entities within the aggregate
    - Ensure transactional consistency within the aggregate boundary
    - Emit domain events for state changes
    - Maintain version for optimistic concurrency

    Note: Uses kw_only=True to allow subclasses to add non-default fields.
    """

    id: IdType = field(kw_only=False)  # Allow positional for id
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    _pending_events: List[DomainEvent] = field(default_factory=list, repr=False)

    def __eq__(self, other: object) -> bool:
        """Aggregates are equal if they have the same ID."""
        if not isinstance(other, AggregateRoot):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def _touch(self) -> None:
        """Update timestamp and increment version."""
        object.__setattr__(self, "updated_at", datetime.utcnow())
        object.__setattr__(self, "version", self.version + 1)

    def _raise_event(self, event: DomainEvent) -> None:
        """
        Add a domain event to pending events.

        Events will be published after the aggregate is persisted.
        """
        self._pending_events.append(event)

    def collect_events(self) -> List[DomainEvent]:
        """
        Collect and clear pending domain events.

        Called by the repository after successful persistence.
        """
        events = list(self._pending_events)
        self._pending_events.clear()
        return events

    def clear_events(self) -> None:
        """Clear pending events without returning them."""
        self._pending_events.clear()

    @classmethod
    def create(cls, *args: Any, **kwargs: Any) -> Any:
        """
        Factory method for creating new aggregates.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement create()")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Any:
        """
        Reconstruct aggregate from dictionary.

        Used for loading from persistence.
        """
        raise NotImplementedError("Subclasses must implement from_dict()")
