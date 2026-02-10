# ContextSafe - Traceability Injection Middleware (TIM)
# ============================================
"""
Traceability Injection Middleware (TIM) for ContextSafe.

Provides decorators to propagate UC-ID and BR-ID through the execution context.
This enables complete traceability from use case to business rule in logs and metrics.

Usage:
    @trace_use_case("UC-001")
    async def ingest_document(self, command: IngestDocumentCommand) -> Result:
        ...

    @trace_business_rule("BR-002")
    def validate_alias_consistency(self, alias: Alias) -> bool:
        ...
"""

from __future__ import annotations

import functools
from contextvars import ContextVar
from typing import Any, Callable, ParamSpec, TypeVar
from uuid import uuid4

import structlog


# Context variables for traceability
CTX_REQUEST_ID: ContextVar[str | None] = ContextVar("ctx_request_id", default=None)
CTX_USE_CASE_ID: ContextVar[str | None] = ContextVar("ctx_use_case_id", default=None)
CTX_BUSINESS_RULE_ID: ContextVar[str | None] = ContextVar("ctx_business_rule_id", default=None)

# Type variables for decorator
P = ParamSpec("P")
T = TypeVar("T")

logger = structlog.get_logger(__name__)


def set_request_id(request_id: str | None = None) -> str:
    """
    Set the request ID in the context.

    Args:
        request_id: Optional request ID. If None, generates a new UUID.

    Returns:
        The request ID that was set.
    """
    rid = request_id or str(uuid4())
    CTX_REQUEST_ID.set(rid)
    return rid


def trace_use_case(use_case_id: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to inject use case ID into the logging context.

    Args:
        use_case_id: The use case identifier (e.g., "UC-001")

    Returns:
        Decorated function with use case tracing

    Example:
        @trace_use_case("UC-001")
        async def execute(self, command: Command) -> Result:
            # All logs within this function will include use_case_id="UC-001"
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            token = CTX_USE_CASE_ID.set(use_case_id)
            try:
                logger.debug("use_case_started", use_case_id=use_case_id)
                result = await func(*args, **kwargs)
                logger.debug("use_case_completed", use_case_id=use_case_id)
                return result
            except Exception as e:
                logger.error(
                    "use_case_failed",
                    use_case_id=use_case_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise
            finally:
                CTX_USE_CASE_ID.reset(token)

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            token = CTX_USE_CASE_ID.set(use_case_id)
            try:
                logger.debug("use_case_started", use_case_id=use_case_id)
                result = func(*args, **kwargs)
                logger.debug("use_case_completed", use_case_id=use_case_id)
                return result
            except Exception as e:
                logger.error(
                    "use_case_failed",
                    use_case_id=use_case_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise
            finally:
                CTX_USE_CASE_ID.reset(token)

        # Check if function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper

    return decorator


def trace_business_rule(rule_id: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to inject business rule ID into the logging context.

    Args:
        rule_id: The business rule identifier (e.g., "BR-002")

    Returns:
        Decorated function with business rule tracing

    Example:
        @trace_business_rule("BR-002")
        def validate_alias_consistency(self, alias: Alias) -> bool:
            # All logs within this function will include business_rule_id="BR-002"
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            token = CTX_BUSINESS_RULE_ID.set(rule_id)
            try:
                logger.debug("business_rule_check_started", business_rule_id=rule_id)
                result = func(*args, **kwargs)
                logger.debug(
                    "business_rule_check_completed",
                    business_rule_id=rule_id,
                    result=bool(result),
                )
                return result
            except Exception as e:
                logger.error(
                    "business_rule_check_failed",
                    business_rule_id=rule_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise
            finally:
                CTX_BUSINESS_RULE_ID.reset(token)

        return wrapper

    return decorator


class TracingContext:
    """
    Context manager for setting tracing context variables.

    Usage:
        async with TracingContext(
            request_id="req-123",
            use_case_id="UC-001",
            business_rule_id="BR-002"
        ):
            # All logs within this block will include the context
            ...
    """

    def __init__(
        self,
        request_id: str | None = None,
        use_case_id: str | None = None,
        business_rule_id: str | None = None,
    ) -> None:
        self.request_id = request_id
        self.use_case_id = use_case_id
        self.business_rule_id = business_rule_id
        self._tokens: list[Any] = []

    def __enter__(self) -> "TracingContext":
        if self.request_id:
            self._tokens.append(("request", CTX_REQUEST_ID.set(self.request_id)))
        if self.use_case_id:
            self._tokens.append(("use_case", CTX_USE_CASE_ID.set(self.use_case_id)))
        if self.business_rule_id:
            self._tokens.append(("rule", CTX_BUSINESS_RULE_ID.set(self.business_rule_id)))
        return self

    def __exit__(self, *args: Any) -> None:
        for name, token in reversed(self._tokens):
            if name == "request":
                CTX_REQUEST_ID.reset(token)
            elif name == "use_case":
                CTX_USE_CASE_ID.reset(token)
            elif name == "rule":
                CTX_BUSINESS_RULE_ID.reset(token)

    async def __aenter__(self) -> "TracingContext":
        return self.__enter__()

    async def __aexit__(self, *args: Any) -> None:
        self.__exit__(*args)
