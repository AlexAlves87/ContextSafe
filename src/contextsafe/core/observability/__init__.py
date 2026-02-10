# ContextSafe - Observability Module
# ============================================
"""
Observability configuration for ContextSafe.

This module provides:
- Structured logging with structlog
- Traceability Injection Middleware (TIM) decorators
- Context variable propagation for UC-ID and BR-ID

Usage:
    from contextsafe.core.observability import (
        configure_logging,
        trace_use_case,
        trace_business_rule,
        get_logger,
    )
"""

from contextsafe.core.observability.logging import configure_logging, get_logger
from contextsafe.core.observability.traceability import (
    CTX_BUSINESS_RULE_ID,
    CTX_REQUEST_ID,
    CTX_USE_CASE_ID,
    trace_business_rule,
    trace_use_case,
)


__all__ = [
    "configure_logging",
    "get_logger",
    "trace_use_case",
    "trace_business_rule",
    "CTX_REQUEST_ID",
    "CTX_USE_CASE_ID",
    "CTX_BUSINESS_RULE_ID",
]
