"""
Anonymization API schemas (DTOs).

Traceability:
- Contract: CNT-T4-ANONYMIZATION-SCHEMA-001
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnonymizationRequest(BaseModel):
    """Request schema for document anonymization."""

    level: str = Field(
        "INTERMEDIATE",
        description="Anonymization level (BASIC/INTERMEDIATE/ADVANCED)",
    )
    categories: list[str] | None = Field(
        None, description="Categories to anonymize (None = all detected)"
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate anonymization level."""
        allowed = {"BASIC", "INTERMEDIATE", "ADVANCED"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid level. Allowed: {', '.join(allowed)}")
        return v.upper()


class AnonymizationResponse(BaseModel):
    """Response schema for anonymization results."""

    document_id: UUID = Field(..., description="Document ID")
    level: str = Field(..., description="Anonymization level used")
    anonymized_content: str = Field(..., description="Anonymized text content")
    entities_replaced: int = Field(..., ge=0, description="Number of entities replaced")
    glossary_entries: int = Field(..., ge=0, description="Number of glossary entries")
    completed_at: datetime = Field(..., description="Completion timestamp")

    model_config = {"from_attributes": True}


class GlossaryEntryResponse(BaseModel):
    """Response schema for a glossary entry."""

    alias: str = Field(..., description="The alias used")
    category: str = Field(..., description="PII category")
    created_at: datetime = Field(..., description="When the alias was created")


class GlossaryResponse(BaseModel):
    """Response schema for project glossary."""

    project_id: UUID = Field(..., description="Project ID")
    entries: list[GlossaryEntryResponse] = Field(..., description="Glossary entries")
    total_entries: int = Field(..., ge=0, description="Total number of entries")

    model_config = {"from_attributes": True}
