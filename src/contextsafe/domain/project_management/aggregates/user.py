"""
User Aggregate - Aggregate root for user management.

Traceability:
- Standard: consolidated_standards.yaml#factories.aggregates.User
- Bounded Context: BC-004 (ProjectManagement)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from uuid import uuid4

from contextsafe.domain.shared.errors import DomainError
from contextsafe.domain.shared.types import AggregateRoot, DomainEvent, Err, Ok, Result
from contextsafe.domain.shared.value_objects import EntityId


class UserRole(str, Enum):
    """User roles."""

    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"


class UserError(DomainError):
    """User-related error."""

    error_code = "ERR-USER-000"
    type_uri = "https://api.contextsafe.io/errors/user"
    title = "User Error"
    status = 422


@dataclass(frozen=True, kw_only=True)
class User(AggregateRoot[EntityId]):
    """
    Aggregate root for a user.

    Manages user identity and authentication state.
    """

    id: EntityId = field(kw_only=False)
    email: str = field(kw_only=False)
    username: str = field(kw_only=False)
    password_hash: str = ""
    role: UserRole = UserRole.USER
    is_active: bool = True
    last_login: Optional[datetime] = None
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    _pending_events: List[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls,
        email: str,
        username: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
    ) -> Result[User, UserError]:
        """
        Create a new User.

        Args:
            email: User email address
            username: Display name
            password_hash: Hashed password
            role: User role

        Returns:
            Ok[User] if valid, Err[UserError] if invalid
        """
        # Validate email
        email = email.strip().lower()
        if not email or "@" not in email:
            return Err(UserError("Invalid email address"))

        # Validate username
        username = username.strip()
        if not username or len(username) > 100:
            return Err(UserError("Username must be 1-100 characters"))

        # Generate user ID
        user_id_result = EntityId.create(str(uuid4()))
        if user_id_result.is_err():
            return Err(UserError("Failed to generate user ID"))

        user_id = user_id_result.unwrap()

        return Ok(
            cls(
                id=user_id,
                email=email,
                username=username,
                password_hash=password_hash,
                role=role,
            )
        )

    def update_email(self, new_email: str) -> Result[None, UserError]:
        """Update user email."""
        new_email = new_email.strip().lower()
        if not new_email or "@" not in new_email:
            return Err(UserError("Invalid email address"))

        object.__setattr__(self, "email", new_email)
        self._touch()
        return Ok(None)

    def update_username(self, new_username: str) -> Result[None, UserError]:
        """Update username."""
        new_username = new_username.strip()
        if not new_username or len(new_username) > 100:
            return Err(UserError("Username must be 1-100 characters"))

        object.__setattr__(self, "username", new_username)
        self._touch()
        return Ok(None)

    def update_password(self, new_password_hash: str) -> None:
        """Update password hash."""
        object.__setattr__(self, "password_hash", new_password_hash)
        self._touch()

    def update_role(self, new_role: UserRole) -> None:
        """Update user role."""
        object.__setattr__(self, "role", new_role)
        self._touch()

    def record_login(self) -> None:
        """Record a login event."""
        object.__setattr__(self, "last_login", datetime.utcnow())
        self._touch()

    def deactivate(self) -> None:
        """Deactivate the user."""
        object.__setattr__(self, "is_active", False)
        self._touch()

    def reactivate(self) -> None:
        """Reactivate the user."""
        object.__setattr__(self, "is_active", True)
        self._touch()

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role.value,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        """Reconstruct from dictionary."""
        user_id = EntityId.create(data["id"]).unwrap()
        role = UserRole(data["role"])

        return cls(
            id=user_id,
            email=data["email"],
            username=data["username"],
            password_hash=data.get("password_hash", ""),
            role=role,
            is_active=data.get("is_active", True),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            settings=data.get("settings", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
        )
