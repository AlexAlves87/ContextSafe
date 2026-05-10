"""
EventPublisher port.

Abstract interface for publishing domain events.

Traceability:
- Standard: consolidated_standards.yaml#imports.components.EventPublisher
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from contextsafe.domain.shared.types import DomainEvent


class EventPublisher(ABC):
    """
    Port for publishing domain events.

    Implementations:
    - InMemoryEventPublisher (for single-process)
    - RedisEventPublisher (for distributed - future)
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.

        Args:
            event: The event to publish
        """
        ...

    @abstractmethod
    async def publish_all(self, events: list[DomainEvent]) -> None:
        """
        Publish multiple domain events.

        Args:
            events: The events to publish
        """
        ...

    @abstractmethod
    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], None],
    ) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: The type of event to subscribe to
            handler: The handler function to call
        """
        ...

    @abstractmethod
    def unsubscribe(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], None],
    ) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove
        """
        ...
