"""
SQLite persistence implementation.

Provides SQLAlchemy-based persistence for ContextSafe.
"""

from contextsafe.infrastructure.persistence.sqlite.repositories import (
    SQLiteDocumentRepository,
    SQLiteGlossaryRepository,
    SQLiteProjectRepository,
)
from contextsafe.infrastructure.persistence.sqlite.unit_of_work import (
    SQLiteUnitOfWork,
)


__all__ = [
    "SQLiteDocumentRepository",
    "SQLiteGlossaryRepository",
    "SQLiteProjectRepository",
    "SQLiteUnitOfWork",
]
