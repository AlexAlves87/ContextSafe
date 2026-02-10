"""
Domain errors for ContextSafe.

All errors follow RFC 7807 Problem Details format.
"""
from contextsafe.domain.shared.errors.domain_error import (
    AliasLeaksPiiError,
    AuditError,
    BatchError,
    DetectionError,
    DocumentError,
    DocumentSizeError,
    DomainError,
    DuplicateAliasError,
    GlossaryError,
    InconsistentMappingError,
    InvalidAliasError,
    InvalidCategoryError,
    InvalidExtensionError,
    InvalidIdError,
    InvalidLevelError,
    InvalidScoreError,
    InvalidSpanError,
    InvalidStateError,
    InvariantViolationError,
    LowConfidenceError,
    NotFoundError,
    ProblemDetails,
    RepositoryError,
    StateTransitionError,
    ValidationError,
)

__all__ = [
    # Base
    "DomainError",
    "ProblemDetails",
    "ValidationError",
    "InvariantViolationError",
    # Validation errors
    "InvalidIdError",
    "InvalidAliasError",
    "InvalidCategoryError",
    "InvalidLevelError",
    "InvalidStateError",
    "InvalidScoreError",
    "InvalidSpanError",
    # Document errors
    "DocumentError",
    "DocumentSizeError",
    "InvalidExtensionError",
    "StateTransitionError",
    # Glossary errors
    "GlossaryError",
    "DuplicateAliasError",
    "InconsistentMappingError",
    "AliasLeaksPiiError",
    # Detection errors
    "DetectionError",
    "LowConfidenceError",
    # Infrastructure errors
    "RepositoryError",
    "NotFoundError",
    "AuditError",
    "BatchError",
]
