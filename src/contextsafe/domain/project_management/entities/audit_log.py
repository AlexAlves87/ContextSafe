"""
AuditLog entity.

Represents an audit log entry for tracking operations.

Traceability:
- Standard: consolidated_standards.yaml#factories.entities.AuditLog
- Requirement: security.audit_logging_required = true
- Bounded Context: BC-004 (ProjectManagement)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from contextsafe.domain.shared.errors import AuditError
from contextsafe.domain.shared.types import Entity, Err, Ok, Result
from contextsafe.domain.shared.value_objects import EntityId, ProjectId


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Document events
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_INGESTED = "DOCUMENT_INGESTED"
    DOCUMENT_PROCESSED = "DOCUMENT_PROCESSED"
    DOCUMENT_ANONYMIZED = "DOCUMENT_ANONYMIZED"
    DOCUMENT_DOWNLOADED = "DOCUMENT_DOWNLOADED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"

    # Project events
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    PROJECT_DELETED = "PROJECT_DELETED"

    # Detection events
    PII_DETECTED = "PII_DETECTED"
    DETECTION_REVIEWED = "DETECTION_REVIEWED"

    # Alias events
    ALIAS_ASSIGNED = "ALIAS_ASSIGNED"
    ALIAS_UPDATED = "ALIAS_UPDATED"

    # User events
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"


@dataclass(kw_only=True)
class AuditLog(Entity[EntityId]):
    """
    Audit log entry for tracking user actions.

    Provides complete traceability of:
    - Who did what
    - When it happened
    - What was affected
    - What changed
    """

    id: EntityId = field(kw_only=False)
    project_id: Optional[ProjectId] = field(kw_only=False)
    event_type: AuditEventType = field(kw_only=False)
    user_id: Optional[str] = field(kw_only=False)
    description: str = field(kw_only=False)
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: str,
        project_id: Optional[ProjectId],
        description: str,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Result[AuditLog, AuditError]:
        """
        Create an AuditLog entry.

        Args:
            event_type: Type of audit event
            project_id: Project context (if applicable)
            description: Human-readable description
            user_id: User who performed the action
            entity_type: Type of affected entity
            entity_id: ID of affected entity
            old_value: Previous value (for updates)
            new_value: New value (for updates)
            metadata: Additional context

        Returns:
            Ok[AuditLog] if valid, Err[AuditError] if invalid
        """
        # Generate audit ID
        audit_id_result = EntityId.create(str(uuid4()))
        if audit_id_result.is_err():
            return Err(AuditError("Failed to generate audit ID"))

        audit_id = audit_id_result.unwrap()

        # Parse event type
        try:
            event = AuditEventType(event_type.upper())
        except ValueError:
            return Err(AuditError(f"Unknown audit event type: {event_type}"))

        return Ok(
            cls(
                id=audit_id,
                project_id=project_id,
                event_type=event,
                user_id=user_id,
                description=description,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                metadata=metadata or {},
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id) if self.project_id else None,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "description": self.description,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditLog:
        """Reconstruct from dictionary."""
        audit_id = EntityId.create(data["id"]).unwrap()
        project_id = (
            ProjectId.create(data["project_id"]).unwrap()
            if data.get("project_id")
            else None
        )
        event = AuditEventType(data["event_type"])

        return cls(
            id=audit_id,
            project_id=project_id,
            event_type=event,
            user_id=data.get("user_id"),
            description=data["description"],
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )
