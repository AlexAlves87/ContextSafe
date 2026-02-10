"""
AliasAssigned domain event.

Emitted when an alias is assigned to a PII entity.

Traceability:
- Standard: consolidated_standards.yaml#imports.components.AliasAssigned
- Business Rule: BR-002 (Alias Consistency)
- Bounded Context: BC-003 (Anonymization)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from contextsafe.domain.shared.types import DomainEvent


@dataclass(frozen=True)
class AliasAssigned(DomainEvent):
    """
    Event emitted when an alias is assigned to a PII entity.

    This event is important for:
    - Audit trail of alias assignments
    - Consistency tracking
    - Debugging alias behavior
    """

    project_id: str = ""
    entity_id: str = ""
    original_value: str = ""
    alias: str = ""
    category: str = ""
    is_new_alias: bool = True

    @classmethod
    def create(
        cls,
        project_id: str,
        entity_id: str,
        original_value: str,
        alias: str,
        category: str,
        is_new_alias: bool = True,
        correlation_id: str = "",
    ) -> AliasAssigned:
        """Create an AliasAssigned event."""
        return cls(
            project_id=project_id,
            entity_id=entity_id,
            original_value=original_value,
            alias=alias,
            category=category,
            is_new_alias=is_new_alias,
            correlation_id=correlation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "project_id": self.project_id,
            "entity_id": self.entity_id,
            "original_value": self.original_value,
            "alias": self.alias,
            "category": self.category,
            "is_new_alias": self.is_new_alias,
        })
        return base
