"""
Document routes.

Traceability:
- Contract: CNT-T4-DOCUMENTS-001
- Standard: consolidated_standards.yaml#vocabulary.dtos
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse

from contextsafe.api.middleware.session import get_session_id
from contextsafe.api.schemas import (
    DocumentResponse,
    ErrorResponse,
)
from contextsafe.api.schemas.response_wrapper import (
    ApiListResponse,
    ApiResponse,
    PaginatedMeta,
)
from contextsafe.api.session_manager import session_manager


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/v1/documents", tags=["documents"])

from contextsafe.api.services.document_processor import (
    process_document_real as _process_document_real,
    processing_tasks as _processing_tasks,
)


@router.post(
    "",
    response_model=ApiResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        409: {"model": ErrorResponse, "description": "Duplicate document"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def create_document(
    request: Request,
    project_id: UUID = Query(..., description="Project ID"),
    file: UploadFile = File(...),
) -> ApiResponse[DocumentResponse]:
    """
    Upload and ingest a new document.

    Accepts multipart/form-data with file upload.
    """
    session_id = get_session_id(request)
    project_id_str = str(project_id)

    # Check project exists in session
    if not session_manager.get_project(session_id, project_id_str):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Validate file size (10MB max)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB.",
        )

    # Determine format from filename
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    format_map = {"pdf": "pdf", "docx": "docx", "doc": "docx", "txt": "txt",
                  "png": "image", "jpg": "image", "jpeg": "image"}
    doc_format = format_map.get(ext, "txt")

    # Extract text from document using the container's text extractor
    extracted_text = ""
    page_count = 1
    try:
        from contextsafe.api.dependencies import get_text_extractor
        extractor = get_text_extractor()
        result = await extractor.extract(content, filename)
        if result.text.strip():
            extracted_text = result.text
            page_count = result.page_count
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"No se pudo extraer texto del documento: {filename}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed for {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo extraer texto del documento: {filename}",
        )

    # Add document to session
    doc = session_manager.add_document(
        session_id=session_id,
        filename=filename,
        page_count=page_count,
        project_id=project_id_str,
        format=doc_format,
        size_bytes=len(content),
        content=extracted_text,
        original_content=content,
    )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document",
        )

    now = datetime.utcnow()
    response = DocumentResponse(
        id=UUID(doc.id),
        project_id=project_id,
        filename=filename,
        state="pending",
        created_at=now,
        updated_at=now,
    )

    return ApiResponse(data=response)


@router.get(
    "/{document_id}",
    response_model=ApiResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_document(document_id: UUID, request: Request) -> ApiResponse[dict]:
    """Retrieve document metadata by ID."""
    session_id = get_session_id(request)
    doc = session_manager.get_document(session_id, str(document_id))
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Return full document info including progress for polling
    return ApiResponse(data={
        "id": doc.id,
        "projectId": doc.project_id,
        "filename": doc.filename,
        "format": doc.format,
        "state": doc.state,
        "progress": doc.progress,
        "currentEntity": doc.current_entity,
        "pageCount": doc.page_count,
        "entityCount": doc.entity_count,
        "expiresInSeconds": None,
        "createdAt": doc.created_at.isoformat(),
        "textContent": doc.content or "",
    })


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def delete_document(document_id: UUID, request: Request) -> Response:
    """Delete a document and its associated data."""
    session_id = get_session_id(request)
    doc_id_str = str(document_id)

    if not session_manager.get_document(session_id, doc_id_str):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    session_manager.delete_document(session_id, doc_id_str)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{document_id}/entities",
    response_model=ApiListResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_entities(document_id: UUID, request: Request) -> ApiListResponse[dict]:
    """Get detected PII entities for a document."""
    session_id = get_session_id(request)
    doc_id_str = str(document_id)

    doc = session_manager.get_document(session_id, doc_id_str)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    entities = doc.detected_pii or []
    return ApiListResponse(
        data=entities,
        meta=PaginatedMeta(total=len(entities), limit=100, offset=0),
    )


@router.get(
    "/{document_id}/anonymized",
    response_model=ApiResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_anonymized(document_id: UUID, request: Request) -> ApiResponse[dict]:
    """Get anonymized content for a document."""
    session_id = get_session_id(request)
    doc_id_str = str(document_id)

    doc = session_manager.get_document(session_id, doc_id_str)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    if not doc.anonymized:
        # Return original if not yet processed
        return ApiResponse(data={
            "originalText": doc.content or "",
            "anonymizedText": doc.content or "",
        })

    return ApiResponse(data={
        "originalText": doc.anonymized.get("original", ""),
        "anonymizedText": doc.anonymized.get("anonymized", ""),
    })


@router.post(
    "/{document_id}/process",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Processing started (async - use WebSocket for progress)"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        409: {"model": ErrorResponse, "description": "Already processing"},
    },
)
async def process_document(
    document_id: UUID,
    request: Request,
    level: str = Query(None, description="Anonymization level: BASIC, INTERMEDIATE, ADVANCED"),
) -> ApiResponse[dict]:
    """Start processing a document (detection + anonymization)."""
    session_id = get_session_id(request)
    doc_id_str = str(document_id)

    doc = session_manager.get_document(session_id, doc_id_str)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    if doc.state in ["ingesting", "detecting", "anonymizing"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed",
        )

    # Si se pasa nivel, actualizar el proyecto con ese nivel
    project_id = doc.project_id
    if level and project_id:
        project_data = session_manager.get_project(session_id, project_id)
        if project_data:
            project_data["anonymization_level"] = level.upper()
            session_manager.update_project(session_id, project_id, project_data)

    # CRITICAL: Update state to "ingesting" BEFORE creating task
    # This ensures frontend polling sees the correct state immediately
    session_manager.update_document(session_id, doc_id_str, state="ingesting")

    # Start async processing with real NER detection
    task = asyncio.create_task(_process_document_real(doc_id_str, project_id, session_id))
    _processing_tasks[doc_id_str] = task

    return ApiResponse(data={
        "documentId": doc_id_str,
        "status": "processing_started",
        "state": "ingesting",
        "message": f"Document processing has been initiated with level {level or 'default'}",
    })


@router.post(
    "/batch/process",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Batch processing started (async)"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def batch_process_documents(
    request: Request,
    document_ids: list[str] = Query(..., description="List of document IDs to process"),
) -> ApiResponse[dict]:
    """
    Start batch processing for multiple documents.

    Processes all specified documents concurrently.
    Use WebSocket connections per document to track individual progress.
    """
    session_id = get_session_id(request)
    started = []
    skipped = []
    not_found = []

    for doc_id in document_ids:
        doc = session_manager.get_document(session_id, doc_id)
        if not doc:
            not_found.append(doc_id)
            continue

        if doc.state in ["ingesting", "detecting", "anonymizing"]:
            skipped.append({"id": doc_id, "reason": "already_processing"})
            continue

        # Start async processing
        project_id = doc.project_id
        task = asyncio.create_task(_process_document_real(doc_id, project_id, session_id))
        _processing_tasks[doc_id] = task
        started.append(doc_id)

    return ApiResponse(data={
        "started": started,
        "skipped": skipped,
        "not_found": not_found,
        "total_started": len(started),
        "message": f"Batch processing started for {len(started)} documents",
    })


@router.post(
    "/project/{project_id}/process-all",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "All documents processing started (async)"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def process_all_project_documents(project_id: UUID, request: Request) -> ApiResponse[dict]:
    """
    Process all pending documents in a project.

    Finds all documents with state 'pending' or 'failed' and starts processing.
    """
    session_id = get_session_id(request)
    project_id_str = str(project_id)

    if not session_manager.get_project(session_id, project_id_str):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Find all pending/failed documents for this project
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session not found")

    project_docs = session.get_project_documents(project_id_str)
    pending_docs = [
        doc for doc in project_docs.values()
        if doc.state in ["pending", "error"]
    ]

    started = []
    for doc in pending_docs:
        if doc.state not in ["ingesting", "detecting", "anonymizing"]:
            task = asyncio.create_task(_process_document_real(doc.id, project_id_str, session_id))
            _processing_tasks[doc.id] = task
            started.append(doc.id)

    return ApiResponse(data={
        "project_id": project_id_str,
        "started": started,
        "total_started": len(started),
        "total_pending": len(pending_docs),
        "message": f"Started processing {len(started)} documents",
    })


@router.post(
    "/{document_id}/validate",
    response_model=ApiResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def validate_document_pii(
    document_id: UUID,
    request: Request,
    strict: bool = Query(True, description="Check HIGH severity PII too"),
) -> ApiResponse[dict]:
    """
    Validate anonymized document for residual PII before export.

    Scans the anonymized text for critical PII (DNI, SS, bank accounts, etc.)
    that should have been anonymized. Returns validation status.

    Use this endpoint to check if a document is safe to export.
    """
    session_id = get_session_id(request)
    doc_id_str = str(document_id)

    doc = session_manager.get_document(session_id, doc_id_str)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    if not doc.anonymized:
        return ApiResponse(data={
            "valid": False,
            "status": "NOT_ANONYMIZED",
            "message": "El documento no ha sido anonimizado. Procese el documento primero.",
        })

    # Import and run validation
    from contextsafe.api.services.pii_validation import validate_no_critical_pii

    anonymized_text = doc.anonymized.get("anonymized", "")
    pii_matches = validate_no_critical_pii(anonymized_text, strict=strict)

    if pii_matches:
        critical = [m for m in pii_matches if m.severity == "CRITICAL"]
        high = [m for m in pii_matches if m.severity == "HIGH"]

        return ApiResponse(data={
            "valid": False,
            "status": "PII_DETECTED",
            "message": f"Se detectaron {len(pii_matches)} datos personales sin anonimizar",
            "critical_count": len(critical),
            "high_count": len(high),
            "details": [
                {
                    "category": m.category,
                    "value": m.value[:3] + "***" if len(m.value) > 3 else "***",
                    "severity": m.severity,
                }
                for m in pii_matches[:10]
            ],
            "recommendation": "Reprocese el documento con la detección NER actualizada.",
        })

    return ApiResponse(data={
        "valid": True,
        "status": "SAFE_TO_EXPORT",
        "message": "El documento está correctamente anonimizado y es seguro exportar.",
    })


@router.post(
    "/{document_id}/export",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        422: {"model": ErrorResponse, "description": "PII detected - export blocked"},
    },
)
async def export_document(
    document_id: UUID,
    request: Request,
    format: str = Query("txt", description="Export format: pdf, docx, txt"),
    skip_pii_check: bool = Query(False, description="Skip PII validation (NOT recommended)"),
) -> StreamingResponse:
    """
    Export anonymized document in specified format.

    **POLICY GATE**: Validates no critical PII remains before export.
    If DNI, SS, bank accounts found -> export BLOCKED (HTTP 422).
    """
    session_id = get_session_id(request)
    doc_id_str = str(document_id)

    doc = session_manager.get_document(session_id, doc_id_str)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    if doc.anonymized:
        text_content = doc.anonymized.get("anonymized", doc.content or "")
    else:
        text_content = doc.content or ""

    # ============================================================
    # POLICY GATE: Block export if critical PII detected
    # ============================================================
    if not skip_pii_check:
        from contextsafe.api.services.pii_validation import (
            validate_no_critical_pii,
            format_pii_validation_error,
        )

        pii_matches = validate_no_critical_pii(text_content, strict=True)
        if pii_matches:
            error_detail = format_pii_validation_error(pii_matches)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_detail,
            )

    filename_base = doc.filename.rsplit(".", 1)[0]
    title = f"Documento Anonimizado: {filename_base}"

    if format == "pdf":
        from contextsafe.api.routes.export import _generate_pdf_content
        pdf_bytes = _generate_pdf_content(text_content, title)
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}_anonimizado.pdf"'},
        )

    elif format == "docx":
        from contextsafe.api.routes.export import _generate_docx_content
        docx_bytes = _generate_docx_content(text_content, title)
        return StreamingResponse(
            iter([docx_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}_anonimizado.docx"'},
        )

    else:
        # Default: TXT
        return StreamingResponse(
            iter([text_content.encode("utf-8")]),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}_anonimizado.txt"'},
        )


# Note: Glossary is now stored in SessionManager
# Use session_manager.get_glossary(session_id, project_id) instead


# ============================================================================
# ENTITY REVIEW (HITL - Human In The Loop)
# ============================================================================

@router.post(
    "/{document_id}/entities/{entity_id}/review",
    response_model=ApiResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Document or entity not found"},
        400: {"model": ErrorResponse, "description": "Invalid review action"},
    },
)
async def review_entity(
    document_id: UUID,
    entity_id: UUID,
    request: Request,
) -> ApiResponse[dict]:
    """
    Review a detected entity (approve, reject, or correct).

    This endpoint allows human reviewers to validate NER detections,
    particularly for AMBER zone (medium confidence) entities.

    Actions:
    - APPROVED: Confirm the detection is correct
    - REJECTED: Mark as false positive (will be removed from anonymization)
    - CORRECTED: Fix category or value (requires newCategory/newValue)
    """
    session_id = get_session_id(request)
    doc_id_str = str(document_id)
    entity_id_str = str(entity_id)

    # Parse request body
    try:
        body = await request.json()
    except Exception:
        body = {}

    action = body.get("action", "APPROVED").upper()
    new_category = body.get("newCategory")
    new_value = body.get("newValue")
    review_time_ms = body.get("reviewTimeMs", 0)

    # Validate action
    valid_actions = {"APPROVED", "REJECTED", "CORRECTED"}
    if action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Valid: {', '.join(valid_actions)}",
        )

    # Get document
    doc = session_manager.get_document(session_id, doc_id_str)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Find entity in detected_pii
    entities = doc.detected_pii or []
    entity_found = False

    for entity in entities:
        if entity.get("id") == entity_id_str:
            entity_found = True
            entity["reviewed"] = True
            entity["review_action"] = action

            # Apply corrections if action is CORRECTED
            if action == "CORRECTED":
                old_alias = entity.get("alias", "")
                old_category = entity.get("category", "")

                if new_category:
                    entity["category"] = new_category.upper()
                if new_value:
                    entity["original_text"] = new_value

                # Regenerate alias for the new category
                if new_category and new_category.upper() != old_category:
                    new_cat_upper = new_category.upper()
                    # Find highest counter for the new category across all entities
                    alias_patterns = {
                        "PERSON_NAME": "Persona",
                        "ORGANIZATION": "Org",
                        "ADDRESS": "Dir",
                        "DNI_NIE": "Doc",
                        "PASSPORT": "Pasaporte",
                        "PHONE": "Tel",
                        "EMAIL": "Email",
                        "BANK_ACCOUNT": "Cuenta",
                        "CREDIT_CARD": "Tarjeta",
                        "DATE": "Fecha",
                        "MEDICAL_RECORD": "Historial",
                        "LICENSE_PLATE": "Matricula",
                        "SOCIAL_SECURITY": "SS",
                    }
                    prefix = alias_patterns.get(new_cat_upper, new_cat_upper)
                    max_counter = 0
                    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
                    for e in entities:
                        m = pattern.match(e.get("alias", ""))
                        if m:
                            max_counter = max(max_counter, int(m.group(1)))
                    new_alias = f"{prefix}_{str(max_counter + 1).zfill(3)}"
                    entity["alias"] = new_alias

                    # Update glossary: remove old entry, add new one
                    project_id = doc.project_id
                    if project_id:
                        glossary = session_manager.get_glossary(session_id, project_id)
                        # Remove old glossary entry for this alias
                        glossary = [g for g in glossary if g.get("alias") != old_alias]
                        # Add new entry
                        glossary.append({
                            "id": str(uuid4()),
                            "original_text": entity["original_text"],
                            "alias": new_alias,
                            "category": new_cat_upper,
                            "occurrences": 1,
                            "created_at": datetime.utcnow().isoformat(),
                            "reversible": True,
                        })
                        session_manager.set_glossary(session_id, project_id, glossary)

                    # Update anonymized text: replace old alias with new alias
                    if doc.anonymized and old_alias:
                        anon_text = doc.anonymized.get("anonymized", "")
                        if old_alias in anon_text:
                            anon_text = anon_text.replace(old_alias, new_alias)
                            doc.anonymized["anonymized"] = anon_text

            break

    if not entity_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found in document",
        )

    # Update document with reviewed entities
    session_manager.update_document(session_id, doc_id_str, detected_pii=entities)

    # Calculate review summary
    total = len(entities)
    reviewed = sum(1 for e in entities if e.get("reviewed"))
    approved = sum(1 for e in entities if e.get("review_action") == "APPROVED")
    rejected = sum(1 for e in entities if e.get("review_action") == "REJECTED")
    corrected = sum(1 for e in entities if e.get("review_action") == "CORRECTED")
    pending = total - reviewed

    review_summary = {
        "total": total,
        "reviewed": reviewed,
        "approved": approved,
        "rejected": rejected,
        "corrected": corrected,
        "pending": pending,
        "progress": round(reviewed / total * 100, 1) if total > 0 else 100,
    }

    # Build response data
    response_data: dict[str, Any] = {
        "entityId": entity_id_str,
        "action": action,
        "reviewSummary": review_summary,
    }

    # Include updated entity data for CORRECTED actions
    if action == "CORRECTED":
        for entity in entities:
            if entity.get("id") == entity_id_str:
                response_data["newAlias"] = entity.get("alias", "")
                response_data["newCategory"] = entity.get("category", "")
                break

    return ApiResponse(data=response_data)


@router.post(
    "/{document_id}/entities/batch-review",
    response_model=ApiResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def batch_review_entities(
    document_id: UUID,
    request: Request,
) -> ApiResponse[dict]:
    """
    Batch review all entities in a confidence zone.

    Typically used to approve all GREEN zone (high confidence) entities at once.
    """
    session_id = get_session_id(request)
    doc_id_str = str(document_id)

    # Parse request body
    try:
        body = await request.json()
    except Exception:
        body = {}

    zone = body.get("zone", "GREEN").upper()
    action = body.get("action", "APPROVED").upper()

    # Get document
    doc = session_manager.get_document(session_id, doc_id_str)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Define zone thresholds
    zone_thresholds = {
        "GREEN": (0.85, 1.0),
        "AMBER": (0.40, 0.85),
        "RED": (0.0, 0.40),
    }

    if zone not in zone_thresholds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid zone. Valid: GREEN, AMBER, RED",
        )

    min_conf, max_conf = zone_thresholds[zone]

    # Update entities in zone
    entities = doc.detected_pii or []
    entities_approved = 0

    for entity in entities:
        confidence = entity.get("confidence", 0)
        if min_conf <= confidence < max_conf and not entity.get("reviewed"):
            entity["reviewed"] = True
            entity["review_action"] = action
            entities_approved += 1

    # Update document
    session_manager.update_document(session_id, doc_id_str, detected_pii=entities)

    # Calculate review summary
    total = len(entities)
    reviewed = sum(1 for e in entities if e.get("reviewed"))
    approved = sum(1 for e in entities if e.get("review_action") == "APPROVED")
    rejected = sum(1 for e in entities if e.get("review_action") == "REJECTED")
    corrected = sum(1 for e in entities if e.get("review_action") == "CORRECTED")
    pending = total - reviewed

    review_summary = {
        "total": total,
        "reviewed": reviewed,
        "approved": approved,
        "rejected": rejected,
        "corrected": corrected,
        "pending": pending,
        "progress": round(reviewed / total * 100, 1) if total > 0 else 100,
    }

    return ApiResponse(data={
        "entitiesApproved": entities_approved,
        "zone": zone,
        "reviewSummary": review_summary,
    })


# ============================================================================
# PII CATEGORIES
# ============================================================================

# Canonical list of PII categories with Spanish labels
PII_CATEGORIES = [
    {"id": "PERSON_NAME", "label": "Nombre de persona", "group": "identity"},
    {"id": "ORGANIZATION", "label": "Organización", "group": "identity"},
    {"id": "ADDRESS", "label": "Dirección", "group": "location"},
    {"id": "LOCATION", "label": "Ubicación", "group": "location"},
    {"id": "POSTAL_CODE", "label": "Código Postal", "group": "location"},
    {"id": "DNI_NIE", "label": "DNI/NIE", "group": "documents"},
    {"id": "PASSPORT", "label": "Pasaporte", "group": "documents"},
    {"id": "PHONE", "label": "Teléfono", "group": "contact"},
    {"id": "EMAIL", "label": "Email", "group": "contact"},
    {"id": "IBAN", "label": "IBAN", "group": "financial"},
    {"id": "BANK_ACCOUNT", "label": "Cuenta bancaria", "group": "financial"},
    {"id": "CREDIT_CARD", "label": "Tarjeta de crédito", "group": "financial"},
    {"id": "DATE", "label": "Fecha", "group": "temporal"},
    {"id": "MEDICAL_RECORD", "label": "Historia clínica", "group": "health"},
    {"id": "LICENSE_PLATE", "label": "Matrícula", "group": "vehicle"},
    {"id": "SOCIAL_SECURITY", "label": "Seguridad Social", "group": "documents"},
    {"id": "PROFESSIONAL_ID", "label": "ID Profesional", "group": "documents"},
    {"id": "CASE_NUMBER", "label": "Nº Procedimiento", "group": "legal"},
    {"id": "PLATFORM", "label": "Plataforma", "group": "digital"},
    {"id": "IP_ADDRESS", "label": "Dirección IP", "group": "digital"},
]


@router.get(
    "/categories",
    response_model=ApiResponse[list],
)
async def list_pii_categories() -> ApiResponse[list]:
    """
    List all available PII categories.

    Returns categories with id, label (Spanish), and group for UI rendering.
    Used by the entity review UI to populate the category correction dropdown.
    """
    return ApiResponse(data=PII_CATEGORIES)


# ============================================================================
# MANUAL ANONYMIZATION
# ============================================================================

@router.post(
    "/{document_id}/anonymize-selection",
    response_model=ApiResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def anonymize_selection(
    document_id: UUID,
    request: Request,
    text: str = Query(..., description="Selected text to anonymize"),
    category: str = Query(..., description="PII category (e.g., PERSON_NAME, DNI_NIE, PHONE)"),
    alias: str = Query(None, description="Custom alias (auto-generated if not provided)"),
) -> ApiResponse[dict]:
    """
    Manually anonymize a selected text.

    This allows users to anonymize text that wasn't detected automatically,
    such as professional license numbers (numero de colegiado), case numbers, etc.

    The text is added to the project glossary and the document is regenerated.
    """
    import re

    session_id = get_session_id(request)
    doc_id_str = str(document_id)

    # Check document exists
    doc = session_manager.get_document(session_id, doc_id_str)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    project_id = doc.project_id
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no project association",
        )

    # Validate the text exists in the original document
    original_text = doc.content or ""
    if text not in original_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Selected text not found in document",
        )

    # Get anonymization level from project
    project_data = session_manager.get_project(session_id, project_id)
    anonymization_level = (project_data.get("anonymization_level", "INTERMEDIATE") if project_data else "INTERMEDIATE").upper()
    is_masking_level = anonymization_level == "BASIC"

    # Normalize category
    category_upper = category.upper().replace("-", "_").replace(" ", "_")

    # Valid categories
    valid_categories = {
        "PERSON_NAME", "ORGANIZATION", "ADDRESS", "POSTAL_CODE",
        "DNI_NIE", "PASSPORT", "PHONE", "EMAIL", "BANK_ACCOUNT",
        "CREDIT_CARD", "DATE", "MEDICAL_RECORD", "LICENSE_PLATE",
        "SOCIAL_SECURITY", "OTHER"
    }

    if category_upper not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Valid: {', '.join(sorted(valid_categories))}",
        )

    # Get glossary from session
    glossary = session_manager.get_glossary(session_id, project_id)

    # Check if text is already in glossary
    existing = next(
        (e for e in glossary if e.get("original_text", "").lower() == text.lower()),
        None
    )

    if existing:
        # Update existing entry with new alias if provided (only for non-BASIC)
        if alias and not is_masking_level:
            existing["alias"] = alias
        generated_alias = existing["alias"]
    else:
        # Generate alias based on anonymization level
        if is_masking_level:
            # BASIC level: use asterisks (masking)
            # Preserve word structure: "Juan Pérez" → "***** ******"
            words = text.split()
            masked_words = ["*" * max(len(word), 5) for word in words]
            generated_alias = " ".join(masked_words)
        elif not alias:
            # INTERMEDIATE/ADVANCED: generate pseudonym
            category_prefix = {
                "PERSON_NAME": "Persona",
                "ORGANIZATION": "Org",
                "ADDRESS": "Dir",
                "POSTAL_CODE": "CP",
                "DNI_NIE": "ID",
                "PASSPORT": "Pasaporte",
                "PHONE": "Tel",
                "EMAIL": "Email",
                "BANK_ACCOUNT": "Cuenta",
                "CREDIT_CARD": "Tarjeta",
                "DATE": "Fecha",
                "MEDICAL_RECORD": "HistMed",
                "LICENSE_PLATE": "Matricula",
                "SOCIAL_SECURITY": "NSS",
                "OTHER": "Dato",
            }.get(category_upper, "Dato")

            existing_count = sum(
                1 for e in glossary
                if e.get("category", "").upper() == category_upper
            )
            generated_alias = f"{category_prefix}_{existing_count + 1:03d}"
        else:
            generated_alias = alias

        # Add to glossary
        session_manager.add_glossary_entry(session_id, project_id, {
            "id": str(uuid4()),
            "original_text": text,
            "alias": generated_alias,
            "category": category_upper,
            "occurrences": original_text.count(text),
            "created_at": datetime.utcnow().isoformat(),
            "manual": True,  # Mark as manually added
            "reversible": not is_masking_level,  # BASIC is not reversible
            "masking_level": anonymization_level,
        })

    # Regenerate anonymized text for this document
    anonymized_text = original_text

    # Get updated glossary and sort by length (longest first)
    glossary = session_manager.get_glossary(session_id, project_id)
    sorted_glossary = sorted(
        glossary,
        key=lambda e: len(e.get("original_text", "")),
        reverse=True,
    )

    for entry in sorted_glossary:
        orig = entry.get("original_text", "")
        entry_alias = entry.get("alias", "")
        if orig and entry_alias:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(orig), re.IGNORECASE)
            anonymized_text = pattern.sub(entry_alias, anonymized_text)

    # Update anonymized content in session
    session_manager.update_document(
        session_id, doc_id_str,
        anonymized={"original": original_text, "anonymized": anonymized_text}
    )

    return ApiResponse(data={
        "success": True,
        "text": text,
        "alias": generated_alias,
        "category": category_upper,
        "document_id": doc_id_str,
        "anonymized_text": anonymized_text,
        "message": f"'{text}' anonimizado como '{generated_alias}'",
    })
