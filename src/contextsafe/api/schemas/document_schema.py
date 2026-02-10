"""
Document API schemas (DTOs).

Traceability:
- Contract: CNT-T4-DOCUMENT-SCHEMA-001
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DocumentRequest(BaseModel):
    """Request schema for document upload."""

    project_id: UUID = Field(..., description="Project to add document to")
    filename: str = Field(..., max_length=255, description="Original filename")
    content_type: str | None = Field(None, description="MIME type of the document")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename has allowed extension."""
        allowed_extensions = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".docx"}
        ext = v.rsplit(".", 1)[-1].lower() if "." in v else ""
        if f".{ext}" not in allowed_extensions:
            raise ValueError(f"Invalid extension. Allowed: {', '.join(allowed_extensions)}")
        return v


class DocumentResponse(BaseModel):
    """Response schema for document."""

    id: UUID = Field(..., description="Document ID")
    project_id: UUID = Field(..., description="Parent project ID")
    filename: str = Field(..., description="Original filename")
    state: str = Field(..., description="Current processing state")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Response schema for document list."""

    items: list[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
