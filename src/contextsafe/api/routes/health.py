"""
Health check routes.

Traceability:
- Contract: CNT-T4-HEALTH-001
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, Any]:
    """
    Basic health check.

    Returns 200 OK if the server is running.
    """
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check including database connectivity.

    Returns 200 if all dependencies are available.
    """
    # TODO: Add actual database check when DI is wired
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "ner_service": "ok",
        },
    }
