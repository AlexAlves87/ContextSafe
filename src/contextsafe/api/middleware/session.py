"""
Session helpers para ContextSafe (uso local).

Provee funciones helper para obtener la sesión local desde request.state.
"""

from fastapi import Request

from ..session_manager import session_manager


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_current_session(request: Request):
    """
    Obtiene la sesión del request.state.

    Uso en routes:
        @router.get("/something")
        async def something(request: Request):
            session = get_current_session(request)
            # usar session...
    """
    session = getattr(request.state, "session", None)
    if not session:
        # Crear sesión local automáticamente
        session = session_manager.get_or_create_local_session()
        request.state.session = session
        request.state.session_id = session.id
    return session


def get_session_id(request: Request) -> str:
    """Obtiene el session_id del request.state."""
    session_id = getattr(request.state, "session_id", None)
    if not session_id:
        # Crear sesión local automáticamente
        session = session_manager.get_or_create_local_session()
        request.state.session = session
        request.state.session_id = session.id
        session_id = session.id
    return session_id
