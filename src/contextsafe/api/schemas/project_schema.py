"""
Project API schemas (DTOs).

Traceability:
- Contract: CNT-T4-PROJECT-SCHEMA-001
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProjectRequest(BaseModel):
    """Request schema for project creation/update."""

    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str | None = Field(None, max_length=500, description="Project description")
    default_anonymization_level: str = Field(
        "INTERMEDIATE",
        description="Default anonymization level (BASIC/INTERMEDIATE/ADVANCED)",
    )

    @field_validator("default_anonymization_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate anonymization level."""
        allowed = {"BASIC", "INTERMEDIATE", "ADVANCED"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid level. Allowed: {', '.join(allowed)}")
        return v.upper()


class ProjectResponse(BaseModel):
    """Response schema for project."""

    id: UUID = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: str | None = Field(None, description="Project description")
    anonymization_level: str = Field("intermediate", alias="anonymizationLevel", description="Anonymization level")
    created_at: datetime = Field(..., alias="createdAt", description="Creation timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="Update timestamp")
    document_count: int = Field(0, alias="documentCount", description="Number of documents")
    entity_count: int = Field(0, alias="entityCount", description="Number of detected entities")
    completion_percentage: int = Field(0, alias="completionPercentage", description="Processing completion percentage")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ProjectListResponse(BaseModel):
    """Response schema for project list."""

    items: list[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total count")
