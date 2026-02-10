"""
Shared types for the ContextSafe domain.

Exports:
- Result, Ok, Err: Railway-oriented programming types
- Entity: Base class for entities
- AggregateRoot: Base class for aggregates
- DomainEvent: Base class for domain events
"""
from contextsafe.domain.shared.types.base_aggregate import AggregateRoot
from contextsafe.domain.shared.types.base_entity import Entity, generate_id
from contextsafe.domain.shared.types.base_event import DomainEvent
from contextsafe.domain.shared.types.result import Err, Ok, Result, is_err, is_ok

__all__ = [
    "Result",
    "Ok",
    "Err",
    "is_ok",
    "is_err",
    "Entity",
    "generate_id",
    "AggregateRoot",
    "DomainEvent",
]
