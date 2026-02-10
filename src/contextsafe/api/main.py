# ContextSafe - FastAPI Application
# ============================================
"""
Main FastAPI application entry point.

This module re-exports the application from server.py to maintain
a single source of truth for service configuration.

Traceability:
- Contract: CNT-T4-API-001
- Canonical entry point: contextsafe.server
"""
from __future__ import annotations

# Re-export the app from server.py (single source of truth)
from contextsafe.server import app, create_app

__all__ = ["app", "create_app"]


if __name__ == "__main__":
    import uvicorn

    from contextsafe.api.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "contextsafe.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
