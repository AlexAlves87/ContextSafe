"""
SQLite implementation of ProjectRepository.

Traceability:
- Contract: CNT-T3-SQLITE-PROJECT-REPO-001
- Port: ports.ProjectRepository
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from contextsafe.application.ports import ProjectRepository
from contextsafe.domain.project_management.aggregates.project import Project
from contextsafe.domain.shared.errors import RepositoryError
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects import ProjectId
from contextsafe.infrastructure.persistence.models import ProjectModel


class SQLiteProjectRepository(ProjectRepository):
    """
    SQLite implementation of ProjectRepository.

    Uses SQLAlchemy async session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def save(self, project: Project) -> Result[Project, RepositoryError]:
        """
        Save or update a project.

        Args:
            project: The project to save

        Returns:
            Ok[Project] with saved entity, Err[RepositoryError] on failure
        """
        try:
            existing = await self._session.get(ProjectModel, str(project.id))

            if existing:
                existing.update_from_aggregate(project)
            else:
                model = ProjectModel.from_aggregate(project)
                self._session.add(model)

            await self._session.flush()
            return Ok(project)

        except IntegrityError as e:
            await self._session.rollback()
            if "UNIQUE constraint" in str(e):
                return Err(RepositoryError("Project name already exists"))
            return Err(RepositoryError(f"Integrity error: {e}"))
        except SQLAlchemyError as e:
            await self._session.rollback()
            return Err(RepositoryError(f"Database error: {e}"))

    async def find_by_id(self, project_id: ProjectId) -> Project | None:
        """
        Find a project by ID.

        Args:
            project_id: The project identifier

        Returns:
            The project if found, None otherwise
        """
        try:
            model = await self._session.get(ProjectModel, str(project_id))
            if model is None:
                return None

            return Project.from_dict(model.to_dict())
        except SQLAlchemyError:
            return None

    async def find_by_owner(
        self,
        owner_id: str,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Project]:
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
        try:
            stmt = (
                select(ProjectModel)
                .where(ProjectModel.owner_id == owner_id)
                .order_by(ProjectModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [Project.from_dict(m.to_dict()) for m in models]
        except SQLAlchemyError:
            return []

    async def find_all(
        self,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Project]:
        """
        Find all projects.

        Args:
            include_inactive: Whether to include deactivated projects
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of all projects
        """
        try:
            stmt = (
                select(ProjectModel)
                .order_by(ProjectModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [Project.from_dict(m.to_dict()) for m in models]
        except SQLAlchemyError:
            return []

    async def delete(self, project_id: ProjectId) -> Result[None, RepositoryError]:
        """
        Delete a project.

        Args:
            project_id: The project to delete

        Returns:
            Ok[None] if deleted, Err[RepositoryError] on failure
        """
        try:
            model = await self._session.get(ProjectModel, str(project_id))
            if model:
                await self._session.delete(model)
                await self._session.flush()
            return Ok(None)
        except SQLAlchemyError as e:
            await self._session.rollback()
            return Err(RepositoryError(f"Delete failed: {e}"))

    async def exists_by_id(self, project_id: ProjectId) -> bool:
        """
        Check if a project exists.

        Args:
            project_id: The project identifier

        Returns:
            True if exists, False otherwise
        """
        try:
            stmt = select(ProjectModel.id).where(ProjectModel.id == str(project_id))
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError:
            return False
