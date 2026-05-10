"""
Anonymization domain services.

Exports:
- normalize_pii_value: Centralized PII normalization function
- get_lookup_key: Generate glossary lookup keys
- values_match: Check if two values represent the same entity
- find_matching_value: Find matching value in glossary
- DateShifter: Service for uniform date shifting
- get_date_shifter: Get global date shifter instance
"""

from contextsafe.domain.anonymization.services.date_shifter import (
    DateShiftConfig,
    DateShifter,
    get_date_shifter,
)
from contextsafe.domain.anonymization.services.normalization import (
    find_matching_value,
    get_lookup_key,
    normalize_pii_value,
    values_match,
)


__all__ = [
    # Normalization
    "normalize_pii_value",
    "get_lookup_key",
    "values_match",
    "find_matching_value",
    # Date shifting
    "DateShifter",
    "DateShiftConfig",
    "get_date_shifter",
]
