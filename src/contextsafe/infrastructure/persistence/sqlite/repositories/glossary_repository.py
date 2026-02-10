"""
SQLite implementation of GlossaryRepository.

Traceability:
- Contract: CNT-T3-SQLITE-GLOSSARY-REPO-001
- Port: ports.GlossaryRepository
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from contextsafe.application.ports import GlossaryRepository
from contextsafe.domain.anonymization.aggregates.glossary import Glossary
from contextsafe.domain.shared.errors import RepositoryError
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects import ProjectId
from contextsafe.infrastructure.persistence.models import GlossaryModel


class SQLiteGlossaryRepository(GlossaryRepository):
    """
    SQLite implementation of GlossaryRepository.

    Uses SQLAlchemy async session for database operations.
    Critical for maintaining alias consistency.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def save(self, glossary: Glossary) -> Result[Glossary, RepositoryError]:
        """
        Save or update a glossary.

        Args:
            glossary: The glossary to save

        Returns:
            Ok[Glossary] with saved entity, Err[RepositoryError] on failure
        """
        try:
            # Check if exists (by project_id, one glossary per project)
            stmt = select(GlossaryModel).where(GlossaryModel.project_id == str(glossary.project_id))
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.update_from_aggregate(glossary)
            else:
                model = GlossaryModel.from_aggregate(glossary)
                self._session.add(model)

            await self._session.flush()
            return Ok(glossary)

        except SQLAlchemyError as e:
            await self._session.rollback()
            return Err(RepositoryError(f"Database error: {e}"))

    async def find_by_project(self, project_id: ProjectId) -> Glossary | None:
        """
        Find the glossary for a project.

        Args:
            project_id: The project identifier

        Returns:
            The glossary if found, None otherwise
        """
        try:
            stmt = select(GlossaryModel).where(GlossaryModel.project_id == str(project_id))
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return Glossary.from_dict(model.to_dict())
        except SQLAlchemyError:
            return None

    async def get_or_create(self, project_id: ProjectId) -> Glossary:
        """
        Get existing glossary or create new one.

        Args:
            project_id: The project identifier

        Returns:
            Existing or new empty glossary
        """
        existing = await self.find_by_project(project_id)
        if existing:
            return existing

        # Create new empty glossary
        new_glossary = Glossary.create(project_id)
        save_result = await self.save(new_glossary)
        if save_result.is_ok():
            return save_result.unwrap()

        # Return in-memory glossary if save failed
        return new_glossary

    async def delete(self, project_id: ProjectId) -> Result[None, RepositoryError]:
        """
        Delete a glossary.

        Args:
            project_id: The project whose glossary to delete

        Returns:
            Ok[None] if deleted, Err[RepositoryError] on failure
        """
        try:
            stmt = select(GlossaryModel).where(GlossaryModel.project_id == str(project_id))
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                await self._session.delete(model)
                await self._session.flush()
            return Ok(None)
        except SQLAlchemyError as e:
            await self._session.rollback()
            return Err(RepositoryError(f"Delete failed: {e}"))
