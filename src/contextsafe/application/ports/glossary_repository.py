"""
GlossaryRepository port.

Abstract interface for glossary persistence.

Traceability:
- Standard: consolidated_standards.yaml#imports.components.GlossaryRepository
- Business Rule: BR-002 (Alias Consistency)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from contextsafe.domain.anonymization.aggregates.glossary import Glossary
from contextsafe.domain.shared.errors import RepositoryError
from contextsafe.domain.shared.types import Result
from contextsafe.domain.shared.value_objects import ProjectId


class GlossaryRepository(ABC):
    """
    Port for glossary persistence.

    Critical for maintaining alias consistency across sessions.

    Implementations:
    - SQLiteGlossaryRepository (infrastructure layer)
    """

    @abstractmethod
    async def save(self, glossary: Glossary) -> Result[Glossary, RepositoryError]:
        """
        Save a glossary.

        Args:
            glossary: The glossary to save

        Returns:
            Ok[Glossary] with saved entity, Err[RepositoryError] on failure
        """
        ...

    @abstractmethod
    async def find_by_project(self, project_id: ProjectId) -> Optional[Glossary]:
        """
        Find the glossary for a project.

        Each project has exactly one glossary.

        Args:
            project_id: The project identifier

        Returns:
            The glossary if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_or_create(self, project_id: ProjectId) -> Glossary:
        """
        Get existing glossary or create new one.

        Args:
            project_id: The project identifier

        Returns:
            Existing or new empty glossary
        """
        ...

    @abstractmethod
    async def delete(self, project_id: ProjectId) -> Result[None, RepositoryError]:
        """
        Delete a glossary.

        Args:
            project_id: The project whose glossary to delete

        Returns:
            Ok[None] if deleted, Err[RepositoryError] on failure
        """
        ...
