"""
In-memory event publisher.

Simple event publisher for single-process applications.

Traceability:
- Contract: CNT-T3-INMEMORY-PUBLISHER-001
- Port: ports.EventPublisher
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable

from contextsafe.application.ports import EventPublisher
from contextsafe.domain.shared.types import DomainEvent


logger = logging.getLogger(__name__)


class InMemoryEventPublisher(EventPublisher):
    """
    In-memory implementation of EventPublisher.

    Features:
    - Synchronous and asynchronous handlers
    - Handler registration/deregistration
    - Error isolation (one handler failure doesn't affect others)
    """

    def __init__(self) -> None:
        """Initialize the in-memory publisher."""
        self._handlers: dict[type[DomainEvent], set[Callable[[DomainEvent], None]]] = defaultdict(
            set
        )
        self._async_handlers: dict[type[DomainEvent], set[Callable[[DomainEvent], None]]] = (
            defaultdict(set)
        )

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.

        Invokes all registered handlers for the event type.

        Args:
            event: The event to publish
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, set())
        async_handlers = self._async_handlers.get(event_type, set())

        # Invoke sync handlers
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler failed for {event_type.__name__}: {e}")

        # Invoke async handlers
        for handler in async_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Async handler failed for {event_type.__name__}: {e}")

    async def publish_all(self, events: list[DomainEvent]) -> None:
        """
        Publish multiple domain events.

        Args:
            events: The events to publish
        """
        for event in events:
            await self.publish(event)

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
        if asyncio.iscoroutinefunction(handler):
            self._async_handlers[event_type].add(handler)
        else:
            self._handlers[event_type].add(handler)

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
        if asyncio.iscoroutinefunction(handler):
            self._async_handlers[event_type].discard(handler)
        else:
            self._handlers[event_type].discard(handler)

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._handlers.clear()
        self._async_handlers.clear()

    def get_handler_count(self, event_type: type[DomainEvent]) -> int:
        """Get the number of handlers for an event type."""
        return len(self._handlers.get(event_type, set())) + len(
            self._async_handlers.get(event_type, set())
        )
