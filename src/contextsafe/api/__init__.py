# ContextSafe - API Layer
# ============================================
"""
API layer containing FastAPI routes and schemas.

Modules:
- routes: HTTP endpoints for all use cases
- schemas: Request/response Pydantic models
- middleware: CORS, error handling, logging
- dependencies: FastAPI dependency injection
- websocket: Real-time progress updates
"""

from contextsafe.api.config import Settings, get_settings


__all__ = [
    "Settings",
    "get_settings",
]
