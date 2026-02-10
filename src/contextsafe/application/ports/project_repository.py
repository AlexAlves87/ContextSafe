"""
ProjectRepository port.

Abstract interface for project persistence.

Traceability:
- Naming: find_by_* pattern per controlled_vocabulary.yaml
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from contextsafe.domain.project_management.aggregates.project import Project
from contextsafe.domain.shared.errors import RepositoryError
from contextsafe.domain.shared.types import Result
from contextsafe.domain.shared.value_objects import ProjectId


class ProjectRepository(ABC):
    """
    Port for project persistence.

    Implementations:
    - SQLiteProjectRepository (infrastructure layer)
    """

    @abstractmethod
    async def save(self, project: Project) -> Result[Project, RepositoryError]:
        """
        Save a project.

        Args:
            project: The project to save

        Returns:
            Ok[Project] with saved entity, Err[RepositoryError] on failure
        """
        ...

    @abstractmethod
    async def find_by_id(self, project_id: ProjectId) -> Optional[Project]:
        """
        Find a project by ID.

        Args:
            project_id: The project identifier

        Returns:
            The project if found, None otherwise
        """
        ...

    @abstractmethod
    async def find_by_owner(
        self,
        owner_id: str,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Project]:
        """
        Find projects by owner.

        Args:
            owner_id: The owner identifier
            include_inactive: Whether to include deactivated projects
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of projects owned by the user
        """
        ...

    @abstractmethod
    async def find_all(
        self,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Project]:
        """
        Find all projects.

        Args:
            include_inactive: Whether to include deactivated projects
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of all projects
        """
        ...

    @abstractmethod
    async def delete(self, project_id: ProjectId) -> Result[None, RepositoryError]:
        """
        Delete a project.

        Args:
            project_id: The project to delete

        Returns:
            Ok[None] if deleted, Err[RepositoryError] on failure
        """
        ...

    @abstractmethod
    async def exists_by_id(self, project_id: ProjectId) -> bool:
        """
        Check if a project exists.

        Args:
            project_id: The project identifier

        Returns:
            True if exists, False otherwise
        """
        ...
