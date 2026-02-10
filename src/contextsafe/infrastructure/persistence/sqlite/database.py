"""
SQLite database configuration and session management.

Traceability:
- Contract: CNT-T3-PERSISTENCE-001
- IMPLEMENTATION_PLAN.md Phase 3.1
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from contextsafe.infrastructure.persistence.sqlite.models import Base


class DatabaseConfig:
    """Database configuration."""

    def __init__(
        self,
        database_url: str | None = None,
        echo: bool = False,
    ):
        """
        Initialize database configuration.

        Args:
            database_url: SQLite connection URL (async driver)
            echo: Whether to log SQL statements
        """
        if database_url is None:
            # Default to local file in data directory
            data_dir = Path(os.getcwd()) / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "contextsafe.db"
            database_url = f"sqlite+aiosqlite:///{db_path}"

        self.database_url = database_url
        self.echo = echo


class Database:
    """
    Async database manager for SQLite.

    Manages engine, session factory, and table creation.
    """

    def __init__(self, config: DatabaseConfig | None = None):
        """
        Initialize database with configuration.

        Args:
            config: Database configuration. Uses defaults if None.
        """
        self._config = config or DatabaseConfig()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._session_factory

    async def init(self) -> None:
        """
        Initialize the database engine and session factory.

        Creates the engine, session factory, and all tables.
        """
        self._engine = create_async_engine(
            self._config.database_url,
            echo=self._config.echo,
            # SQLite-specific settings
            connect_args={"check_same_thread": False},
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Create all tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Close the database engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def create_session(self) -> AsyncSession:
        """Create a new database session."""
        return self.session_factory()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for database sessions.

        Yields:
            AsyncSession: Database session

        Example:
            async with db.session() as session:
                result = await session.execute(query)
        """
        session = self.create_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Global database instance
_db: Database | None = None


async def init_database(
    database_url: str | None = None,
    echo: bool = False,
) -> Database:
    """
    Initialize the global database instance.

    Args:
        database_url: SQLite connection URL
        echo: Whether to log SQL statements

    Returns:
        Initialized Database instance
    """
    global _db
    config = DatabaseConfig(database_url=database_url, echo=echo)
    _db = Database(config)
    await _db.init()
    return _db


async def close_database() -> None:
    """Close the global database instance."""
    global _db
    if _db:
        await _db.close()
        _db = None


def get_database() -> Database:
    """
    Get the global database instance.

    Raises:
        RuntimeError: If database not initialized
    """
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get the session factory for dependency injection.

    Returns:
        Session factory function
    """
    return get_database().session_factory
