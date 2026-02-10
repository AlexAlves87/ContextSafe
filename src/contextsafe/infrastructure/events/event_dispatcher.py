"""
Event dispatcher for domain events.

Coordinates event handling across the application.

Traceability:
- Contract: CNT-T3-EVENT-DISPATCHER-001
"""

from __future__ import annotations

import logging

from contextsafe.application.ports import EventPublisher
from contextsafe.domain.shared.types import DomainEvent


logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Central event dispatcher for the application.

    Features:
    - Event queue management
    - Handler orchestration
    - Event history (for debugging)
    """

    def __init__(
        self,
        publisher: EventPublisher,
        keep_history: bool = False,
        max_history: int = 1000,
    ) -> None:
        """
        Initialize the event dispatcher.

        Args:
            publisher: The event publisher to use
            keep_history: Whether to keep event history
            max_history: Maximum events to keep in history
        """
        self._publisher = publisher
        self._keep_history = keep_history
        self._max_history = max_history
        self._history: list[DomainEvent] = []
        self._event_counts: dict[str, int] = {}

    async def dispatch(self, event: DomainEvent) -> None:
        """
        Dispatch a single event.

        Args:
            event: The event to dispatch
        """
        event_name = type(event).__name__
        logger.debug(f"Dispatching event: {event_name}")

        # Track event counts
        self._event_counts[event_name] = self._event_counts.get(event_name, 0) + 1

        # Keep history if enabled
        if self._keep_history:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        # Publish to handlers
        await self._publisher.publish(event)

    async def dispatch_all(self, events: list[DomainEvent]) -> None:
        """
        Dispatch multiple events.

        Args:
            events: The events to dispatch
        """
        for event in events:
            await self.dispatch(event)

    def get_history(self) -> list[DomainEvent]:
        """Get the event history (if enabled)."""
        return list(self._history)

    def get_event_counts(self) -> dict[str, int]:
        """Get counts of dispatched events by type."""
        return dict(self._event_counts)

    def clear_history(self) -> None:
        """Clear the event history."""
        self._history.clear()

    def reset_counts(self) -> None:
        """Reset event counts."""
        self._event_counts.clear()


def create_default_dispatcher(
    keep_history: bool = False,
) -> tuple[EventDispatcher, EventPublisher]:
    """
    Create a default event dispatcher with in-memory publisher.

    Args:
        keep_history: Whether to keep event history

    Returns:
        Tuple of (EventDispatcher, EventPublisher)
    """
    from contextsafe.infrastructure.events.in_memory_publisher import (
        InMemoryEventPublisher,
    )

    publisher = InMemoryEventPublisher()
    dispatcher = EventDispatcher(publisher, keep_history=keep_history)
    return dispatcher, publisher
