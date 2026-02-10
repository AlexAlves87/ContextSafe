"""
Event infrastructure for ContextSafe.

Provides event publishing and dispatching capabilities.
"""

from contextsafe.infrastructure.events.event_dispatcher import (
    EventDispatcher,
    create_default_dispatcher,
)
from contextsafe.infrastructure.events.in_memory_publisher import InMemoryEventPublisher


__all__ = [
    "EventDispatcher",
    "InMemoryEventPublisher",
    "create_default_dispatcher",
]
