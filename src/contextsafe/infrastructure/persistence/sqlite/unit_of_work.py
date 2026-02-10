"""
SQLite Unit of Work implementation.

Manages transaction boundaries for SQLite operations.

Traceability:
- Contract: CNT-T3-SQLITE-UOW-001
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from contextsafe.domain.shared.errors import RepositoryError
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.infrastructure.persistence.sqlite.repositories import (
    SQLiteDocumentRepository,
    SQLiteGlossaryRepository,
    SQLiteProjectRepository,
)


class SQLiteUnitOfWork:
    """
    Unit of Work pattern for SQLite.

    Manages transaction boundaries and provides access to repositories.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        """
        Initialize unit of work with session factory.

        Args:
            session_factory: Factory function that creates new sessions
        """
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._documents: SQLiteDocumentRepository | None = None
        self._projects: SQLiteProjectRepository | None = None
        self._glossaries: SQLiteGlossaryRepository | None = None

    async def __aenter__(self) -> SQLiteUnitOfWork:
        """
        Enter the unit of work context.

        Creates a new session and initializes repositories.
        """
        self._session = self._session_factory()
        self._documents = SQLiteDocumentRepository(self._session)
        self._projects = SQLiteProjectRepository(self._session)
        self._glossaries = SQLiteGlossaryRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the unit of work context.

        Rolls back on exception, then closes session.
        """
        if exc_type is not None:
            await self.rollback()
        if self._session:
            await self._session.close()

    @property
    def documents(self) -> SQLiteDocumentRepository:
        """Get the document repository."""
        if self._documents is None:
            raise RuntimeError("Unit of work not started")
        return self._documents

    @property
    def projects(self) -> SQLiteProjectRepository:
        """Get the project repository."""
        if self._projects is None:
            raise RuntimeError("Unit of work not started")
        return self._projects

    @property
    def glossaries(self) -> SQLiteGlossaryRepository:
        """Get the glossary repository."""
        if self._glossaries is None:
            raise RuntimeError("Unit of work not started")
        return self._glossaries

    async def commit(self) -> Result[None, RepositoryError]:
        """
        Commit the current transaction.

        Returns:
            Ok[None] if successful, Err[RepositoryError] on failure
        """
        if self._session is None:
            return Err(RepositoryError("Session not initialized"))

        try:
            await self._session.commit()
            return Ok(None)
        except SQLAlchemyError as e:
            await self._session.rollback()
            return Err(RepositoryError(f"Commit failed: {e}"))

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session:
            await self._session.rollback()
