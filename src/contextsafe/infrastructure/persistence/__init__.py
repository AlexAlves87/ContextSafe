"""
Persistence infrastructure for ContextSafe.

Provides database connection management and repository implementations.
"""

from contextsafe.infrastructure.persistence.database import Database
from contextsafe.infrastructure.persistence.sqlite import (
    SQLiteDocumentRepository,
    SQLiteGlossaryRepository,
    SQLiteProjectRepository,
    SQLiteUnitOfWork,
)


__all__ = [
    "Database",
    "SQLiteDocumentRepository",
    "SQLiteGlossaryRepository",
    "SQLiteProjectRepository",
    "SQLiteUnitOfWork",
]
