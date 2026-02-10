"""
Normalization service facade.

Re-exports domain normalization functions for use by the API layer,
maintaining hexagonal architecture (API → Application → Domain).
"""

from contextsafe.domain.anonymization.services.normalization import (
    normalize_pii_value,
    values_match,
)

__all__ = ["normalize_pii_value", "values_match"]
