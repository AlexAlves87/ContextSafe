"""
Centralized PII value normalization module.

CRITICAL: This is the SINGLE SOURCE OF TRUTH for normalization.
All glossary lookups MUST use these functions to ensure consistency.

Traceability:
- Bug Fix: Corrección #5 - Inconsistencia de entidades
- Bug Fix: FP-6 - Typos no consolidados (Tapia vs Tapias)
- Audit: PLAN_CORRECCION_AUDITORIA.md
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

# Fuzzy matching for typo handling (FP-6)
try:
    from thefuzz import fuzz
    THEFUZZ_AVAILABLE = True
except ImportError:
    THEFUZZ_AVAILABLE = False


# Minimum similarity ratio for fuzzy matching (0-100)
# High threshold (90+) to avoid false positive consolidations
FUZZY_MATCH_THRESHOLD = 90


# ============================================================================
# NORMALIZATION PATTERNS
# ============================================================================

# Spanish honorific prefixes to strip during normalization
HONORIFIC_PREFIXES = re.compile(
    r"^(?:D\.?ª?|Dña\.?|Don|Doña|Sr\.?|Sra\.?|Señor|Señora|"
    r"Ilmo\.?|Excmo\.?|Ilma\.?|Excma\.?|Dr\.?|Dra\.?)\s+",
    re.IGNORECASE | re.UNICODE
)

# Legal form suffixes to normalize (Spanish company types)
LEGAL_SUFFIXES = re.compile(
    r"\s*,?\s*(?:S\.?\s*L\.?\s*P\.?|S\.?\s*L\.?\s*U\.?|S\.?\s*L\.?|"
    r"S\.?\s*A\.?\s*U\.?|S\.?\s*A\.?|S\.?\s*C\.?|C\.?\s*B\.?|"
    r"S\.?\s*Coop\.?|Coop\.?)\s*\.?\s*$",
    re.IGNORECASE
)

# Categories that use person-specific normalization
PERSON_CATEGORIES = {"PERSON_NAME"}

# Categories that use organization-specific normalization
ORG_CATEGORIES = {"ORGANIZATION"}


def normalize_pii_value(value: str, category: str = "") -> str:
    """
    Normalize a PII value for consistent glossary lookup.

    This function MUST be used in ALL places where the glossary is accessed
    to guarantee that variations of the same entity receive the same alias.

    Normalization steps:
    1. Strip whitespace
    2. (PERSON) Remove honorific prefixes (D., Dña., Don, Doña, Sr., Sra., etc.)
    3. (ORG) Normalize legal form suffixes (S.L., S.A., S.L.P., etc.)
    4. Unicode NFC normalization
    5. Collapse multiple spaces
    6. Strip and lowercase

    Args:
        value: Original PII value
        category: PII category (for category-specific normalization)

    Returns:
        Normalized value for lookup

    Examples:
        >>> normalize_pii_value("D. Juan García López", "PERSON_NAME")
        "juan garcía lópez"
        >>> normalize_pii_value("MENTOR ABOGADOS S.L.P.", "ORGANIZATION")
        "mentor abogados"
        >>> normalize_pii_value("Mentor Abogados, SLP", "ORGANIZATION")
        "mentor abogados"
    """
    if not value:
        return ""

    normalized = value.strip()

    # Category-specific normalization
    if category in PERSON_CATEGORIES or (not category):
        # Remove honorific prefixes for persons
        normalized = HONORIFIC_PREFIXES.sub("", normalized)

    if category in ORG_CATEGORIES or (not category):
        # Normalize legal form suffixes for organizations
        normalized = LEGAL_SUFFIXES.sub("", normalized)
        # Remove trailing punctuation
        normalized = normalized.rstrip(".,;:")

    # Unicode normalization (NFC form)
    normalized = unicodedata.normalize("NFC", normalized)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Final strip and lowercase
    return normalized.strip().lower()


def get_lookup_key(value: str, category: str) -> str:
    """
    Generate the glossary lookup key for a PII value.

    The key format is: "{category}:{normalized_value}"

    Args:
        value: Original PII value
        category: PII category

    Returns:
        Unique lookup key for the glossary

    Examples:
        >>> get_lookup_key("D. Juan García", "PERSON_NAME")
        "PERSON_NAME:juan garcía"
        >>> get_lookup_key("MENTOR ABOGADOS S.L.P.", "ORGANIZATION")
        "ORGANIZATION:mentor abogados"
    """
    normalized = normalize_pii_value(value, category)
    return f"{category}:{normalized}"


def values_match(value1: str, value2: str, category: str = "") -> bool:
    """
    Check if two PII values represent the same entity.

    Uses normalization to compare values, so variations like
    "D. Juan García" and "Juan García" will match.

    Args:
        value1: First value
        value2: Second value
        category: PII category (for category-specific normalization)

    Returns:
        True if values represent the same entity

    Examples:
        >>> values_match("D. Juan García", "Juan García", "PERSON_NAME")
        True
        >>> values_match("MENTOR ABOGADOS SLP", "Mentor Abogados, S.L.P.", "ORGANIZATION")
        True
    """
    return normalize_pii_value(value1, category) == normalize_pii_value(value2, category)


def find_matching_value(
    target: str,
    candidates: dict[str, str],
    category: str,
) -> Optional[str]:
    """
    Find a matching value in a dictionary of candidates.

    Useful for finding existing glossary entries that match a new value.

    For PERSON_NAME category, also matches partial names:
    - "Alberto Baxeras" matches "Alberto Baxeras Aizpún"
    - The shorter name is considered a partial reference to the full name

    Args:
        target: Value to find
        candidates: Dictionary of {original_value: alias}
        category: PII category

    Returns:
        The alias if a match is found, None otherwise

    Examples:
        >>> glossary = {"D. Juan García": "Persona_001"}
        >>> find_matching_value("Juan García", glossary, "PERSON_NAME")
        "Persona_001"
        >>> glossary = {"D. Alberto Baxeras Aizpún": "Persona_001"}
        >>> find_matching_value("D. Alberto Baxeras", glossary, "PERSON_NAME")
        "Persona_001"
    """
    target_normalized = normalize_pii_value(target, category)

    # First pass: exact match (normalized)
    for original, alias in candidates.items():
        if normalize_pii_value(original, category) == target_normalized:
            return alias

    # Second pass: partial name matching (PERSON_NAME only)
    # "alberto baxeras" should match "alberto baxeras aizpún"
    if category == "PERSON_NAME" and target_normalized:
        target_parts = target_normalized.split()

        # Need at least 2 parts (name + surname) to match partially
        if len(target_parts) >= 2:
            for original, alias in candidates.items():
                original_normalized = normalize_pii_value(original, category)
                original_parts = original_normalized.split()

                # Check if target is a prefix of original (same first N words)
                # "alberto baxeras" matches "alberto baxeras aizpún"
                if len(original_parts) > len(target_parts):
                    if original_parts[:len(target_parts)] == target_parts:
                        return alias

                # Check if original is a prefix of target
                # "alberto baxeras aizpún" should find alias of "alberto baxeras"
                elif len(target_parts) > len(original_parts):
                    if target_parts[:len(original_parts)] == original_parts:
                        return alias

    # Third pass: fuzzy matching for typos (PERSON_NAME only)
    # "tapia hermida" should match "tapias hermida" (common typos)
    # FP-6: Typos no consolidados
    if THEFUZZ_AVAILABLE and category == "PERSON_NAME" and target_normalized:
        for original, alias in candidates.items():
            original_normalized = normalize_pii_value(original, category)
            # Use token_sort_ratio for better handling of word order variations
            # and fuzz.ratio for exact character comparison
            ratio = fuzz.ratio(target_normalized, original_normalized)
            if ratio >= FUZZY_MATCH_THRESHOLD:
                return alias
            # Also try token sort ratio for reordered names
            token_ratio = fuzz.token_sort_ratio(target_normalized, original_normalized)
            if token_ratio >= FUZZY_MATCH_THRESHOLD:
                return alias

    return None
