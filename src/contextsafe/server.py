"""
FastAPI server setup.

Creates and configures the FastAPI application.

Traceability:
- Contract: CNT-T5-SERVER-001
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, WebSocket

from contextsafe.api.config import Settings, get_settings
from contextsafe.api.dependencies import get_container
from contextsafe.api.middleware import (
    ErrorHandlerMiddleware,
    configure_cors,
    register_exception_handlers,
)
from contextsafe.api.routes import (
    documents_router,
    export_router,
    glossary_router,
    health_router,
    projects_router,
    system_router,
)
from contextsafe.api.websocket import handle_progress_websocket


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    container = get_container()

    # Initialize database
    from contextsafe.infrastructure.persistence import Database

    database = Database(settings.database_url)
    await database.create_all()
    container.set_database(database)

    # NER service is lazy-initialized by the container on first access
    # (see Container._create_ner_service for configuration)

    # Initialize event publisher
    from contextsafe.infrastructure.events import InMemoryEventPublisher

    publisher = InMemoryEventPublisher()
    container.set_event_publisher(publisher)

    # Initialize text extractor
    from contextsafe.infrastructure.document_processing import (
        CompositeDocumentExtractor,
    )

    extractor = CompositeDocumentExtractor.create_default()
    container.set_text_extractor(extractor)

    yield

    # Shutdown
    await database.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        settings: Optional settings override (for testing)

    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="ContextSafe",
        description="Document anonymization API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # Configure CORS
    configure_cors(app, allow_origins=settings.cors_origins)

    # Add error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)

    # Register exception handlers
    register_exception_handlers(app)

    # Register routes
    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(projects_router)
    app.include_router(glossary_router)
    app.include_router(export_router)
    app.include_router(system_router)

    # Register WebSocket endpoint (matches frontend: /ws/documents/{id}/progress)
    @app.websocket("/ws/documents/{document_id}/progress")
    async def progress_websocket(websocket: WebSocket, document_id: UUID) -> None:
        print(f"[WS] WebSocket connection attempt for document {document_id}")
        await handle_progress_websocket(websocket, document_id)
        print(f"[WS] WebSocket disconnected for document {document_id}")

    return app


# Application instance for uvicorn
app = create_app()
