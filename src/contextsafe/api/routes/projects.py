"""
Project routes.

Traceability:
- Contract: CNT-T4-PROJECTS-001
- Standard: consolidated_standards.yaml#vocabulary.dtos
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from contextsafe.api.middleware.session import get_session_id
from contextsafe.api.schemas import (
    ErrorResponse,
    ProjectRequest,
    ProjectResponse,
)
from contextsafe.api.schemas.response_wrapper import (
    ApiListResponse,
    ApiResponse,
    PaginatedMeta,
)
from contextsafe.api.session_manager import session_manager


router = APIRouter(prefix="/v1/projects", tags=["projects"])


@router.post(
    "",
    response_model=ApiResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        409: {"model": ErrorResponse, "description": "Project name exists"},
    },
)
async def create_project(
    request_body: ProjectRequest,
    request: Request,
) -> ApiResponse[ProjectResponse]:
    """Create a new project."""
    session_id = get_session_id(request)

    project_id = uuid4()
    now = datetime.utcnow()
    project = ProjectResponse(
        id=project_id,
        name=request_body.name,
        description=request_body.description,
        anonymization_level=request_body.default_anonymization_level.lower(),
        created_at=now,
        updated_at=now,
        document_count=0,
        entity_count=0,
        completion_percentage=0,
    )

    # Store in session
    project_data = project.model_dump() if hasattr(project, 'model_dump') else project.dict()
    session_manager.add_project(session_id, str(project_id), project_data)

    return ApiResponse(data=project)


@router.get(
    "/{project_id}",
    response_model=ApiResponse[ProjectResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def get_project(project_id: UUID, request: Request) -> ApiResponse[ProjectResponse]:
    """Retrieve project by ID."""
    session_id = get_session_id(request)

    project_data = session_manager.get_project(session_id, str(project_id))
    if not project_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    project = ProjectResponse(**project_data)
    return ApiResponse(data=project)


@router.put(
    "/{project_id}",
    response_model=ApiResponse[ProjectResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def update_project(
    project_id: UUID,
    request_body: ProjectRequest,
    request: Request,
) -> ApiResponse[ProjectResponse]:
    """Update project metadata."""
    session_id = get_session_id(request)

    project_data = session_manager.get_project(session_id, str(project_id))
    if not project_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Parse created_at from stored data
    created_at = project_data.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

    updated = ProjectResponse(
        id=project_id,
        name=request_body.name,
        description=request_body.description,
        anonymization_level=request_body.default_anonymization_level.lower(),
        created_at=created_at,
        updated_at=datetime.utcnow(),
        document_count=project_data.get("document_count", 0),
        entity_count=project_data.get("entity_count", 0),
        completion_percentage=project_data.get("completion_percentage", 0),
    )

    updated_data = updated.model_dump() if hasattr(updated, 'model_dump') else updated.dict()
    session_manager.update_project(session_id, str(project_id), updated_data)

    return ApiResponse(data=updated)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def delete_project(project_id: UUID, request: Request) -> Response:
    """Delete a project."""
    session_id = get_session_id(request)

    if not session_manager.get_project(session_id, str(project_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    session_manager.delete_project(session_id, str(project_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "",
    response_model=ApiListResponse[ProjectResponse],
)
async def list_projects(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> ApiListResponse[ProjectResponse]:
    """List all projects for this session."""
    session_id = get_session_id(request)

    all_projects_data = session_manager.list_projects(session_id)
    all_projects = [ProjectResponse(**p) for p in all_projects_data]

    total = len(all_projects)
    paginated = all_projects[offset:offset + limit]
    return ApiListResponse(
        data=paginated,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
    )


# ============================================================================
# PROJECT DOCUMENTS (UI-BIND-002)
# ============================================================================
@router.get(
    "/{project_id}/documents",
    response_model=ApiListResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def list_project_documents(
    project_id: UUID,
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> ApiListResponse[dict]:
    """List all documents in a project."""
    session_id = get_session_id(request)

    if not session_manager.get_project(session_id, str(project_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get documents from session
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session not found")

    project_docs = session.get_project_documents(str(project_id))
    docs = [
        {
            "id": doc.id,
            "filename": doc.filename,
            "format": doc.format,
            "state": doc.state,
            "entity_count": doc.entity_count,
            "page_count": doc.page_count,
            "created_at": doc.created_at.isoformat(),
        }
        for doc in project_docs.values()
    ]

    total = len(docs)
    paginated = docs[offset:offset + limit]
    return ApiListResponse(
        data=paginated,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
    )


# ============================================================================
# PROJECT SETTINGS (UI-BIND-008)
# ============================================================================
@router.get(
    "/{project_id}/settings",
    response_model=ApiResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def get_project_settings(project_id: UUID, request: Request) -> ApiResponse[dict]:
    """Get project settings."""
    session_id = get_session_id(request)

    project_data = session_manager.get_project(session_id, str(project_id))
    if not project_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return ApiResponse(
        data={
            "project_id": str(project_id),
            "default_anonymization_level": project_data.get("anonymization_level", "INTERMEDIATE"),
            "enabled_categories": [],
            "auto_detect": True,
        }
    )


@router.put(
    "/{project_id}/settings",
    response_model=ApiResponse[dict],
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def update_project_settings(
    project_id: UUID,
    settings: dict,
    request: Request,
) -> ApiResponse[dict]:
    """Update project settings."""
    session_id = get_session_id(request)

    project_data = session_manager.get_project(session_id, str(project_id))
    if not project_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Mapear campos de settings a campos del proyecto
    if "anonymizationLevel" in settings:
        project_data["anonymization_level"] = settings["anonymizationLevel"].upper()
    if "enabledCategories" in settings:
        project_data["enabled_categories"] = settings["enabledCategories"]
    if "preserveFormatting" in settings:
        project_data["preserve_formatting"] = settings["preserveFormatting"]
    if "maintainConsistency" in settings:
        project_data["maintain_consistency"] = settings["maintainConsistency"]
    if "generateAuditReport" in settings:
        project_data["generate_audit_report"] = settings["generateAuditReport"]

    # GUARDAR los cambios
    session_manager.update_project(session_id, str(project_id), project_data)

    return ApiResponse(
        data={
            "project_id": str(project_id),
            **settings,
        }
    )
