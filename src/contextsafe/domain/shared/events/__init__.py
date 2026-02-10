"""
Domain events for the ContextSafe system.

All events are:
- Immutable (frozen dataclasses)
- Named in past tense
- Contain all data needed to describe what happened
"""
from contextsafe.domain.shared.events.alias_assigned import AliasAssigned
from contextsafe.domain.shared.events.document_anonymized import DocumentAnonymized
from contextsafe.domain.shared.events.document_ingested import DocumentIngested
from contextsafe.domain.shared.events.pii_detected import PiiDetected

__all__ = [
    "DocumentIngested",
    "PiiDetected",
    "AliasAssigned",
    "DocumentAnonymized",
]
