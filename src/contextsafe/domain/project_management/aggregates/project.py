"""
Project Aggregate - Aggregate root for project management.

Traceability:
- Standard: consolidated_standards.yaml#factories.aggregates.Project
- Invariants: INV-013, INV-015
- Bounded Context: BC-004 (ProjectManagement)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional
from uuid import uuid4

from contextsafe.domain.shared.errors import DomainError, ValidationError
from contextsafe.domain.shared.types import AggregateRoot, DomainEvent, Err, Ok, Result
from contextsafe.domain.shared.value_objects import ProjectId


class ProjectError(DomainError):
    """Project-related error."""

    error_code = "ERR-PROJ-000"
    type_uri = "https://api.contextsafe.io/errors/project"
    title = "Project Error"
    status = 422


@dataclass(frozen=True, kw_only=True)
class Project(AggregateRoot[ProjectId]):
    """
    Aggregate root for a project.

    A project contains:
    - Documents to be anonymized
    - A glossary of alias mappings
    - Settings for anonymization
    - Audit trail
    """

    id: ProjectId = field(kw_only=False)
    name: str = field(kw_only=False)
    description: str = ""
    owner_id: str = ""
    document_count: int = 0
    is_active: bool = True
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    _pending_events: List[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls,
        name: str,
        owner_id: str,
        description: str = "",
        settings: Optional[dict[str, Any]] = None,
    ) -> Result[Project, ProjectError]:
        """
        Create a new Project.

        Args:
            name: Project name (1-200 chars)
            owner_id: ID of the project owner
            description: Optional description

        Returns:
            Ok[Project] if valid, Err[ProjectError] if invalid
        """
        # Validate name (INV-013)
        name = name.strip()
        if not name or len(name) > 200:
            return Err(
                ProjectError("Project name must be 1-200 characters")
            )

        # Validate owner (INV-015)
        if not owner_id:
            return Err(ProjectError("Project must have an owner"))

        # Generate project ID
        project_id_result = ProjectId.create(str(uuid4()))
        if project_id_result.is_err():
            return Err(ProjectError("Failed to generate project ID"))

        project_id = project_id_result.unwrap()

        return Ok(
            cls(
                id=project_id,
                name=name,
                description=description,
                owner_id=owner_id,
                settings=settings or {},
            )
        )

    def rename(self, new_name: str) -> Result[None, ProjectError]:
        """
        Rename the project.

        Args:
            new_name: New project name
        """
        new_name = new_name.strip()
        if not new_name or len(new_name) > 200:
            return Err(
                ProjectError("Project name must be 1-200 characters")
            )

        object.__setattr__(self, "name", new_name)
        self._touch()
        return Ok(None)

    def update_description(self, description: str) -> None:
        """Update the project description."""
        object.__setattr__(self, "description", description)
        self._touch()

    def update_settings(self, settings: dict[str, Any]) -> None:
        """Update project settings."""
        current = dict(self.settings)
        current.update(settings)
        object.__setattr__(self, "settings", current)
        self._touch()

    def increment_document_count(self) -> None:
        """Increment the document counter."""
        object.__setattr__(self, "document_count", self.document_count + 1)
        self._touch()

    def decrement_document_count(self) -> None:
        """Decrement the document counter."""
        if self.document_count > 0:
            object.__setattr__(self, "document_count", self.document_count - 1)
            self._touch()

    def deactivate(self) -> None:
        """Deactivate the project (soft delete)."""
        object.__setattr__(self, "is_active", False)
        self._touch()

    def reactivate(self) -> None:
        """Reactivate the project."""
        object.__setattr__(self, "is_active", True)
        self._touch()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "document_count": self.document_count,
            "is_active": self.is_active,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        """Reconstruct from dictionary."""
        project_id = ProjectId.create(data["id"]).unwrap()

        return cls(
            id=project_id,
            name=data["name"],
            description=data.get("description", ""),
            owner_id=data["owner_id"],
            document_count=data.get("document_count", 0),
            is_active=data.get("is_active", True),
            settings=data.get("settings", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
        )
