"""
Database connection manager.

Provides async SQLAlchemy engine and session factory for SQLite.

Traceability:
- Contract: CNT-T3-DATABASE-001
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """
    Database connection manager for SQLite with async support.

    Manages:
    - Engine lifecycle
    - Session factory
    - Connection pool (for SQLite, limited to 5 connections)
    """

    def __init__(self, database_url: str) -> None:
        """
        Initialize database connection.

        Args:
            database_url: SQLite connection URL (sqlite+aiosqlite:///path/to/db.sqlite)

        Raises:
            ValueError: If database_url is empty
        """
        if not database_url:
            raise ValueError("database_url cannot be empty")

        self._engine: AsyncEngine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get the SQLAlchemy async engine."""
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Get a database session as async context manager.

        Automatically commits on success, rolls back on exception.

        Yields:
            AsyncSession: The database session
        """
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_all(self) -> None:
        """
        Create all tables defined in the metadata.

        Should be called once at application startup.
        """
        from contextsafe.infrastructure.persistence.models import Base

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self) -> None:
        """
        Drop all tables. USE WITH CAUTION - for testing only.
        """
        from contextsafe.infrastructure.persistence.models import Base

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """
        Close the database connection.

        Should be called during application shutdown.
        """
        await self._engine.dispose()

    async def health_check(self) -> bool:
        """
        Check if database is accessible.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with self.session() as session:
                await session.execute(
                    session.get_bind().dialect.do_ping  # type: ignore
                )
            return True
        except Exception:
            return False
