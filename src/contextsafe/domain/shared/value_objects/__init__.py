"""
Value objects for the ContextSafe domain.

All value objects are:
- Immutable (frozen dataclasses)
- Validated via factory methods returning Result types
- Compared by value, not identity
"""
from contextsafe.domain.shared.value_objects.alias import Alias
from contextsafe.domain.shared.value_objects.anonymization_level import (
    ADVANCED,
    BASIC,
    INTERMEDIATE,
    AnonymizationLevel,
    AnonymizationLevelEnum,
)
from contextsafe.domain.shared.value_objects.confidence_score import (
    REVIEW_THRESHOLD,
    ConfidenceScore,
)
from contextsafe.domain.shared.value_objects.document_id import DocumentId
from contextsafe.domain.shared.value_objects.document_state import (
    ANONYMIZED,
    ANONYMIZING,
    DETECTED,
    DETECTING,
    FAILED,
    INGESTED,
    PENDING,
    DocumentState,
    DocumentStateEnum,
)
from contextsafe.domain.shared.value_objects.entity_id import EntityId
from contextsafe.domain.shared.value_objects.pii_category import (
    ADDRESS,
    BANK_ACCOUNT,
    CASE_NUMBER,
    CREDIT_CARD,
    DATE,
    DNI_NIE,
    EMAIL,
    IBAN,
    IP_ADDRESS,
    LICENSE_PLATE,
    LOCATION,
    MEDICAL_RECORD,
    ORGANIZATION,
    PASSPORT,
    PERSON_NAME,
    PHONE,
    PLATFORM,
    POSTAL_CODE,
    PROFESSIONAL_ID,
    SOCIAL_SECURITY,
    PiiCategory,
    PiiCategoryEnum,
)
from contextsafe.domain.shared.value_objects.project_id import ProjectId
from contextsafe.domain.shared.value_objects.text_span import TextSpan

__all__ = [
    # IDs
    "DocumentId",
    "ProjectId",
    "EntityId",
    # Core value objects
    "Alias",
    "ConfidenceScore",
    "TextSpan",
    # Enums with constants
    "PiiCategory",
    "PiiCategoryEnum",
    "PERSON_NAME",
    "ORGANIZATION",
    "ADDRESS",
    "LOCATION",
    "POSTAL_CODE",
    "DNI_NIE",
    "PASSPORT",
    "PHONE",
    "EMAIL",
    "BANK_ACCOUNT",
    "IBAN",
    "CREDIT_CARD",
    "DATE",
    "MEDICAL_RECORD",
    "LICENSE_PLATE",
    "SOCIAL_SECURITY",
    "PROFESSIONAL_ID",
    "CASE_NUMBER",
    "PLATFORM",
    "IP_ADDRESS",
    # Anonymization levels
    "AnonymizationLevel",
    "AnonymizationLevelEnum",
    "BASIC",
    "INTERMEDIATE",
    "ADVANCED",
    # Document states
    "DocumentState",
    "DocumentStateEnum",
    "PENDING",
    "INGESTED",
    "DETECTING",
    "DETECTED",
    "ANONYMIZING",
    "ANONYMIZED",
    "FAILED",
    # Constants
    "REVIEW_THRESHOLD",
]
