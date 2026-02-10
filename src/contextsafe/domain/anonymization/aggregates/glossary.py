"""
Glossary Aggregate - Core aggregate for alias consistency.

Enforces the critical business rule BR-002: same entity -> same alias.

Traceability:
- Standard: consolidated_standards.yaml#factories.aggregates.Glossary
- Invariants: INV-009, INV-010, INV-011
- Business Rule: BR-002 (Alias Consistency)
- Bounded Context: BC-003 (Anonymization)
- Bug Fix: Consistency of Identity (anti-duplicates)
- Bug Fix: Corrección #5 - Inconsistencia de entidades (PLAN_CORRECCION_AUDITORIA.md)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from contextsafe.domain.anonymization.entities.alias_mapping import AliasMapping
from contextsafe.domain.anonymization.services.normalization import (
    normalize_pii_value,
    get_lookup_key,
)
from contextsafe.domain.shared.errors import (
    DuplicateAliasError,
    GlossaryError,
    InconsistentMappingError,
)
from contextsafe.domain.shared.types import AggregateRoot, DomainEvent, Err, Ok, Result
from contextsafe.domain.shared.value_objects import (
    Alias,
    EntityId,
    PiiCategory,
    PiiCategoryEnum,
    ProjectId,
)


@dataclass(kw_only=True)
class Glossary(AggregateRoot[ProjectId]):
    """
    Aggregate root for managing alias mappings within a project.

    The Glossary ensures:
    1. Same normalized value -> same alias (consistency)
    2. Each alias is unique within the project
    3. Aliases don't leak PII

    This is THE critical component for anonymization consistency.
    """

    id: ProjectId = field(kw_only=False)
    # Maps normalized_value -> AliasMapping
    _mappings_by_value: Dict[str, AliasMapping] = field(default_factory=dict)
    # Maps alias_value -> normalized_value (for uniqueness check)
    _values_by_alias: Dict[str, str] = field(default_factory=dict)
    # Counter per category for generating sequential aliases
    _counters: Dict[PiiCategoryEnum, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    _pending_events: List[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def create(cls, project_id: ProjectId) -> Glossary:
        """
        Create a new empty Glossary for a project.

        Args:
            project_id: The project this glossary belongs to

        Returns:
            New Glossary instance
        """
        return cls(id=project_id)

    def get_or_assign_alias(
        self,
        normalized_value: str,
        category: PiiCategory,
        document_id: Optional[str] = None,
    ) -> Result[Alias, GlossaryError]:
        """
        Get existing alias or assign a new one.

        This is the main method for ensuring consistency:
        - If the value already has an alias, return it
        - If not, generate a new unique alias

        Uses robust normalization to prevent duplicates:
        - "D. Juan García" and "Juan García" get the same alias
        - "Empresa ABC, S.L." and "Empresa ABC" get the same alias

        Args:
            normalized_value: The normalized PII text
            category: The PII category
            document_id: Optional document where first found

        Returns:
            Ok[Alias] with the (existing or new) alias
        """
        # Create lookup key with robust normalization (category-aware)
        category_str = str(category)
        lookup_key = get_lookup_key(normalized_value, category_str)

        # Check if already mapped
        if lookup_key in self._mappings_by_value:
            mapping = self._mappings_by_value[lookup_key]
            mapping.increment_count()
            return Ok(mapping.alias)

        # Generate new alias
        alias_result = self._generate_next_alias(category)
        if alias_result.is_err():
            return Err(alias_result.unwrap_err())

        alias = alias_result.unwrap()

        # Create mapping
        mapping_result = AliasMapping.create(
            normalized_value=normalized_value,
            category=category,
            project_id=self.id,
            alias=alias,
            first_document_id=document_id,
        )

        if mapping_result.is_err():
            return Err(mapping_result.unwrap_err())

        mapping = mapping_result.unwrap()

        # Store mapping
        self._mappings_by_value[lookup_key] = mapping
        self._values_by_alias[alias.value] = normalized_value

        self._touch()

        # Emit event
        # self._raise_event(AliasAssigned(...))

        return Ok(alias)

    def find_alias(
        self, normalized_value: str, category: PiiCategory
    ) -> Optional[Alias]:
        """
        Find existing alias for a value.

        Uses robust normalization to find matches even with
        variations like honorific prefixes.

        Args:
            normalized_value: The normalized PII text
            category: The PII category

        Returns:
            The alias if found, None otherwise
        """
        category_str = str(category)
        lookup_key = get_lookup_key(normalized_value, category_str)
        mapping = self._mappings_by_value.get(lookup_key)
        return mapping.alias if mapping else None

    def update_alias(
        self,
        original_term: str,
        category: PiiCategory,
        new_alias_value: str,
    ) -> Result[Alias, GlossaryError]:
        """
        Update the alias for an existing term.

        This enables user-driven alias customization (BR-002 Evolution).
        Aliases are immutable automatically, but mutable under explicit user demand.

        Args:
            original_term: The original PII text to find
            category: The PII category
            new_alias_value: The new alias string (can be custom like "Juez")

        Returns:
            Ok[Alias] with the new alias, Err[GlossaryError] if not found or invalid

        Traceability:
            - BR-002 Evolution: User-driven alias modification
        """
        # 1. Find existing mapping using robust normalization (category-aware)
        category_str = str(category)
        lookup_key = get_lookup_key(original_term, category_str)
        normalized = normalize_pii_value(original_term, category_str)
        mapping = self._mappings_by_value.get(lookup_key)

        if mapping is None:
            return Err(
                GlossaryError(
                    f"No mapping found for term '{original_term}' "
                    f"in category '{category}'"
                )
            )

        # 2. Store old alias for index update
        old_alias_value = mapping.alias.value

        # 3. Create new custom alias
        new_alias_result = Alias.create_custom(new_alias_value, category)
        if new_alias_result.is_err():
            return Err(GlossaryError(str(new_alias_result.unwrap_err())))

        new_alias = new_alias_result.unwrap()

        # 4. Check uniqueness (new alias must not conflict with another term)
        if new_alias.value in self._values_by_alias:
            existing_term = self._values_by_alias[new_alias.value]
            if existing_term != normalized:
                return Err(
                    GlossaryError(
                        f"Alias '{new_alias_value}' is already used for "
                        f"another term: '{existing_term}'"
                    )
                )

        # 5. Update the mapping
        update_result = mapping.update_alias(new_alias)
        if update_result.is_err():
            return Err(update_result.unwrap_err())

        # 6. Update reverse index
        if old_alias_value in self._values_by_alias:
            del self._values_by_alias[old_alias_value]
        self._values_by_alias[new_alias.value] = normalized

        self._touch()

        return Ok(new_alias)

    def find_original_value(self, alias_value: str) -> Optional[str]:
        """
        Find the original value for an alias (reverse lookup).

        Args:
            alias_value: The alias string

        Returns:
            The original normalized value if found
        """
        return self._values_by_alias.get(alias_value)

    def _generate_next_alias(
        self, category: PiiCategory
    ) -> Result[Alias, GlossaryError]:
        """
        Generate the next sequential alias for a category.

        Args:
            category: The PII category

        Returns:
            Ok[Alias] with the new alias
        """
        # Get and increment counter
        current = self._counters.get(category.value, 0)
        next_index = current + 1
        self._counters[category.value] = next_index

        # Generate alias
        alias_result = Alias.generate(category, next_index)
        if alias_result.is_err():
            return Err(GlossaryError(f"Failed to generate alias: {alias_result.unwrap_err()}"))

        return Ok(alias_result.unwrap())

    def is_alias_unique(self, alias_value: str) -> bool:
        """Check if an alias is not already used."""
        return alias_value not in self._values_by_alias

    @property
    def mapping_count(self) -> int:
        """Get total number of mappings."""
        return len(self._mappings_by_value)

    @property
    def mappings(self) -> List[AliasMapping]:
        """Get all mappings."""
        return list(self._mappings_by_value.values())

    def get_mappings_by_category(
        self, category: PiiCategory
    ) -> List[AliasMapping]:
        """Get all mappings for a category."""
        return [
            m for m in self._mappings_by_value.values()
            if m.category == category
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "mappings": [m.to_dict() for m in self._mappings_by_value.values()],
            "counters": {k.value: v for k, v in self._counters.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Glossary:
        """Reconstruct from dictionary."""
        project_id = ProjectId.create(data["id"]).unwrap()

        glossary = cls(id=project_id)

        # Restore counters
        for cat_str, count in data.get("counters", {}).items():
            cat_enum = PiiCategoryEnum(cat_str)
            glossary._counters[cat_enum] = count

        # Restore mappings
        for mapping_data in data.get("mappings", []):
            mapping = AliasMapping.from_dict(mapping_data)
            lookup_key = mapping.lookup_key
            glossary._mappings_by_value[lookup_key] = mapping
            glossary._values_by_alias[mapping.alias.value] = mapping.normalized_value

        glossary.created_at = datetime.fromisoformat(data["created_at"])
        glossary.updated_at = datetime.fromisoformat(data["updated_at"])
        glossary.version = data.get("version", 1)

        return glossary
