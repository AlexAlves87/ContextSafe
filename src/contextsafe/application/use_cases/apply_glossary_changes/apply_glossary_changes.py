"""
ApplyGlossaryChanges use case.

Applies user-defined alias changes to the glossary and regenerates
the anonymized document with the updated mappings.

Traceability:
- Bounded Context: BC-003 (Anonymization)
- Business Rule: BR-002 Evolution (User-driven alias modification)
- Function: F-010, F-011, F-012 (alias generation and replacement)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from contextsafe.application.ports import (
    DocumentRepository,
    EventPublisher,
    GlossaryRepository,
)
from contextsafe.domain.shared.errors import DomainError, DocumentError, NotFoundError
from contextsafe.domain.shared.events import DocumentAnonymized
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects import DocumentId, PiiCategory, ProjectId


@dataclass(frozen=True, slots=True)
class AliasChange:
    """A single alias change request."""

    original_term: str
    category: str
    new_alias: str


@dataclass(frozen=True, slots=True)
class ApplyGlossaryChangesRequest:
    """Input for applying glossary changes."""

    project_id: str
    changes: List[AliasChange]
    document_id: Optional[str] = None  # If provided, regenerate this document


@dataclass(frozen=True, slots=True)
class ChangeResult:
    """Result of a single alias change."""

    original_term: str
    old_alias: str
    new_alias: str
    success: bool
    error: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ApplyGlossaryChangesResponse:
    """Output from applying glossary changes."""

    project_id: str
    changes_applied: int
    changes_failed: int
    change_results: List[ChangeResult]
    document_regenerated: bool
    anonymized_text: Optional[str] = None


class ApplyGlossaryChanges:
    """
    Use case for applying user-defined alias changes.

    Steps:
    1. Load glossary for project
    2. Apply each alias change
    3. Save updated glossary
    4. If document_id provided, regenerate anonymized version
    5. Publish events

    Architecture:
    - Glossary changes persist globally (project-level)
    - Document regeneration is lazy (only requested document)
    - Other documents get updated when opened (consistency eventual)
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
        self, request: ApplyGlossaryChangesRequest
    ) -> Result[ApplyGlossaryChangesResponse, DomainError]:
        """
        Execute the glossary changes use case.

        Args:
            request: The change request with project_id, changes, and optional document_id

        Returns:
            Ok[ApplyGlossaryChangesResponse] on success, Err[DomainError] on failure
        """
        # 1. Validate project ID
        project_id_result = ProjectId.create(request.project_id)
        if project_id_result.is_err():
            return Err(DocumentError(f"Invalid project ID: {request.project_id}"))

        project_id = project_id_result.unwrap()

        # 2. Load glossary
        glossary = await self._glossary_repo.find_by_project(project_id)
        if glossary is None:
            return Err(NotFoundError.create("Glossary", request.project_id))

        # 3. Apply each change
        change_results: List[ChangeResult] = []
        changes_applied = 0
        changes_failed = 0

        for change in request.changes:
            # Parse category
            cat_result = PiiCategory.from_string(change.category)
            if cat_result.is_err():
                change_results.append(
                    ChangeResult(
                        original_term=change.original_term,
                        old_alias="",
                        new_alias=change.new_alias,
                        success=False,
                        error=f"Invalid category: {change.category}",
                    )
                )
                changes_failed += 1
                continue

            category = cat_result.unwrap()

            # Get current alias before update
            current_alias = glossary.find_alias(change.original_term, category)
            old_alias_value = current_alias.value if current_alias else ""

            # Apply update
            update_result = glossary.update_alias(
                original_term=change.original_term,
                category=category,
                new_alias_value=change.new_alias,
            )

            if update_result.is_err():
                change_results.append(
                    ChangeResult(
                        original_term=change.original_term,
                        old_alias=old_alias_value,
                        new_alias=change.new_alias,
                        success=False,
                        error=str(update_result.unwrap_err()),
                    )
                )
                changes_failed += 1
            else:
                change_results.append(
                    ChangeResult(
                        original_term=change.original_term,
                        old_alias=old_alias_value,
                        new_alias=change.new_alias,
                        success=True,
                    )
                )
                changes_applied += 1

        # 4. Save glossary (even if some changes failed, save successful ones)
        if changes_applied > 0:
            save_result = await self._glossary_repo.save(glossary)
            if save_result.is_err():
                return Err(DocumentError(f"Failed to save glossary: {save_result.unwrap_err()}"))

        # 5. Regenerate document if requested
        document_regenerated = False
        anonymized_text: Optional[str] = None

        if request.document_id and changes_applied > 0:
            regen_result = await self._regenerate_document(
                request.document_id, glossary
            )
            if regen_result.is_ok():
                document_regenerated = True
                anonymized_text = regen_result.unwrap()

        return Ok(
            ApplyGlossaryChangesResponse(
                project_id=request.project_id,
                changes_applied=changes_applied,
                changes_failed=changes_failed,
                change_results=change_results,
                document_regenerated=document_regenerated,
                anonymized_text=anonymized_text,
            )
        )

    async def _regenerate_document(
        self, document_id: str, glossary
    ) -> Result[str, DomainError]:
        """
        Regenerate anonymized text for a document using updated glossary.

        Uses simple text replacement based on glossary mappings.
        This is a "lazy" regeneration - only the requested document is updated.

        Args:
            document_id: The document to regenerate
            glossary: The updated glossary with new alias mappings

        Returns:
            Ok[str] with new anonymized text, Err[DomainError] on failure
        """
        # 1. Parse document ID
        doc_id_result = DocumentId.create(document_id)
        if doc_id_result.is_err():
            return Err(DocumentError(f"Invalid document ID: {document_id}"))

        doc_id = doc_id_result.unwrap()

        # 2. Load document
        aggregate = await self._document_repo.find_by_id(doc_id)
        if aggregate is None:
            return Err(NotFoundError.create("Document", document_id))

        # 3. Get original text
        if aggregate.extracted_text is None:
            return Err(DocumentError("Document has no extracted text"))

        # 4. Build replacement map from glossary
        # Map: original_term -> new_alias
        text = aggregate.extracted_text

        # Sort mappings by length (longest first) to avoid partial replacements
        sorted_mappings = sorted(
            glossary.mappings,
            key=lambda m: len(m.normalized_value),
            reverse=True,
        )

        # 5. Apply replacements (case-insensitive)
        for mapping in sorted_mappings:
            # Create case-insensitive pattern for original term
            pattern = re.compile(
                re.escape(mapping.normalized_value),
                re.IGNORECASE,
            )
            text = pattern.sub(mapping.alias.value, text)

        # 6. Update document aggregate
        # Note: We're updating the anonymized_text directly without state transition
        # because the document is already in ANONYMIZED state
        object.__setattr__(aggregate, "anonymized_text", text)
        aggregate._touch()

        # 7. Save document
        save_result = await self._document_repo.save(aggregate)
        if save_result.is_err():
            return Err(DocumentError(f"Failed to save document: {save_result.unwrap_err()}"))

        # 8. Publish event
        event = DocumentAnonymized.create(
            document_id=document_id,
            project_id=str(aggregate.document.project_id),
            anonymization_level=str(aggregate.anonymization_level) if aggregate.anonymization_level else "INTERMEDIATE",
            entities_anonymized=len(sorted_mappings),
            unique_aliases_used=len(sorted_mappings),
            original_length=len(aggregate.extracted_text),
            anonymized_length=len(text),
        )
        await self._event_publisher.publish(event)

        return Ok(text)
