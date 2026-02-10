"""
Domain events for entity detection and review audit trail.

These events capture human oversight actions required by AI Act Art. 14.
Every review decision is recorded as an immutable fact for forensic
traceability.

Traceability:
- AI Act Art. 14: Human oversight for high-risk systems
- AI Act Art. 12: Automatic event logging
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from contextsafe.domain.shared.types.base_event import DomainEvent


@dataclass(frozen=True)
class EntityReviewed(DomainEvent):
    """
    Emitted when a human reviews a detected entity.

    Records the full context of the review decision including
    confidence zone, time spent, and action taken.
    """

    document_id: str = ""
    project_id: str = ""
    entity_id: str = ""
    category: str = ""
    original_value: str = ""
    confidence: float = 0.0
    zone: str = ""  # GREEN, AMBER, RED
    action: str = ""  # APPROVED, REJECTED, CORRECTED
    correction_applied: bool = False
    new_category: Optional[str] = None
    new_value: Optional[str] = None
    user_session_id: str = ""
    review_time_ms: int = 0  # Time spent reviewing this entity

    @classmethod
    def create(
        cls,
        document_id: str,
        project_id: str,
        entity_id: str,
        category: str,
        original_value: str,
        confidence: float,
        zone: str,
        action: str,
        user_session_id: str,
        review_time_ms: int = 0,
        correction_applied: bool = False,
        new_category: Optional[str] = None,
        new_value: Optional[str] = None,
    ) -> EntityReviewed:
        return cls(
            occurred_at=datetime.now(timezone.utc),
            event_id=str(uuid4()),
            document_id=document_id,
            project_id=project_id,
            entity_id=entity_id,
            category=category,
            original_value=original_value,
            confidence=confidence,
            zone=zone,
            action=action,
            user_session_id=user_session_id,
            review_time_ms=review_time_ms,
            correction_applied=correction_applied,
            new_category=new_category,
            new_value=new_value,
        )

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "document_id": self.document_id,
            "project_id": self.project_id,
            "entity_id": self.entity_id,
            "category": self.category,
            "original_value": self.original_value,
            "confidence": self.confidence,
            "zone": self.zone,
            "action": self.action,
            "correction_applied": self.correction_applied,
            "new_category": self.new_category,
            "new_value": self.new_value,
            "user_session_id": self.user_session_id,
            "review_time_ms": self.review_time_ms,
        })
        return base


@dataclass(frozen=True)
class BatchReviewCompleted(DomainEvent):
    """
    Emitted when a batch of GREEN-zone entities is approved.

    Captures the bulk approval for audit trail without requiring
    individual events per entity (reduces noise for high-confidence items).
    """

    document_id: str = ""
    project_id: str = ""
    entity_count: int = 0
    zone: str = "GREEN"
    user_session_id: str = ""

    @classmethod
    def create(
        cls,
        document_id: str,
        project_id: str,
        entity_count: int,
        user_session_id: str,
    ) -> BatchReviewCompleted:
        return cls(
            occurred_at=datetime.now(timezone.utc),
            event_id=str(uuid4()),
            document_id=document_id,
            project_id=project_id,
            entity_count=entity_count,
            user_session_id=user_session_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "document_id": self.document_id,
            "project_id": self.project_id,
            "entity_count": self.entity_count,
            "zone": self.zone,
            "user_session_id": self.user_session_id,
        })
        return base


@dataclass(frozen=True)
class ExportAttempted(DomainEvent):
    """
    Emitted when a user attempts to export a document.

    Records whether the export was allowed or blocked, and why.
    """

    document_id: str = ""
    project_id: str = ""
    user_session_id: str = ""
    allowed: bool = False
    blocked_reason: str = ""
    pending_reviews: int = 0
    total_entities: int = 0
    reviewed_entities: int = 0
    validation_failures: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        document_id: str,
        project_id: str,
        user_session_id: str,
        allowed: bool,
        pending_reviews: int = 0,
        total_entities: int = 0,
        reviewed_entities: int = 0,
        blocked_reason: str = "",
        validation_failures: tuple[str, ...] = (),
    ) -> ExportAttempted:
        return cls(
            occurred_at=datetime.now(timezone.utc),
            event_id=str(uuid4()),
            document_id=document_id,
            project_id=project_id,
            user_session_id=user_session_id,
            allowed=allowed,
            blocked_reason=blocked_reason,
            pending_reviews=pending_reviews,
            total_entities=total_entities,
            reviewed_entities=reviewed_entities,
            validation_failures=validation_failures,
        )

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "document_id": self.document_id,
            "project_id": self.project_id,
            "user_session_id": self.user_session_id,
            "allowed": self.allowed,
            "blocked_reason": self.blocked_reason,
            "pending_reviews": self.pending_reviews,
            "total_entities": self.total_entities,
            "reviewed_entities": self.reviewed_entities,
            "validation_failures": list(self.validation_failures),
        })
        return base
