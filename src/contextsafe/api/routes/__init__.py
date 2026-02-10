"""
API routes for ContextSafe.

All routers are exposed here for main application registration.
"""

from contextsafe.api.routes.documents import router as documents_router
from contextsafe.api.routes.export import router as export_router
from contextsafe.api.routes.glossary import router as glossary_router
from contextsafe.api.routes.health import router as health_router
from contextsafe.api.routes.projects import router as projects_router
from contextsafe.api.routes.system import router as system_router


__all__ = [
    "documents_router",
    "export_router",
    "glossary_router",
    "health_router",
    "projects_router",
    "system_router",
]
