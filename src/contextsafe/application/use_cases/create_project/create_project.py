"""
CreateProject use case.

Handles project creation.

Traceability:
- Bounded Context: BC-004 (ProjectManagement)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from contextsafe.application.ports import EventPublisher, ProjectRepository
from contextsafe.domain.project_management.aggregates.project import Project
from contextsafe.domain.shared.errors import DomainError
from contextsafe.domain.shared.types import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class CreateProjectRequest:
    """Input for project creation."""

    name: str
    owner_id: str
    description: str = ""
    settings: Optional[dict[str, Any]] = None


@dataclass(frozen=True, slots=True)
class CreateProjectResponse:
    """Output from project creation."""

    project_id: str
    name: str
    owner_id: str
    created_at: str


class CreateProject:
    """
    Use case for creating a new project.

    Steps:
    1. Validate input
    2. Create project aggregate
    3. Save to repository
    4. Return response
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._project_repo = project_repository
        self._event_publisher = event_publisher

    async def execute(
        self, request: CreateProjectRequest
    ) -> Result[CreateProjectResponse, DomainError]:
        """
        Execute the create project use case.

        Args:
            request: The creation request

        Returns:
            Ok[CreateProjectResponse] on success, Err[DomainError] on failure
        """
        # 1. Create project aggregate
        project_result = Project.create(
            name=request.name,
            owner_id=request.owner_id,
            description=request.description,
            settings=request.settings,
        )

        if project_result.is_err():
            return Err(project_result.unwrap_err())

        project = project_result.unwrap()

        # 2. Save to repository
        save_result = await self._project_repo.save(project)
        if save_result.is_err():
            return Err(save_result.unwrap_err())

        saved_project = save_result.unwrap()

        # 3. Return response
        return Ok(
            CreateProjectResponse(
                project_id=str(saved_project.id),
                name=saved_project.name,
                owner_id=saved_project.owner_id,
                created_at=saved_project.created_at.isoformat(),
            )
        )
