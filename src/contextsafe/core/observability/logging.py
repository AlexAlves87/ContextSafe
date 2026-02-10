# ContextSafe - Structured Logging Configuration
# ============================================
"""
Structured logging configuration using structlog.

Features:
- JSON output in production
- Colored console output in development
- Automatic context injection (request_id, use_case_id, business_rule_id)
- ISO 8601 timestamps
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from contextsafe.core.observability.traceability import (
    CTX_BUSINESS_RULE_ID,
    CTX_REQUEST_ID,
    CTX_USE_CASE_ID,
)


def add_context_vars(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add context variables to log events."""
    request_id = CTX_REQUEST_ID.get(None)
    if request_id:
        event_dict["request_id"] = request_id

    use_case_id = CTX_USE_CASE_ID.get(None)
    if use_case_id:
        event_dict["use_case_id"] = use_case_id

    business_rule_id = CTX_BUSINESS_RULE_ID.get(None)
    if business_rule_id:
        event_dict["business_rule_id"] = business_rule_id

    return event_dict


def configure_logging(
    *,
    level: str = "INFO",
    json_output: bool = False,
    log_file: str | None = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output JSON format (for production)
        log_file: Optional file path for logging
    """
    # Common processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_context_vars,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        # Production: JSON format
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Colored console output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
