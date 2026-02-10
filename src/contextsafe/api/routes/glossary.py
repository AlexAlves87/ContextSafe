"""
Glossary routes.

Traceability:
- Contract: CNT-T4-GLOSSARY-001
- Standard: consolidated_standards.yaml#vocabulary.dtos

Note: Glossary is always scoped to a specific project (BR-002).
"""

from __future__ import annotations

import re
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from contextsafe.api.middleware.session import get_session_id
from contextsafe.api.schemas import ErrorResponse, GlossaryEntryResponse
from contextsafe.api.schemas.response_wrapper import ApiListResponse, ApiResponse, PaginatedMeta
from contextsafe.api.session_manager import session_manager

# Import use case and dependencies
from contextsafe.api.dependencies import get_container
from contextsafe.application.use_cases import (
    ApplyGlossaryChanges,
    ApplyGlossaryChangesRequest,
    AliasChange,
)


router = APIRouter(prefix="/v1/projects", tags=["glossary"])


# ============================================================================
# Request/Response Schemas for PUT
# ============================================================================


class AliasChangeSchema(BaseModel):
    """Schema for a single alias change."""

    original_term: str = Field(..., description="The original PII text")
    category: str = Field(..., description="PII category (e.g., PERSON_NAME)")
    new_alias: str = Field(..., description="The new alias to use (e.g., 'Juez')")
    new_category: Optional[str] = Field(None, description="New category if changing (e.g., 'organization')")


class UpdateGlossaryRequest(BaseModel):
    """Request body for updating glossary aliases."""

    changes: List[AliasChangeSchema] = Field(
        default=[], description="List of alias changes to apply"
    )
    deletions: List[str] = Field(
        default=[], description="List of entry IDs to delete (undo anonymization)"
    )
    document_id: Optional[str] = Field(
        None, description="Document ID to regenerate (optional)"
    )


class ChangeResultSchema(BaseModel):
    """Result of a single alias change."""

    original_term: str
    old_alias: str
    new_alias: str
    success: bool
    error: Optional[str] = None


class UpdateGlossaryResponse(BaseModel):
    """Response from updating glossary."""

    project_id: str
    changes_applied: int
    changes_failed: int
    deletions_applied: int = 0
    merged_count: int = 0  # Number of duplicate entries that were merged
    change_results: List[ChangeResultSchema]
    document_regenerated: bool
    anonymized_text: Optional[str] = None


@router.get(
    "/{project_id}/glossary",
    response_model=ApiListResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def get_glossary(project_id: UUID, request: Request) -> ApiListResponse[dict]:
    """
    Retrieve project glossary (alias mappings).

    Returns all alias mappings for the project.
    Note: Original PII values are never returned, only aliases.
    """
    session_id = get_session_id(request)
    project_id_str = str(project_id)

    # Check project exists
    if not session_manager.get_project(session_id, project_id_str):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    entries = session_manager.get_glossary(session_id, project_id_str)

    # Transform to match frontend expected format
    # Include version/traceability info (OMISIÓN 2)
    formatted_entries = []
    for entry in entries:
        formatted_entries.append({
            "id": entry["id"],
            "originalText": entry["original_text"],
            "alias": entry["alias"],
            "category": entry["category"],
            "occurrences": entry.get("occurrences", 1),
            "createdAt": entry.get("created_at", ""),
            # Traceability fields
            "version": entry.get("version", 1),
            "updatedAt": entry.get("updated_at", entry.get("created_at", "")),
            "historyCount": len(entry.get("history", [])),
        })

    return ApiListResponse(
        data=formatted_entries,
        meta=PaginatedMeta(total=len(formatted_entries), limit=100, offset=0),
    )


@router.put(
    "/{project_id}/glossary",
    response_model=ApiResponse[UpdateGlossaryResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Project or glossary not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def update_glossary(
    project_id: UUID,
    request_body: UpdateGlossaryRequest,
    request: Request,
) -> ApiResponse[UpdateGlossaryResponse]:
    """
    Update glossary aliases and optionally regenerate document.

    This endpoint allows users to customize aliases in the glossary.
    Changes persist globally at project level (BR-002 Evolution).
    Document regeneration is lazy - only the specified document is updated.

    Traceability:
    - BR-002 Evolution: User-driven alias modification
    - Consistency: Eventual (other docs updated when opened)
    """
    session_id = get_session_id(request)
    project_id_str = str(project_id)

    # Check project exists
    if not session_manager.get_project(session_id, project_id_str):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get glossary from session
    glossary_entries = session_manager.get_glossary(session_id, project_id_str)
    if not glossary_entries:
        glossary_entries = []

    import traceback

    try:
        # Apply changes directly to in-memory glossary
        change_results: List[ChangeResultSchema] = []
        changes_applied = 0
        changes_failed = 0

        from datetime import datetime, timezone

        # 1. Apply Deletions first
        deletions_applied = 0
        if hasattr(request_body, 'deletions') and request_body.deletions:
            original_count = len(glossary_entries)
            # Filter out deleted entries
            glossary_entries = [
                e for e in glossary_entries if e["id"] not in request_body.deletions
            ]
            deletions_applied = original_count - len(glossary_entries)
    
        # 2. Apply Updates
        for change in request_body.changes:
            # Find the entry to update
            found = False
            for entry in glossary_entries:
                # Match by original text (case-insensitive)
                if entry.get("original_text", "").lower() == change.original_term.lower():
                    old_alias = entry.get("alias", "")
                    old_category = entry.get("category", "")
                    entry["alias"] = change.new_alias

                    # Update category if new_category is provided
                    if change.new_category:
                        entry["category"] = change.new_category

                    # TRACEABILITY: Track version history (OMISIÓN 2)
                    if "history" not in entry:
                        entry["history"] = []
                    history_entry = {
                        "old_alias": old_alias,
                        "new_alias": change.new_alias,
                        "changed_at": datetime.now(timezone.utc).isoformat(),
                        "version": len(entry.get("history", [])) + 2,  # v1 is original
                    }
                    # Track category change in history
                    if change.new_category and change.new_category != old_category:
                        history_entry["old_category"] = old_category
                        history_entry["new_category"] = change.new_category
                    entry["history"].append(history_entry)
                    entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                    entry["version"] = len(entry["history"]) + 1

                    change_results.append(ChangeResultSchema(
                        original_term=change.original_term,
                        old_alias=old_alias,
                        new_alias=change.new_alias,
                        success=True,
                        error=None,
                    ))
                    changes_applied += 1
                    found = True
                    break

            if not found:
                change_results.append(ChangeResultSchema(
                    original_term=change.original_term,
                    old_alias="",
                    new_alias=change.new_alias,
                    success=False,
                    error=f"Entry not found: {change.original_term}",
                ))
                changes_failed += 1

        # 3. MERGE DUPLICATES: Unify entries with same alias AND category
        # This handles the case where user changes an alias to match an existing one
        merged_count = 0
        seen_keys: dict[str, int] = {}  # (alias, category) -> index in glossary
        entries_to_remove: set[int] = set()

        for i, entry in enumerate(glossary_entries):
            alias = entry.get("alias", "").lower()
            category = entry.get("category", "").lower()
            key = (alias, category)

            if key in seen_keys:
                # Found duplicate - merge into the first occurrence
                first_idx = seen_keys[key]
                first_entry = glossary_entries[first_idx]

                # Sum occurrences
                first_entry["occurrences"] = (
                    first_entry.get("occurrences", 1) + entry.get("occurrences", 1)
                )

                # Combine original_text as list (for reference)
                if "merged_originals" not in first_entry:
                    first_entry["merged_originals"] = [first_entry.get("original_text", "")]
                first_entry["merged_originals"].append(entry.get("original_text", ""))

                # Track merge in history
                first_entry["history"].append({
                    "action": "merged_duplicate",
                    "merged_original_text": entry.get("original_text", ""),
                    "merged_occurrences": entry.get("occurrences", 1),
                    "changed_at": datetime.now(timezone.utc).isoformat(),
                })
                first_entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                first_entry["version"] = len(first_entry.get("history", [])) + 1

                entries_to_remove.add(i)
                merged_count += 1
            else:
                seen_keys[key] = i

        # Remove merged entries (iterate in reverse to preserve indices)
        if entries_to_remove:
            glossary_entries = [
                e for i, e in enumerate(glossary_entries) if i not in entries_to_remove
            ]

        # Save updated glossary to session
        session_manager.set_glossary(session_id, project_id_str, glossary_entries)

        # Regenerate ALL documents in the project with updated aliases
        document_regenerated = False
        anonymized_text: Optional[str] = None
        documents_updated = 0

        if changes_applied > 0 or deletions_applied > 0:
            # Get session for document access
            session = session_manager.get_session(session_id)
            if session:
                # Sort glossary entries by length (longest first) to avoid partial replacements
                sorted_entries = sorted(
                    glossary_entries,
                    key=lambda e: len(e.get("original_text", "")),
                    reverse=True,
                )

                # Find all documents for this project and regenerate them
                project_docs = session.get_project_documents(project_id_str)
                for doc_id, doc in project_docs.items():
                    original_text = doc.content or ""
                    if original_text:
                        # Apply all glossary aliases to regenerate anonymized text
                        new_anonymized = original_text
                        for entry in sorted_entries:
                            orig = entry.get("original_text", "")
                            alias = entry.get("alias", "")
                            if orig and alias:
                                # Case-insensitive replacement
                                pattern = re.compile(re.escape(orig), re.IGNORECASE)
                                new_anonymized = pattern.sub(alias, new_anonymized)

                        # Update anonymized content in session
                        session_manager.update_document(
                            session_id, doc_id,
                            anonymized={"original": original_text, "anonymized": new_anonymized}
                        )
                        documents_updated += 1

                        # Return the specific document if requested
                        if request_body.document_id == doc_id:
                            anonymized_text = new_anonymized

                document_regenerated = documents_updated > 0
    
        return ApiResponse(
            data=UpdateGlossaryResponse(
                project_id=project_id_str,
                changes_applied=changes_applied,
                changes_failed=changes_failed,
                deletions_applied=deletions_applied,
                merged_count=merged_count,
                change_results=change_results,
                document_regenerated=document_regenerated,
                anonymized_text=anonymized_text,
            )
        )
    except Exception as e:
        with open("debug_error.log", "a") as f:
            f.write(f"ERROR: {str(e)}\n")
            f.write(traceback.format_exc())
        raise e


# ============================================================================
# CORRECT GLOSSARY ENTRIES (Fix detection boundaries)
# ============================================================================


class OriginalTextCorrectionSchema(BaseModel):
    """Schema for correcting the original text of a glossary entry."""

    entry_id: str = Field(..., description="ID of the glossary entry")
    old_original_text: str = Field(..., description="The incorrectly detected text")
    new_original_text: str = Field(..., description="The corrected text")
    category: str = Field(..., description="PII category")
    alias: str = Field(..., description="The alias assigned to this entry")


class CorrectGlossaryRequest(BaseModel):
    """Request body for correcting glossary entries."""

    corrections: List[OriginalTextCorrectionSchema] = Field(
        ..., description="List of corrections to apply"
    )
    document_id: Optional[str] = Field(
        None, description="Document ID to regenerate (optional)"
    )


class CorrectGlossaryResponse(BaseModel):
    """Response from correcting glossary entries."""

    project_id: str
    changes_applied: int
    changes_failed: int
    document_regenerated: bool


@router.post(
    "/{project_id}/glossary/correct",
    response_model=ApiResponse[CorrectGlossaryResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Project or glossary not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def correct_glossary_entries(
    project_id: UUID,
    request_body: CorrectGlossaryRequest,
    request: Request,
) -> ApiResponse[CorrectGlossaryResponse]:
    """
    Correct glossary entries (fix detection boundaries).

    This endpoint allows users to fix incorrect text detection boundaries.
    For example, if "también Ezten lo" was detected but only "Ezten" should be,
    this allows correcting the original text in the glossary.

    The document is regenerated with the corrected boundaries.
    """
    session_id = get_session_id(request)
    project_id_str = str(project_id)

    # Check project exists
    if not session_manager.get_project(session_id, project_id_str):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get glossary from session
    glossary_entries = session_manager.get_glossary(session_id, project_id_str)
    changes_applied = 0
    changes_failed = 0

    from datetime import datetime, timezone

    for correction in request_body.corrections:
        # Find the entry by ID or by old_original_text
        found = False
        for entry in glossary_entries:
            # Match by ID or by original text
            if (entry.get("id") == correction.entry_id or
                entry.get("original_text", "").lower() == correction.old_original_text.lower()):

                old_text = entry.get("original_text", "")
                new_text = correction.new_original_text
                old_alias = entry.get("alias", "")

                # ================================================================
                # CRITICAL FIX: Check if new text normalizes differently
                # If it does, this should be a NEW entity with a NEW alias,
                # not just an update to the existing entry.
                # ================================================================
                from contextsafe.application.services.normalization import (
                    normalize_pii_value,
                    values_match,
                )

                category = entry.get("category", "")
                old_normalized = normalize_pii_value(old_text, category)
                new_normalized = normalize_pii_value(new_text, category)

                # If normalization differs, this is a DIFFERENT entity
                if old_normalized != new_normalized:
                    # Check if new_text already exists in glossary
                    existing_entry = None
                    for other_entry in glossary_entries:
                        if other_entry is not entry and other_entry.get("category") == category:
                            if values_match(other_entry.get("original_text", ""), new_text, category):
                                existing_entry = other_entry
                                break

                    if existing_entry:
                        # Use existing alias for this normalized text
                        entry["alias"] = existing_entry.get("alias", old_alias)
                    else:
                        # Generate NEW alias for this different entity
                        # Find max number for this category and increment
                        prefix = old_alias.rsplit("_", 1)[0] if "_" in old_alias else "Dato"
                        max_num = 0
                        for other in glossary_entries:
                            other_alias = other.get("alias", "")
                            if other_alias.startswith(prefix + "_"):
                                try:
                                    num = int(other_alias.rsplit("_", 1)[1])
                                    max_num = max(max_num, num)
                                except (ValueError, IndexError):
                                    pass
                        new_alias = f"{prefix}_{max_num + 1:03d}"
                        entry["alias"] = new_alias

                # Update the original text
                entry["original_text"] = new_text

                # Track history
                if "history" not in entry:
                    entry["history"] = []
                history_entry = {
                    "action": "original_text_corrected",
                    "old_original_text": old_text,
                    "new_original_text": new_text,
                    "changed_at": datetime.now(timezone.utc).isoformat(),
                    "version": len(entry.get("history", [])) + 2,
                }
                # Track alias change if it happened
                new_alias = entry.get("alias", "")
                if new_alias != old_alias:
                    history_entry["old_alias"] = old_alias
                    history_entry["new_alias"] = new_alias
                    history_entry["action"] = "original_text_and_alias_changed"
                entry["history"].append(history_entry)
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                entry["version"] = len(entry["history"]) + 1

                changes_applied += 1
                found = True
                break

        if not found:
            changes_failed += 1

    # Save updated glossary to session
    session_manager.set_glossary(session_id, project_id_str, glossary_entries)

    # Regenerate all documents with corrected glossary
    document_regenerated = False

    if changes_applied > 0:
        session = session_manager.get_session(session_id)
        if session:
            # Sort by length (longest first) for replacement
            sorted_entries = sorted(
                glossary_entries,
                key=lambda e: len(e.get("original_text", "")),
                reverse=True,
            )

            project_docs = session.get_project_documents(project_id_str)
            for doc_id, doc in project_docs.items():
                original_text = doc.content or ""
                if original_text:
                    new_anonymized = original_text
                    for entry in sorted_entries:
                        orig = entry.get("original_text", "")
                        alias = entry.get("alias", "")
                        if orig and alias:
                            pattern = re.compile(re.escape(orig), re.IGNORECASE)
                            new_anonymized = pattern.sub(alias, new_anonymized)

                    session_manager.update_document(
                        session_id, doc_id,
                        anonymized={"original": original_text, "anonymized": new_anonymized}
                    )
                    document_regenerated = True

    return ApiResponse(
        data=CorrectGlossaryResponse(
            project_id=project_id_str,
            changes_applied=changes_applied,
            changes_failed=changes_failed,
            document_regenerated=document_regenerated,
        )
    )
