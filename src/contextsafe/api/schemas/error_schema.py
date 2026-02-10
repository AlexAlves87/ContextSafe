"""
Error response schemas (RFC 7807 Problem Details).

Traceability:
- Contract: CNT-T4-ERROR-SCHEMA-001
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    RFC 7807 Problem Details error response.

    Standard format for HTTP API errors.
    """

    type: str = Field(
        ...,
        description="URI reference identifying problem type",
        examples=["/errors/document-not-found"],
    )
    title: str = Field(
        ...,
        description="Short, human-readable summary",
        examples=["Document Not Found"],
    )
    status: int = Field(
        ...,
        description="HTTP status code",
        examples=[404],
    )
    detail: str = Field(
        ...,
        description="Human-readable explanation",
        examples=["The document with ID '123' was not found."],
    )
    instance: str | None = Field(
        None,
        description="URI reference to specific occurrence",
        examples=["/api/v1/documents/123"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "/errors/document-not-found",
                    "title": "Document Not Found",
                    "status": 404,
                    "detail": "The document with ID '123' was not found.",
                    "instance": "/api/v1/documents/123",
                }
            ]
        }
    }


class ValidationErrorDetail(BaseModel):
    """Detail for a single validation error."""

    loc: list[str] = Field(..., description="Location of the error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseModel):
    """Response for validation errors (400 Bad Request)."""

    type: str = Field(
        "/errors/validation-error",
        description="URI reference identifying problem type",
    )
    title: str = Field(
        "Validation Error",
        description="Short, human-readable summary",
    )
    status: int = Field(
        400,
        description="HTTP status code",
    )
    detail: str = Field(
        "Request validation failed",
        description="Human-readable explanation",
    )
    errors: list[ValidationErrorDetail] = Field(..., description="List of validation errors")
