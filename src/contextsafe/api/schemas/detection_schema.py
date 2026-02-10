"""
Detection API schemas (DTOs).

Traceability:
- Contract: CNT-T4-DETECTION-SCHEMA-001
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DetectionRequest(BaseModel):
    """Request schema for PII detection."""

    categories: list[str] | None = Field(None, description="Categories to detect (None = all)")
    confidence_threshold: float = Field(
        0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str] | None) -> list[str] | None:
        """Validate category names."""
        if v is None:
            return None
        allowed = {
            "PERSON_NAME",
            "ORGANIZATION",
            "ADDRESS",
            "DNI_NIE",
            "PASSPORT",
            "PHONE",
            "EMAIL",
            "BANK_ACCOUNT",
            "CREDIT_CARD",
            "DATE",
            "MEDICAL_RECORD",
            "LICENSE_PLATE",
            "SOCIAL_SECURITY",
        }
        for cat in v:
            if cat.upper() not in allowed:
                raise ValueError(f"Invalid category: {cat}")
        return [c.upper() for c in v]


class PiiEntityResponse(BaseModel):
    """Response schema for a detected PII entity."""

    category: str = Field(..., description="PII category")
    text: str = Field(..., description="Detected text")
    start_offset: int = Field(..., ge=0, description="Start position in text")
    end_offset: int = Field(..., ge=0, description="End position in text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class DetectionResponse(BaseModel):
    """Response schema for detection results."""

    document_id: UUID = Field(..., description="Document ID")
    entities_found: int = Field(..., ge=0, description="Number of entities found")
    entities: list[PiiEntityResponse] = Field(..., description="Detected entities")
    detection_completed_at: datetime = Field(..., description="Completion timestamp")

    model_config = {"from_attributes": True}
