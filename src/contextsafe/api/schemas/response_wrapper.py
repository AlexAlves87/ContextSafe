"""
API Response Wrapper - Standard format for all API responses.

All API responses MUST use this wrapper to ensure frontend-backend consistency.

Format:
  Success: {"data": <payload>, "meta": {...}}
  Error: {"error": {"code": "...", "message": "..."}}

Traceability:
- Standard: consolidated_standards.yaml#vocabulary.dtos
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    data: T = Field(..., description="Response payload")
    meta: dict[str, Any] | None = Field(default=None, description="Optional metadata")


class PaginatedMeta(BaseModel):
    """Pagination metadata."""

    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")


class ApiListResponse(BaseModel, Generic[T]):
    """Standard API list response wrapper with pagination."""

    data: list[T] = Field(..., description="List of items")
    meta: PaginatedMeta = Field(..., description="Pagination metadata")


class ErrorDetail(BaseModel):
    """Error detail."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional details")


class ApiErrorResponse(BaseModel):
    """Standard API error response."""

    error: ErrorDetail = Field(..., description="Error information")
