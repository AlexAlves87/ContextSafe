"""
SQLite implementation of DocumentRepository.

Traceability:
- Contract: CNT-T3-SQLITE-DOCUMENT-REPO-001
- Port: ports.DocumentRepository
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from contextsafe.application.ports import DocumentRepository
from contextsafe.domain.document_processing.aggregates.document_aggregate import (
    DocumentAggregate,
)
from contextsafe.domain.shared.errors import RepositoryError
from contextsafe.domain.shared.types import Err, Ok, Result
from contextsafe.domain.shared.value_objects import DocumentId, ProjectId
from contextsafe.infrastructure.persistence.models import DocumentModel


class SQLiteDocumentRepository(DocumentRepository):
    """
    SQLite implementation of DocumentRepository.

    Uses SQLAlchemy async session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def save(
        self, aggregate: DocumentAggregate
    ) -> Result[DocumentAggregate, RepositoryError]:
        """
        Save or update a document aggregate.

        Uses upsert semantics (merge).

        Args:
            aggregate: The document aggregate to save

        Returns:
            Ok[DocumentAggregate] with saved entity, Err[RepositoryError] on failure
        """
        try:
            # Check if exists
            existing = await self._session.get(DocumentModel, str(aggregate.id))

            if existing:
                existing.update_from_aggregate(aggregate)
            else:
                model = DocumentModel.from_aggregate(aggregate)
                self._session.add(model)

            await self._session.flush()
            return Ok(aggregate)

        except IntegrityError as e:
            await self._session.rollback()
            return Err(RepositoryError(f"Integrity error: {e}"))
        except SQLAlchemyError as e:
            await self._session.rollback()
            return Err(RepositoryError(f"Database error: {e}"))

    async def find_by_id(self, document_id: DocumentId) -> DocumentAggregate | None:
        """
        Find a document by ID.

        Args:
            document_id: The document identifier

        Returns:
            The document aggregate if found, None otherwise
        """
        try:
            model = await self._session.get(DocumentModel, str(document_id))
            if model is None:
                return None

            return DocumentAggregate.from_dict(model.to_dict())
        except SQLAlchemyError:
            return None

    async def find_by_project(
        self,
        project_id: ProjectId,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DocumentAggregate]:
        """
        Find all documents for a project.

        Args:
            project_id: The project identifier
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of document aggregates in the project
        """
        try:
            stmt = (
                select(DocumentModel)
                .where(DocumentModel.project_id == str(project_id))
                .order_by(DocumentModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [DocumentAggregate.from_dict(m.to_dict()) for m in models]
        except SQLAlchemyError:
            return []

    async def delete(self, document_id: DocumentId) -> Result[None, RepositoryError]:
        """
        Delete a document.

        Args:
            document_id: The document to delete

        Returns:
            Ok[None] if deleted, Err[RepositoryError] on failure
        """
        try:
            model = await self._session.get(DocumentModel, str(document_id))
            if model:
                await self._session.delete(model)
                await self._session.flush()
            return Ok(None)
        except SQLAlchemyError as e:
            await self._session.rollback()
            return Err(RepositoryError(f"Delete failed: {e}"))

    async def exists_by_id(self, document_id: DocumentId) -> bool:
        """
        Check if a document exists.

        Args:
            document_id: The document identifier

        Returns:
            True if exists, False otherwise
        """
        try:
            stmt = select(DocumentModel.id).where(DocumentModel.id == str(document_id))
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError:
            return False

    async def count_by_project(self, project_id: ProjectId) -> int:
        """
        Count documents in a project.

        Args:
            project_id: The project identifier

        Returns:
            Number of documents
        """
        try:
            from sqlalchemy import func

            stmt = select(func.count()).where(DocumentModel.project_id == str(project_id))
            result = await self._session.execute(stmt)
            count = result.scalar_one()
            return count if count else 0
        except SQLAlchemyError:
            return 0
