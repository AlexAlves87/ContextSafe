"""
CORS middleware configuration.

Traceability:
- Contract: CNT-T4-CORS-001
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def configure_cors(
    app: FastAPI,
    allow_origins: list[str] | None = None,
    allow_credentials: bool = True,
    allow_methods: list[str] | None = None,
    allow_headers: list[str] | None = None,
    max_age: int = 600,
) -> None:
    """
    Configure CORS middleware for the FastAPI app.

    Args:
        app: FastAPI application instance
        allow_origins: List of allowed origins
        allow_credentials: Allow credentials (cookies, auth headers)
        allow_methods: Allowed HTTP methods
        allow_headers: Allowed headers
        max_age: Max age for preflight cache (seconds)
    """
    if allow_origins is None:
        allow_origins = [
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative port
        ]

    if allow_methods is None:
        allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

    if allow_headers is None:
        allow_headers = [
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "Accept",
            "Origin",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        max_age=max_age,
    )


def get_cors_origins_from_env() -> list[str]:
    """
    Get CORS origins from environment variable.

    Reads CONTEXTSAFE_CORS_ORIGINS as comma-separated list.

    Returns:
        List of allowed origins
    """
    import os

    origins_str = os.environ.get(
        "CONTEXTSAFE_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )
    return [o.strip() for o in origins_str.split(",") if o.strip()]
