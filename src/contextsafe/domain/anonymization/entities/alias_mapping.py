"""
AliasMapping entity.

Represents a mapping from a PII value to its alias.

Traceability:
- Standard: consolidated_standards.yaml#factories.entities.AliasMapping
- Business Rule: BR-002 (Alias Consistency)
- Bounded Context: BC-003 (Anonymization)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from contextsafe.domain.anonymization.services.normalization import (
    get_lookup_key,
    normalize_pii_value,
)
from contextsafe.domain.shared.errors import GlossaryError
from contextsafe.domain.shared.types import Entity, Err, Ok, Result
from contextsafe.domain.shared.value_objects import (
    Alias,
    EntityId,
    PiiCategory,
    ProjectId,
)


@dataclass(kw_only=True)
class AliasMapping(Entity[EntityId]):
    """
    A mapping from a normalized PII value to its alias.

    This is the core entity for ensuring alias consistency (BR-002):
    - Same entity text -> Same alias (within a project)
    - Alias is unique within the project
    """

    id: EntityId = field(kw_only=False)
    project_id: ProjectId = field(kw_only=False)
    category: PiiCategory = field(kw_only=False)
    normalized_value: str = field(kw_only=False)
    alias: Alias = field(kw_only=False)
    occurrence_count: int = 1
    first_document_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        normalized_value: str,
        category: PiiCategory,
        project_id: ProjectId,
        alias: Alias,
        first_document_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Result[AliasMapping, GlossaryError]:
        """
        Create an AliasMapping.

        Args:
            normalized_value: The normalized PII text (lowercase, stripped)
            category: The PII category
            project_id: The project this mapping belongs to
            alias: The alias to use for this value
            first_document_id: ID of document where first detected

        Returns:
            Ok[AliasMapping] if valid, Err[GlossaryError] if invalid
        """
        # Generate mapping ID
        mapping_id_result = EntityId.create(str(uuid4()))
        if mapping_id_result.is_err():
            return Err(GlossaryError("Failed to generate mapping ID"))

        mapping_id = mapping_id_result.unwrap()

        # Validate alias category matches
        if alias.category != category:
            return Err(
                GlossaryError(
                    f"Alias category {alias.category} does not match "
                    f"mapping category {category}"
                )
            )

        return Ok(
            cls(
                id=mapping_id,
                project_id=project_id,
                category=category,
                normalized_value=normalize_pii_value(
                    normalized_value, str(category)
                ),
                alias=alias,
                occurrence_count=1,
                first_document_id=first_document_id,
                metadata=metadata or {},
            )
        )

    def increment_count(self) -> None:
        """Increment the occurrence count."""
        object.__setattr__(self, "occurrence_count", self.occurrence_count + 1)
        self._touch()

    def update_alias(self, new_alias: Alias) -> Result[None, GlossaryError]:
        """
        Update the alias for this mapping.

        This allows users to customize aliases (BR-002 Evolution).
        Aliases are immutable automatically, but mutable under explicit user demand.

        Args:
            new_alias: The new alias to use

        Returns:
            Ok[None] if updated, Err[GlossaryError] if invalid

        Traceability:
            - BR-002 Evolution: User-driven alias modification
        """
        # Validate category matches
        if new_alias.category != self.category:
            return Err(
                GlossaryError(
                    f"New alias category {new_alias.category} does not match "
                    f"mapping category {self.category}"
                )
            )

        object.__setattr__(self, "alias", new_alias)
        object.__setattr__(self, "version", self.version + 1)
        self._touch()
        return Ok(None)

    @property
    def lookup_key(self) -> str:
        """Get the key for lookups (category + normalized_value)."""
        return get_lookup_key(self.normalized_value, str(self.category))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "category": str(self.category),
            "normalized_value": self.normalized_value,
            "alias_value": self.alias.value,
            "occurrence_count": self.occurrence_count,
            "first_document_id": self.first_document_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AliasMapping:
        """Reconstruct from dictionary."""
        mapping_id = EntityId.create(data["id"]).unwrap()
        project_id = ProjectId.create(data["project_id"]).unwrap()
        category = PiiCategory.from_string(data["category"]).unwrap()
        alias = Alias.create(data["alias_value"], category).unwrap()

        return cls(
            id=mapping_id,
            project_id=project_id,
            category=category,
            normalized_value=data["normalized_value"],
            alias=alias,
            occurrence_count=data.get("occurrence_count", 1),
            first_document_id=data.get("first_document_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )
