#!/usr/bin/env python3
"""
Regex patterns for Spanish legal identifiers and dates.

Detects identifiers and dates that may have spaces, dashes, or other formatting
that neural NER models miss. Designed as a complement to transformer-based NER.

Research: CHPDA (2025) - Hybrid regex+NER approach

Patterns:
- DNI/NIE: With/without spaces and dashes
- IBAN: Spanish format with spaces
- NSS: With various separators
- CIF: Standard and spaced formats
- Phone: Spanish mobile/landline formats
- DATE: Roman numerals, written out, legal formats

Usage:
    python scripts/preprocess/spanish_id_patterns.py
"""

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# Try to import date patterns
try:
    from spanish_date_patterns import find_date_matches, DateMatch
    DATE_PATTERNS_AVAILABLE = True
except ImportError:
    try:
        # Try relative import
        from .spanish_date_patterns import find_date_matches, DateMatch
        DATE_PATTERNS_AVAILABLE = True
    except ImportError:
        DATE_PATTERNS_AVAILABLE = False
        DateMatch = None  # type: ignore


@dataclass
class RegexMatch:
    """A match found by regex patterns."""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    pattern_name: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "source": "regex",
            "pattern": self.pattern_name,
        }


# =============================================================================
# DNI/NIE PATTERNS
# =============================================================================

# DNI: 8 digits + letter, with optional spaces/dashes
DNI_PATTERNS = [
    # Standard: 12345678Z
    (r'\b(\d{8})\s*([A-Z])\b', "dni_standard", 0.95),
    # With spaces: 12 345 678 Z or 1234 5678 Z
    (r'\b(\d{2})\s+(\d{3})\s+(\d{3})\s*([A-Z])\b', "dni_spaced_2_3_3", 0.90),
    (r'\b(\d{4})\s+(\d{4})\s*([A-Z])\b', "dni_spaced_4_4", 0.90),
    # With dashes: 12-345-678-Z or 1234-5678-Z
    (r'\b(\d{2})-(\d{3})-(\d{3})-?([A-Z])\b', "dni_dashed_2_3_3", 0.90),
    (r'\b(\d{4})-(\d{4})-?([A-Z])\b', "dni_dashed_4_4", 0.90),
    # With dots: 12.345.678-Z (Spanish format)
    (r'\b(\d{2})\.(\d{3})\.(\d{3})-?([A-Z])\b', "dni_dotted", 0.90),
]

# NIE: X/Y/Z + 7 digits + letter
NIE_PATTERNS = [
    # Standard: X1234567Z
    (r'\b([XYZ])\s*(\d{7})\s*([A-Z])\b', "nie_standard", 0.95),
    # With spaces: X 1234567 Z
    (r'\b([XYZ])\s+(\d{7})\s+([A-Z])\b', "nie_spaced", 0.90),
    # With dashes: X-1234567-Z
    (r'\b([XYZ])-(\d{7})-?([A-Z])\b', "nie_dashed", 0.90),
]


# =============================================================================
# IBAN PATTERNS
# =============================================================================

# Spanish IBAN: ES + 2 check + 20 digits (24 total)
IBAN_PATTERNS = [
    # Standard: ES9121000418450200051332
    (r'\b(ES\d{22})\b', "iban_standard", 0.95),
    # With spaces (groups of 4): ES91 2100 0418 4502 0005 1332
    (r'\b(ES\d{2})\s+(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})\b', "iban_spaced_4", 0.95),
    # Partial spaces
    (r'\b(ES\d{2})\s*(\d{4})\s*(\d{4})\s*(\d{4})\s*(\d{4})\s*(\d{4})\b', "iban_mixed", 0.90),
]


# =============================================================================
# NSS PATTERNS (Número Seguridad Social)
# =============================================================================

# NSS: 12 digits (PP + 8 number + CC control)
NSS_PATTERNS = [
    # Standard: 281234567890
    (r'\b(\d{12})\b(?!\d)', "nss_standard", 0.70),  # Lower confidence - many 12-digit numbers
    # With separators: 28/12345678/90 or 28-12345678-90
    (r'\b(\d{2})[/-](\d{8})[/-](\d{2})\b', "nss_separated", 0.85),
    # Spaced: 28 12345678 90
    (r'\b(\d{2})\s+(\d{8})\s+(\d{2})\b', "nss_spaced", 0.85),
]


# =============================================================================
# CIF PATTERNS
# =============================================================================

# CIF: Letter + 7 digits + control (digit or letter)
CIF_PATTERNS = [
    # Standard: A12345678
    (r'\b([A-HJ-NP-SUVW])(\d{7})([0-9A-J])\b', "cif_standard", 0.95),
    # With dashes: A-1234567-8
    (r'\b([A-HJ-NP-SUVW])-(\d{7})-?([0-9A-J])\b', "cif_dashed", 0.90),
    # With spaces: A 1234567 8
    (r'\b([A-HJ-NP-SUVW])\s+(\d{7})\s*([0-9A-J])\b', "cif_spaced", 0.90),
]


# =============================================================================
# PHONE PATTERNS
# =============================================================================

# Spanish phones: mobile (6/7xx) and landline (9xx)
PHONE_PATTERNS = [
    # Mobile standard: 612345678
    (r'\b([67]\d{8})\b', "phone_mobile", 0.85),
    # Mobile spaced: 612 345 678 or 612 34 56 78
    (r'\b([67]\d{2})\s+(\d{3})\s+(\d{3})\b', "phone_mobile_spaced_3_3_3", 0.90),
    (r'\b([67]\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\b', "phone_mobile_spaced_3_2_2_2", 0.90),
    # With prefix: +34 612345678 or 0034 612345678
    (r'\b(?:\+34|0034)\s*([67]\d{8})\b', "phone_mobile_intl", 0.95),
    (r'\b(?:\+34|0034)\s*([67]\d{2})\s+(\d{3})\s+(\d{3})\b', "phone_mobile_intl_spaced", 0.95),
    # Landline: 912345678 or 91 234 56 78
    (r'\b(9\d{8})\b', "phone_landline", 0.80),
    (r'\b(9\d{2})\s+(\d{3})\s+(\d{3})\b', "phone_landline_spaced", 0.85),
]


# =============================================================================
# PATTERN REGISTRY
# =============================================================================

PATTERN_REGISTRY = {
    "DNI_NIE": DNI_PATTERNS + NIE_PATTERNS,
    "IBAN": IBAN_PATTERNS,
    "NSS": NSS_PATTERNS,
    "CIF": CIF_PATTERNS,
    "PHONE": PHONE_PATTERNS,
}


# =============================================================================
# COMPILED PATTERNS
# =============================================================================

def compile_patterns() -> dict[str, list[tuple[re.Pattern, str, float]]]:
    """Compile all regex patterns for efficiency."""
    compiled = {}
    for entity_type, patterns in PATTERN_REGISTRY.items():
        compiled[entity_type] = [
            (re.compile(pattern, re.IGNORECASE if entity_type != "IBAN" else 0), name, conf)
            for pattern, name, conf in patterns
        ]
    return compiled


COMPILED_PATTERNS = compile_patterns()


# =============================================================================
# PATTERN MATCHER
# =============================================================================

def find_matches(text: str, entity_types: list[str] | None = None) -> list[RegexMatch]:
    """
    Find all regex matches in text.

    Args:
        text: Input text to search
        entity_types: List of types to search for (None = all, includes DATE if available)

    Returns:
        List of RegexMatch objects, sorted by position
    """
    if not text:
        return []

    matches = []

    # Determine types to search
    all_types = list(COMPILED_PATTERNS.keys())
    if DATE_PATTERNS_AVAILABLE:
        all_types.append("DATE")
    types_to_search = entity_types or all_types

    # Search identifier patterns
    for entity_type in types_to_search:
        if entity_type == "DATE":
            continue  # Handle DATE separately below
        if entity_type not in COMPILED_PATTERNS:
            continue

        for pattern, name, confidence in COMPILED_PATTERNS[entity_type]:
            for match in pattern.finditer(text):
                # Reconstruct the full matched text (handling groups)
                matched_text = match.group(0)

                matches.append(RegexMatch(
                    text=matched_text,
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence,
                    pattern_name=name,
                ))

    # Search date patterns if available and requested
    if DATE_PATTERNS_AVAILABLE and (entity_types is None or "DATE" in entity_types):
        date_matches = find_date_matches(text)
        for dm in date_matches:
            matches.append(RegexMatch(
                text=dm.text,
                entity_type="DATE",
                start=dm.start,
                end=dm.end,
                confidence=dm.confidence,
                pattern_name=dm.pattern_name,
            ))

    # Sort by position, then by confidence (higher first for overlaps)
    matches.sort(key=lambda m: (m.start, -m.confidence))

    # Remove overlapping matches (keep highest confidence)
    filtered = []
    last_end = -1
    for match in matches:
        if match.start >= last_end:
            filtered.append(match)
            last_end = match.end

    return filtered


def normalize_match(match: RegexMatch) -> str:
    """
    Normalize a matched identifier by removing spaces/dashes.

    Useful for checksum validation.
    """
    text = match.text
    # Remove common separators
    text = text.replace(' ', '').replace('-', '').replace('.', '').replace('/', '')
    return text.upper()


# =============================================================================
# STANDALONE TESTS
# =============================================================================

@dataclass
class PatternTestCase:
    """Test case for pattern matching."""
    name: str
    text: str
    expected_type: str
    expected_count: int
    description: str


TEST_CASES = [
    # DNI standard
    PatternTestCase("dni_standard", "DNI 12345678Z del titular", "DNI_NIE", 1, "Standard DNI"),
    PatternTestCase("dni_lowercase", "dni 12345678z", "DNI_NIE", 1, "Lowercase DNI"),

    # DNI with spaces
    PatternTestCase("dni_spaces_2_3_3", "DNI 12 345 678 Z", "DNI_NIE", 1, "DNI spaced 2-3-3"),
    PatternTestCase("dni_spaces_4_4", "DNI 1234 5678 Z", "DNI_NIE", 1, "DNI spaced 4-4"),

    # DNI with dashes
    PatternTestCase("dni_dashes", "DNI 12-345-678-Z", "DNI_NIE", 1, "DNI with dashes"),
    PatternTestCase("dni_dots", "DNI 12.345.678-Z", "DNI_NIE", 1, "DNI Spanish format"),

    # NIE
    PatternTestCase("nie_standard", "NIE X1234567Z", "DNI_NIE", 1, "Standard NIE"),
    PatternTestCase("nie_spaced", "NIE X 1234567 Z", "DNI_NIE", 1, "NIE with spaces"),
    PatternTestCase("nie_dashed", "NIE X-1234567-Z", "DNI_NIE", 1, "NIE with dashes"),

    # IBAN
    PatternTestCase("iban_standard", "IBAN ES9121000418450200051332", "IBAN", 1, "Standard IBAN"),
    PatternTestCase("iban_spaced", "IBAN ES91 2100 0418 4502 0005 1332", "IBAN", 1, "IBAN with spaces"),

    # NSS
    PatternTestCase("nss_separated", "NSS 28/12345678/90", "NSS", 1, "NSS with slashes"),
    PatternTestCase("nss_spaced", "NSS 28 12345678 90", "NSS", 1, "NSS with spaces"),

    # CIF
    PatternTestCase("cif_standard", "CIF A12345674", "CIF", 1, "Standard CIF"),
    PatternTestCase("cif_dashed", "CIF A-1234567-4", "CIF", 1, "CIF with dashes"),

    # Phone
    PatternTestCase("phone_mobile", "Tel: 612345678", "PHONE", 1, "Mobile phone"),
    PatternTestCase("phone_mobile_spaced", "Tel: 612 345 678", "PHONE", 1, "Mobile spaced"),
    PatternTestCase("phone_intl", "Tel: +34 612345678", "PHONE", 1, "International format"),
    PatternTestCase("phone_landline", "Tel: 912345678", "PHONE", 1, "Landline"),

    # Multiple in same text
    PatternTestCase("multiple", "DNI 12345678Z y teléfono 612345678", "DNI_NIE", 1, "Multiple entities"),

    # Negative cases
    PatternTestCase("not_dni_short", "Número 1234567Z", "DNI_NIE", 0, "Too short for DNI"),
    PatternTestCase("not_iban_short", "ES91 2100 0418", "IBAN", 0, "Incomplete IBAN"),
]


def run_tests() -> tuple[int, int, list[str]]:
    """Run all pattern tests."""
    passed = 0
    failures = []

    for test in TEST_CASES:
        matches = find_matches(test.text, [test.expected_type])
        actual_count = len(matches)

        if actual_count == test.expected_count:
            passed += 1
            status = "✅"
        else:
            failures.append(f"{test.name}: expected {test.expected_count}, got {actual_count}")
            status = "❌"

        print(f"  {status} {test.name}: {test.description}")
        if actual_count != test.expected_count:
            print(f"      Input: '{test.text}'")
            print(f"      Matches: {[m.text for m in matches]}")

    return passed, len(TEST_CASES), failures


def demo_patterns():
    """Demo pattern matching with examples."""
    print("\n" + "=" * 60)
    print("PATTERN MATCHING DEMO")
    print("=" * 60)

    examples = [
        "El titular con DNI 12 345 678 Z compareció ante notario.",
        "Transferir a cuenta IBAN ES91 2100 0418 4502 0005 1332.",
        "Contactar al 612 345 678 o al +34 912345678.",
        "NIE X-1234567-Z del extranjero residente.",
        "La empresa con CIF A-1234567-4 fue notificada.",
    ]

    for text in examples:
        print(f"\n>>> {text}")
        matches = find_matches(text)
        if matches:
            for m in matches:
                normalized = normalize_match(m)
                print(f"    [{m.entity_type}] '{m.text}' → normalized: '{normalized}'")
                print(f"        pattern: {m.pattern_name}, conf: {m.confidence:.2f}")
        else:
            print("    (no matches)")


if __name__ == "__main__":
    start_time = time.time()

    print("=" * 60)
    print("SPANISH ID PATTERNS - STANDALONE TESTS")
    print("=" * 60)
    print(f"\nEntity types: {list(PATTERN_REGISTRY.keys())}")
    print(f"Total patterns: {sum(len(p) for p in PATTERN_REGISTRY.values())}")
    print(f"\nRunning {len(TEST_CASES)} test cases...\n")

    passed, total, failures = run_tests()

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} passed ({100*passed/total:.1f}%)")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")

    demo_patterns()

    elapsed = time.time() - start_time
    print(f"\nTiempo de ejecución: {elapsed:.3f}s")

    exit(0 if passed == total else 1)
