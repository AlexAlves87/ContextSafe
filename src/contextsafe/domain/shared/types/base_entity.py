"""
Base Entity class for domain entities.

Entities have identity that persists over time. Two entities with the same
attributes but different IDs are different entities.

Traceability:
- Pattern: Domain-Driven Design (Evans)
- Standard: consolidated_standards.yaml#imports.components.Entity
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

IdType = TypeVar("IdType")


@dataclass(kw_only=True)
class Entity(ABC, Generic[IdType]):
    """
    Base class for all domain entities.

    Entities have:
    - A unique identifier that defines equality
    - A lifecycle with creation and update timestamps
    - Version for optimistic concurrency control

    Note: Uses kw_only=True to allow subclasses to add non-default fields.
    """

    id: IdType = field(kw_only=False)  # Allow positional for id
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)

    def __eq__(self, other: object) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)

    def _touch(self) -> None:
        """Update the updated_at timestamp and increment version."""
        object.__setattr__(self, "updated_at", datetime.utcnow())
        object.__setattr__(self, "version", self.version + 1)

    @classmethod
    @abstractmethod
    def create(cls, *args: Any, **kwargs: Any) -> Any:
        """
        Factory method for creating new entities.

        Must be implemented by subclasses to return Result[Entity, Error].
        """
        ...


def generate_id() -> str:
    """Generate a new UUID string for entity IDs."""
    return str(uuid4())
