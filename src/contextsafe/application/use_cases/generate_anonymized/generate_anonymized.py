"""
GenerateAnonymized use case.

Handles document anonymization by replacing PII with aliases.

Traceability:
- Bounded Context: BC-003 (Anonymization)
- Business Rule: BR-002 (Alias Consistency)
- Function: F-010, F-011, F-012 (alias generation and replacement)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from contextsafe.application.ports import (
    DocumentRepository,
    EventPublisher,
    GlossaryRepository,
)
from contextsafe.domain.shared.errors import DocumentError, DomainError, NotFoundError
from contextsafe.domain.shared.events import DocumentAnonymized
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects import (
    AnonymizationLevel,
    DocumentId,
    INTERMEDIATE,
    PiiCategory,
)


@dataclass(frozen=True, slots=True)
class EntityToAnonymize:
    """An entity to be anonymized."""

    category: str
    value: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class GenerateAnonymizedRequest:
    """Input for anonymization."""

    document_id: str
    anonymization_level: str = "INTERMEDIATE"
    entities: Optional[List[EntityToAnonymize]] = None


@dataclass(frozen=True, slots=True)
class AliasUsed:
    """Record of an alias used."""

    original_value: str
    alias: str
    category: str
    occurrences: int


@dataclass(frozen=True, slots=True)
class GenerateAnonymizedResponse:
    """Output from anonymization."""

    document_id: str
    original_length: int
    anonymized_length: int
    entities_replaced: int
    aliases_used: List[AliasUsed]
    anonymized_text: str


class GenerateAnonymized:
    """
    Use case for generating anonymized document.

    Steps:
    1. Load document from repository
    2. Load or create glossary for project
    3. For each entity, get or assign alias
    4. Replace entities with aliases (in reverse order)
    5. Update document aggregate
    6. Save glossary and document
    7. Publish DocumentAnonymized event
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        glossary_repository: GlossaryRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._document_repo = document_repository
        self._glossary_repo = glossary_repository
        self._event_publisher = event_publisher

    async def execute(
        self, request: GenerateAnonymizedRequest
    ) -> Result[GenerateAnonymizedResponse, DomainError]:
        """
        Execute the anonymization use case.

        Args:
            request: The anonymization request

        Returns:
            Ok[GenerateAnonymizedResponse] on success, Err[DomainError] on failure
        """
        # 1. Validate document ID
        doc_id_result = DocumentId.create(request.document_id)
        if doc_id_result.is_err():
            return Err(DocumentError(f"Invalid document ID: {request.document_id}"))

        doc_id = doc_id_result.unwrap()

        # 2. Parse anonymization level
        level_result = AnonymizationLevel.from_string(request.anonymization_level)
        if level_result.is_err():
            return Err(level_result.unwrap_err())

        level = level_result.unwrap()

        # 3. Load document
        aggregate = await self._document_repo.find_by_id(doc_id)
        if aggregate is None:
            return Err(NotFoundError.create("Document", request.document_id))

        # 4. Verify document has extracted text
        if aggregate.extracted_text is None:
            return Err(DocumentError("Document has no extracted text"))

        # 5. Start anonymization
        result = aggregate.start_anonymization(level)
        if result.is_err():
            return Err(result.unwrap_err())

        # 6. Get or create glossary
        glossary = await self._glossary_repo.get_or_create(
            aggregate.document.project_id
        )

        # 7. If no entities provided, we cannot anonymize
        if not request.entities:
            return Err(DocumentError("No entities provided for anonymization"))

        # 8. Sort entities by position (reverse order for safe replacement)
        sorted_entities = sorted(
            request.entities,
            key=lambda e: e.start,
            reverse=True,
        )

        # 9. Replace each entity with its alias
        text = aggregate.extracted_text
        alias_usage: Dict[str, AliasUsed] = {}

        for entity in sorted_entities:
            # Parse category
            cat_result = PiiCategory.from_string(entity.category)
            if cat_result.is_err():
                continue  # Skip invalid categories

            category = cat_result.unwrap()

            # Check if category is included in this level
            if not level.includes_category(category.value):
                continue  # Skip categories not in this level

            # Get or assign alias (BR-002 consistency)
            alias_result = glossary.get_or_assign_alias(
                normalized_value=entity.value,
                category=category,
                document_id=str(doc_id),
            )

            if alias_result.is_err():
                continue  # Skip on error

            alias = alias_result.unwrap()

            # Replace in text (with boundary check to preserve whitespace)
            after_char = text[entity.end:entity.end + 1] if entity.end < len(text) else ""
            space_suffix = " " if after_char.isalnum() else ""
            text = text[:entity.start] + alias.value + space_suffix + text[entity.end:]

            # Track usage
            key = f"{category}:{entity.value.lower()}"
            if key in alias_usage:
                usage = alias_usage[key]
                alias_usage[key] = AliasUsed(
                    original_value=usage.original_value,
                    alias=usage.alias,
                    category=usage.category,
                    occurrences=usage.occurrences + 1,
                )
            else:
                alias_usage[key] = AliasUsed(
                    original_value=entity.value,
                    alias=alias.value,
                    category=str(category),
                    occurrences=1,
                )

        # 9.5 Glossary consistency scan — find values NER missed
        # Searches text for glossary-known entities (PERSON_NAME, ORGANIZATION)
        # that were not detected by NER (e.g., bare names in tables).
        replaced_spans = [
            (entity.start, entity.end) for entity in sorted_entities
            if PiiCategory.from_string(entity.category).is_ok()
            and level.includes_category(
                PiiCategory.from_string(entity.category).unwrap().value
            )
        ]
        text = self._glossary_consistency_scan(
            text, glossary, replaced_spans, level
        )

        # 10. Complete anonymization
        result = aggregate.complete_anonymization(text)
        if result.is_err():
            return Err(result.unwrap_err())

        # 11. Save glossary and document
        await self._glossary_repo.save(glossary)
        await self._document_repo.save(aggregate)

        # 12. Publish event
        event = DocumentAnonymized.create(
            document_id=str(doc_id),
            project_id=str(aggregate.document.project_id),
            anonymization_level=str(level),
            entities_anonymized=len(request.entities),
            unique_aliases_used=len(alias_usage),
            original_length=len(aggregate.extracted_text),
            anonymized_length=len(text),
        )
        await self._event_publisher.publish(event)

        # 13. Return response
        return Ok(
            GenerateAnonymizedResponse(
                document_id=str(doc_id),
                original_length=len(aggregate.extracted_text),
                anonymized_length=len(text),
                entities_replaced=sum(u.occurrences for u in alias_usage.values()),
                aliases_used=list(alias_usage.values()),
                anonymized_text=text,
            )
        )

    @staticmethod
    def _glossary_consistency_scan(
        text: str,
        glossary: Any,
        replaced_spans: list[tuple[int, int]],
        level: AnonymizationLevel,
    ) -> str:
        """
        Post-replacement scan: find glossary-known values that NER missed.

        Searches the already-partially-anonymized text for occurrences of
        values that exist in the glossary but were not detected by NER.
        This catches bare names in tables, repeated mentions without titles, etc.

        Only scans for PERSON_NAME and ORGANIZATION categories (the ones
        prone to detection gaps when appearing without contextual markers).

        Args:
            text: Text after NER-based replacements
            glossary: The project glossary with known mappings
            replaced_spans: Spans already replaced (to avoid double-processing)
            level: Anonymization level (to filter categories)

        Returns:
            Text with additional replacements applied
        """
        additional_replacements: list[tuple[int, int, str]] = []

        for lookup_key, mapping in glossary._mappings_by_value.items():
            parts = lookup_key.split(":", 1)
            if len(parts) != 2:
                continue
            category_str, normalized_value = parts

            # Check if category is included in this level
            cat_result = PiiCategory.from_string(category_str)
            if cat_result.is_err():
                continue
            category = cat_result.unwrap()
            if not level.includes_category(category.value):
                continue

            # Only scan for categories prone to detection gaps
            if category_str not in ("PERSON_NAME", "ORGANIZATION"):
                continue

            # Skip very short values to avoid false matches
            if len(normalized_value) < 5:
                continue

            # Search case-insensitive in the current text
            pattern = re.compile(re.escape(normalized_value), re.IGNORECASE)
            for match in pattern.finditer(text):
                m_start, m_end = match.start(), match.end()

                # Skip if this span overlaps with an already-replaced zone
                overlaps = False
                for r_start, r_end in replaced_spans:
                    if m_start < r_end and m_end > r_start:
                        overlaps = True
                        break
                if overlaps:
                    continue

                additional_replacements.append(
                    (m_start, m_end, mapping.alias.value)
                )

        # Apply replacements in reverse order (largest offset first)
        additional_replacements.sort(key=lambda x: x[0], reverse=True)
        for start, end, alias_value in additional_replacements:
            after_char = text[end:end + 1] if end < len(text) else ""
            space_suffix = " " if after_char.isalnum() else ""
            text = text[:start] + alias_value + space_suffix + text[end:]

        return text
