"""
DocumentRepository port.

Abstract interface for document persistence.

Traceability:
- Standard: consolidated_standards.yaml#imports.components.DocumentRepository
- Naming: find_by_* pattern per controlled_vocabulary.yaml
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from contextsafe.domain.document_processing.aggregates.document_aggregate import (
    DocumentAggregate,
)
from contextsafe.domain.shared.errors import RepositoryError
from contextsafe.domain.shared.types import Result
from contextsafe.domain.shared.value_objects import DocumentId, ProjectId


class DocumentRepository(ABC):
    """
    Port for document persistence.

    Implementations:
    - SQLiteDocumentRepository (infrastructure layer)
    """

    @abstractmethod
    async def save(
        self, aggregate: DocumentAggregate
    ) -> Result[DocumentAggregate, RepositoryError]:
        """
        Save a document aggregate.

        Args:
            aggregate: The document aggregate to save

        Returns:
            Ok[DocumentAggregate] with saved entity, Err[RepositoryError] on failure
        """
        ...

    @abstractmethod
    async def find_by_id(
        self, document_id: DocumentId
    ) -> Optional[DocumentAggregate]:
        """
        Find a document by ID.

        Args:
            document_id: The document identifier

        Returns:
            The document if found, None otherwise
        """
        ...

    @abstractmethod
    async def find_by_project(
        self,
        project_id: ProjectId,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DocumentAggregate]:
        """
        Find all documents for a project.

        Args:
            project_id: The project identifier
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of documents in the project
        """
        ...

    @abstractmethod
    async def delete(self, document_id: DocumentId) -> Result[None, RepositoryError]:
        """
        Delete a document.

        Args:
            document_id: The document to delete

        Returns:
            Ok[None] if deleted, Err[RepositoryError] on failure
        """
        ...

    @abstractmethod
    async def exists_by_id(self, document_id: DocumentId) -> bool:
        """
        Check if a document exists.

        Args:
            document_id: The document identifier

        Returns:
            True if exists, False otherwise
        """
        ...

    @abstractmethod
    async def count_by_project(self, project_id: ProjectId) -> int:
        """
        Count documents in a project.

        Args:
            project_id: The project identifier

        Returns:
            Number of documents
        """
        ...
