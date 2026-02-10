"""
Domain Error base class with RFC 7807 support.

All domain errors inherit from DomainError and provide:
- error_code: Unique identifier for the error type
- to_problem_details(): Convert to RFC 7807 format

Traceability:
- Standard: RFC 7807 (Problem Details for HTTP APIs)
- Source: outputs/phase3/step1_contracts/error_catalog.yaml
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ProblemDetails:
    """
    RFC 7807 Problem Details structure.

    Standard format for HTTP API error responses.
    """

    type: str
    title: str
    status: int
    detail: str
    instance: str = ""
    error_code: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    recoverable: bool = False
    extensions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to RFC 7807 JSON representation."""
        result: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "error_code": self.error_code,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
        }
        if self.instance:
            result["instance"] = self.instance
        if self.recoverable:
            result["recoverable"] = self.recoverable
        if self.extensions:
            result.update(self.extensions)
        return result


class DomainError(Exception):
    """
    Base class for all domain errors.

    Domain errors are:
    - Expected errors that can occur during business operations
    - Converted to Result[T, DomainError] instead of raised
    - Provide RFC 7807 ProblemDetails for API responses
    """

    error_code: str = "ERR-UNKNOWN"
    type_uri: str = "https://api.contextsafe.io/errors/unknown"
    title: str = "Unknown Error"
    status: int = 500
    recoverable: bool = False

    def __init__(self, detail: str, **extensions: Any) -> None:
        """
        Initialize domain error.

        Args:
            detail: Human-readable description of the specific error
            **extensions: Additional context-specific data
        """
        self.detail = detail
        self.extensions = extensions
        self.trace_id = str(uuid4())
        super().__init__(detail)

    def to_problem_details(self, instance: str = "") -> ProblemDetails:
        """Convert to RFC 7807 ProblemDetails."""
        return ProblemDetails(
            type=self.type_uri,
            title=self.title,
            status=self.status,
            detail=self.detail,
            instance=instance,
            error_code=self.error_code,
            trace_id=self.trace_id,
            recoverable=self.recoverable,
            extensions=self.extensions,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 0: DOMAIN ERRORS (Validation, Invariant Violations)
# ═══════════════════════════════════════════════════════════════════════════════


class ValidationError(DomainError):
    """Base class for validation errors."""

    error_code = "ERR-T0-VAL-000"
    type_uri = "https://api.contextsafe.io/errors/validation"
    title = "Validation Error"
    status = 422
    recoverable = True


class InvalidIdError(ValidationError):
    """Invalid ID format error."""

    error_code = "ERR-T0-VAL-001"
    type_uri = "https://api.contextsafe.io/errors/validation/invalid-id"
    title = "Invalid ID Format"

    @classmethod
    def create(cls, value: str, expected_format: str = "UUID") -> InvalidIdError:
        """Create error with context."""
        return cls(
            detail=f"Invalid ID format: '{value}'. Expected {expected_format}.",
            value=value,
            expected_format=expected_format,
        )


class InvalidAliasError(ValidationError):
    """Invalid alias format or content error."""

    error_code = "ERR-T0-VAL-002"
    type_uri = "https://api.contextsafe.io/errors/validation/invalid-alias"
    title = "Invalid Alias"

    @classmethod
    def create(cls, value: str, reason: str) -> InvalidAliasError:
        """Create error with context."""
        return cls(
            detail=f"Invalid alias '{value}': {reason}",
            value=value,
            reason=reason,
        )


class InvalidCategoryError(ValidationError):
    """Invalid PII category error."""

    error_code = "ERR-T0-VAL-003"
    type_uri = "https://api.contextsafe.io/errors/validation/invalid-category"
    title = "Invalid PII Category"

    @classmethod
    def create(cls, value: str) -> InvalidCategoryError:
        """Create error with context."""
        return cls(
            detail=f"Unknown PII category: '{value}'",
            value=value,
        )


class InvalidLevelError(ValidationError):
    """Invalid anonymization level error."""

    error_code = "ERR-T0-VAL-004"
    type_uri = "https://api.contextsafe.io/errors/validation/invalid-level"
    title = "Invalid Anonymization Level"

    @classmethod
    def create(cls, value: str) -> InvalidLevelError:
        """Create error with context."""
        return cls(
            detail=f"Unknown anonymization level: '{value}'. Valid: BASIC, INTERMEDIATE, ADVANCED",
            value=value,
        )


class InvalidStateError(ValidationError):
    """Invalid document state error."""

    error_code = "ERR-T0-VAL-005"
    type_uri = "https://api.contextsafe.io/errors/validation/invalid-state"
    title = "Invalid Document State"

    @classmethod
    def create(cls, value: str) -> InvalidStateError:
        """Create error with context."""
        return cls(
            detail=f"Unknown document state: '{value}'",
            value=value,
        )


class InvalidScoreError(ValidationError):
    """Invalid confidence score error."""

    error_code = "ERR-T0-VAL-006"
    type_uri = "https://api.contextsafe.io/errors/validation/invalid-score"
    title = "Invalid Confidence Score"

    @classmethod
    def create(cls, value: float) -> InvalidScoreError:
        """Create error with context."""
        return cls(
            detail=f"Confidence score must be in [0.0, 1.0], got: {value}",
            value=value,
        )


class InvalidSpanError(ValidationError):
    """Invalid text span error."""

    error_code = "ERR-T0-VAL-007"
    type_uri = "https://api.contextsafe.io/errors/validation/invalid-span"
    title = "Invalid Text Span"

    @classmethod
    def create(cls, start: int, end: int, reason: str) -> InvalidSpanError:
        """Create error with context."""
        return cls(
            detail=f"Invalid span [{start}, {end}]: {reason}",
            start=start,
            end=end,
            reason=reason,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 0: INVARIANT VIOLATIONS
# ═══════════════════════════════════════════════════════════════════════════════


class InvariantViolationError(DomainError):
    """Invariant violation error."""

    error_code = "ERR-T0-INV-000"
    type_uri = "https://api.contextsafe.io/errors/invariant"
    title = "Invariant Violation"
    status = 422
    recoverable = False


class DocumentError(DomainError):
    """Document-related domain error."""

    error_code = "ERR-T0-DOC-000"
    type_uri = "https://api.contextsafe.io/errors/document"
    title = "Document Error"
    status = 422
    recoverable = True


class DocumentSizeError(DocumentError):
    """Document exceeds size limit."""

    error_code = "ERR-T0-DOC-001"
    type_uri = "https://api.contextsafe.io/errors/document/size"
    title = "Document Too Large"

    @classmethod
    def create(cls, size_bytes: int, max_bytes: int) -> DocumentSizeError:
        """Create error with context."""
        size_mb = size_bytes / (1024 * 1024)
        max_mb = max_bytes / (1024 * 1024)
        return cls(
            detail=f"Document size {size_mb:.2f}MB exceeds maximum {max_mb:.2f}MB",
            size_bytes=size_bytes,
            max_bytes=max_bytes,
        )


class InvalidExtensionError(DocumentError):
    """Invalid file extension."""

    error_code = "ERR-T0-DOC-002"
    type_uri = "https://api.contextsafe.io/errors/document/extension"
    title = "Invalid File Extension"

    @classmethod
    def create(cls, extension: str, valid_extensions: list[str]) -> InvalidExtensionError:
        """Create error with context."""
        return cls(
            detail=f"Invalid extension '{extension}'. Valid: {', '.join(valid_extensions)}",
            extension=extension,
            valid_extensions=valid_extensions,
        )


class StateTransitionError(DocumentError):
    """Invalid state transition."""

    error_code = "ERR-T0-DOC-003"
    type_uri = "https://api.contextsafe.io/errors/document/state-transition"
    title = "Invalid State Transition"

    @classmethod
    def create(cls, from_state: str, to_state: str) -> StateTransitionError:
        """Create error with context."""
        return cls(
            detail=f"Cannot transition from {from_state} to {to_state}",
            from_state=from_state,
            to_state=to_state,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 0: GLOSSARY ERRORS
# ═══════════════════════════════════════════════════════════════════════════════


class GlossaryError(DomainError):
    """Glossary-related domain error."""

    error_code = "ERR-T0-GLO-000"
    type_uri = "https://api.contextsafe.io/errors/glossary"
    title = "Glossary Error"
    status = 422
    recoverable = True


class DuplicateAliasError(GlossaryError):
    """Alias already exists in project."""

    error_code = "ERR-T0-GLO-001"
    type_uri = "https://api.contextsafe.io/errors/glossary/duplicate-alias"
    title = "Duplicate Alias"
    recoverable = False

    @classmethod
    def create(cls, alias: str, project_id: str) -> DuplicateAliasError:
        """Create error with context."""
        return cls(
            detail=f"Alias '{alias}' already exists in project {project_id}",
            alias=alias,
            project_id=project_id,
        )


class InconsistentMappingError(GlossaryError):
    """Same entity mapped to different aliases (BR-002 violation)."""

    error_code = "ERR-T0-GLO-002"
    type_uri = "https://api.contextsafe.io/errors/glossary/inconsistent-mapping"
    title = "Inconsistent Alias Mapping"
    recoverable = False

    @classmethod
    def create(
        cls, normalized_value: str, existing_alias: str, new_alias: str
    ) -> InconsistentMappingError:
        """Create error with context."""
        return cls(
            detail=f"Entity '{normalized_value}' already mapped to '{existing_alias}', "
            f"cannot remap to '{new_alias}'",
            normalized_value=normalized_value,
            existing_alias=existing_alias,
            new_alias=new_alias,
        )


class AliasLeaksPiiError(GlossaryError):
    """Alias contains or reveals PII."""

    error_code = "ERR-T0-GLO-003"
    type_uri = "https://api.contextsafe.io/errors/glossary/alias-leaks-pii"
    title = "Alias Leaks PII"
    recoverable = True

    @classmethod
    def create(cls, alias: str, leaked_data: str) -> AliasLeaksPiiError:
        """Create error with context."""
        return cls(
            detail=f"Alias '{alias}' appears to contain PII: '{leaked_data}'",
            alias=alias,
            leaked_data=leaked_data,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 1: DETECTION ERRORS
# ═══════════════════════════════════════════════════════════════════════════════


class DetectionError(DomainError):
    """Detection-related error."""

    error_code = "ERR-T1-DET-000"
    type_uri = "https://api.contextsafe.io/errors/detection"
    title = "Detection Error"
    status = 500
    recoverable = True


class LowConfidenceError(DetectionError):
    """Detection confidence below threshold."""

    error_code = "ERR-T1-DET-001"
    type_uri = "https://api.contextsafe.io/errors/detection/low-confidence"
    title = "Low Confidence Detection"
    status = 422
    recoverable = True

    @classmethod
    def create(cls, confidence: float, threshold: float) -> LowConfidenceError:
        """Create error with context."""
        return cls(
            detail=f"Detection confidence {confidence:.2f} below threshold {threshold:.2f}",
            confidence=confidence,
            threshold=threshold,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 2: INFRASTRUCTURE ERRORS
# ═══════════════════════════════════════════════════════════════════════════════


class RepositoryError(DomainError):
    """Repository/persistence error."""

    error_code = "ERR-T2-REP-000"
    type_uri = "https://api.contextsafe.io/errors/repository"
    title = "Repository Error"
    status = 500
    recoverable = True


class NotFoundError(RepositoryError):
    """Entity not found in repository."""

    error_code = "ERR-T2-REP-001"
    type_uri = "https://api.contextsafe.io/errors/repository/not-found"
    title = "Not Found"
    status = 404
    recoverable = False

    @classmethod
    def create(cls, entity_type: str, entity_id: str) -> NotFoundError:
        """Create error with context."""
        return cls(
            detail=f"{entity_type} with ID '{entity_id}' not found",
            entity_type=entity_type,
            entity_id=entity_id,
        )


class AuditError(DomainError):
    """Audit logging error."""

    error_code = "ERR-T2-AUD-000"
    type_uri = "https://api.contextsafe.io/errors/audit"
    title = "Audit Error"
    status = 500
    recoverable = True


class BatchError(DomainError):
    """Batch processing error."""

    error_code = "ERR-T2-BAT-000"
    type_uri = "https://api.contextsafe.io/errors/batch"
    title = "Batch Error"
    status = 500
    recoverable = True
