"""
API schemas (DTOs) for ContextSafe.

Pydantic models for request/response validation and serialization.
"""

from contextsafe.api.schemas.anonymization_schema import (
    AnonymizationRequest,
    AnonymizationResponse,
    GlossaryEntryResponse,
    GlossaryResponse,
)
from contextsafe.api.schemas.detection_schema import (
    DetectionRequest,
    DetectionResponse,
    PiiEntityResponse,
)
from contextsafe.api.schemas.document_schema import (
    DocumentListResponse,
    DocumentRequest,
    DocumentResponse,
)
from contextsafe.api.schemas.error_schema import (
    ErrorResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from contextsafe.api.schemas.project_schema import (
    ProjectListResponse,
    ProjectRequest,
    ProjectResponse,
)


__all__ = [
    # Document
    "DocumentRequest",
    "DocumentResponse",
    "DocumentListResponse",
    # Project
    "ProjectRequest",
    "ProjectResponse",
    "ProjectListResponse",
    # Detection
    "DetectionRequest",
    "DetectionResponse",
    "PiiEntityResponse",
    # Anonymization
    "AnonymizationRequest",
    "AnonymizationResponse",
    "GlossaryEntryResponse",
    "GlossaryResponse",
    # Error
    "ErrorResponse",
    "ValidationErrorResponse",
    "ValidationErrorDetail",
]
