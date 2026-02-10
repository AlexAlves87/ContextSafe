"""
ProjectId value object.

Immutable identifier for projects.

Traceability:
- Standard: consolidated_standards.yaml#factories.value_objects.ProjectId
- Bounded Context: BC-004 (ProjectManagement)
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from contextsafe.domain.shared.errors import InvalidIdError
from contextsafe.domain.shared.types import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class ProjectId:
    """
    Unique identifier for a project.

    Value object that encapsulates project ID validation.
    """

    value: str

    @classmethod
    def create(cls, value: str) -> Result[ProjectId, InvalidIdError]:
        """
        Create a validated ProjectId.

        Args:
            value: UUID string

        Returns:
            Ok[ProjectId] if valid, Err[InvalidIdError] if invalid
        """
        if not value or not value.strip():
            return Err(InvalidIdError.create("", "non-empty UUID"))

        try:
            UUID(value)
        except ValueError:
            return Err(InvalidIdError.create(value, "UUID"))

        return Ok(cls(value=value))

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Compare by value."""
        if isinstance(other, ProjectId):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Hash by value."""
        return hash(self.value)
