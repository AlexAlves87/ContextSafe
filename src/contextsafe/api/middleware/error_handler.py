"""
Global error handler middleware.

Converts exceptions to RFC 7807 Problem Details format.

Traceability:
- Contract: CNT-T4-ERROR-HANDLER-001
"""

from __future__ import annotations

import logging
import traceback
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from contextsafe.api.schemas import ErrorResponse, ValidationErrorResponse
from contextsafe.domain.shared.errors import (
    DomainError,
    NotFoundError,
    RepositoryError,
)


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler middleware.

    Catches all unhandled exceptions and converts to ErrorResponse.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle request and catch any exceptions."""
        try:
            return await call_next(request)
        except Exception as e:
            return self._handle_exception(request, e)

    def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Convert exception to appropriate error response."""
        request_id = request.headers.get("X-Request-ID", "unknown")

        if isinstance(exc, NotFoundError):
            return self._create_error_response(
                type_uri="/errors/not-found",
                title="Not Found",
                status=404,
                detail=str(exc),
                instance=str(request.url.path),
            )

        if isinstance(exc, DomainError):
            logger.warning(
                f"[{request_id}] Domain error: {exc}",
                extra={"request_id": request_id},
            )
            return self._create_error_response(
                type_uri="/errors/domain-error",
                title="Domain Error",
                status=422,
                detail=str(exc),
                instance=str(request.url.path),
            )

        if isinstance(exc, RepositoryError):
            logger.error(
                f"[{request_id}] Repository error: {exc}",
                extra={"request_id": request_id},
            )
            return self._create_error_response(
                type_uri="/errors/infrastructure-error",
                title="Service Error",
                status=503,
                detail="A service error occurred. Please try again later.",
                instance=str(request.url.path),
            )

        # Unhandled exception
        logger.critical(
            f"[{request_id}] Unhandled exception: {exc}\n{traceback.format_exc()}",
            extra={"request_id": request_id},
        )
        return self._create_error_response(
            type_uri="/errors/internal-error",
            title="Internal Server Error",
            status=500,
            detail="An unexpected error occurred.",
            instance=str(request.url.path),
        )

    def _create_error_response(
        self,
        type_uri: str,
        title: str,
        status: int,
        detail: str,
        instance: str,
    ) -> JSONResponse:
        """Create RFC 7807 error response."""
        return JSONResponse(
            status_code=status,
            content=ErrorResponse(
                type=type_uri,
                title=title,
                status=status,
                detail=detail,
                instance=instance,
            ).model_dump(),
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = [
            {
                "loc": list(e["loc"]),
                "msg": e["msg"],
                "type": e["type"],
            }
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=ValidationErrorResponse(
                errors=errors,
            ).model_dump(),
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        """Handle not found errors."""
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                type="/errors/not-found",
                title="Not Found",
                status=404,
                detail=str(exc),
                instance=str(request.url.path),
            ).model_dump(),
        )
