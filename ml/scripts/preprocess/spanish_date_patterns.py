#!/usr/bin/env python3
"""
Regex patterns for Spanish textual dates.

Detects date formats common in Spanish legal documents that neural NER
models typically miss, including:
- Roman numerals: "XV de marzo del año MMXXIV"
- Fully written: "quince de marzo de dos mil veinticuatro"
- Ordinal: "primero de enero de dos mil veinticuatro"

Based on TIMEX3 annotation standards for temporal expressions.

Usage:
    python scripts/preprocess/spanish_date_patterns.py
"""

import re
import time
from dataclasses import dataclass
from typing import Iterator


@dataclass
class DateMatch:
    """A date match found by regex patterns."""
    text: str
    start: int
    end: int
    confidence: float
    pattern_name: str
    normalized: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "type": "DATE",
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "source": "regex",
            "pattern": self.pattern_name,
        }


# =============================================================================
# SPANISH MONTH NAMES
# =============================================================================

MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

MONTHS_PATTERN = "|".join(MONTHS_ES.keys())

# =============================================================================
# SPANISH NUMBER WORDS
# =============================================================================

# Cardinal numbers (1-31 for days)
CARDINAL_UNITS = {
    "uno": 1, "un": 1, "una": 1,
    "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciséis": 16, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
    "diecinueve": 19, "veinte": 20,
    "veintiuno": 21, "veintiún": 21, "veintidós": 22, "veintidos": 22,
    "veintitrés": 23, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25,
    "veintiséis": 26, "veintiseis": 26, "veintisiete": 27, "veintiocho": 28,
    "veintinueve": 29, "treinta": 30, "treinta y uno": 31,
}

# Ordinal numbers (for "primero", "segundo", etc.)
ORDINAL_UNITS = {
    "primero": 1, "primer": 1, "primera": 1,
    "segundo": 2, "segunda": 2,
    "tercero": 3, "tercer": 3, "tercera": 3,
    "cuarto": 4, "cuarta": 4,
    "quinto": 5, "quinta": 5,
    "sexto": 6, "sexta": 6,
    "séptimo": 7, "septimo": 7, "séptima": 7,
    "octavo": 8, "octava": 8,
    "noveno": 9, "novena": 9,
    "décimo": 10, "decimo": 10, "décima": 10,
}

# Year words (for "dos mil veinticuatro", etc.)
YEAR_THOUSANDS = {"mil": 1000, "dos mil": 2000}
YEAR_HUNDREDS = {
    "cien": 100, "ciento": 100,
    "doscientos": 200, "trescientos": 300, "cuatrocientos": 400,
    "quinientos": 500, "seiscientos": 600, "setecientos": 700,
    "ochocientos": 800, "novecientos": 900,
}

# Build patterns for day words
DAY_CARDINAL_PATTERN = "|".join(sorted(CARDINAL_UNITS.keys(), key=len, reverse=True))
DAY_ORDINAL_PATTERN = "|".join(sorted(ORDINAL_UNITS.keys(), key=len, reverse=True))

# =============================================================================
# ROMAN NUMERALS
# =============================================================================

ROMAN_VALUES = {
    'I': 1, 'V': 5, 'X': 10, 'L': 50,
    'C': 100, 'D': 500, 'M': 1000
}

# Pattern for Roman numerals (day: I-XXXI, year: MCMXX-MMXXX)
ROMAN_DAY_PATTERN = r'(?:XXX[I]?|XX[IVX]?|X[IVX]{0,3}|[IVX]{1,4})'
ROMAN_YEAR_PATTERN = r'M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})'


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral to integer."""
    result = 0
    prev = 0
    for char in reversed(roman.upper()):
        value = ROMAN_VALUES.get(char, 0)
        if value < prev:
            result -= value
        else:
            result += value
        prev = value
    return result


# =============================================================================
# DATE PATTERNS
# =============================================================================

# Spanish year written out pattern
# "dos mil veinticuatro", "mil novecientos ochenta y cuatro"
YEAR_WORDS_PATTERN = (
    r'(?:'
    r'(?:dos\s+)?mil'  # mil or dos mil
    r'(?:\s+(?:novecientos|ochocientos|setecientos|seiscientos|quinientos|cuatrocientos|trescientos|doscientos|ciento?))?'
    r'(?:\s+(?:noventa|ochenta|setenta|sesenta|cincuenta|cuarenta|treinta|veinti(?:nueve|ocho|siete|seis|cinco|cuatro|tres|dós|dos|uno|ún)|veinte|diecinueve|dieciocho|diecisiete|dieciséis|dieciseis|quince|catorce|trece|doce|once|diez|nueve|ocho|siete|seis|cinco|cuatro|tres|dos|uno|un))?'
    r'(?:\s+y\s+(?:nueve|ocho|siete|seis|cinco|cuatro|tres|dos|uno|un))?'
    r')'
)

DATE_PATTERNS = [
    # Roman numeral day + month + Roman year: "XV de marzo del año MMXXIV"
    (
        rf'\b({ROMAN_DAY_PATTERN})\s+de\s+({MONTHS_PATTERN})\s+del?\s+año\s+({ROMAN_YEAR_PATTERN})\b',
        "date_roman_full",
        0.95,
    ),
    # Roman numeral day + month + written year: "XV de marzo de dos mil veinticuatro"
    (
        rf'\b({ROMAN_DAY_PATTERN})\s+de\s+({MONTHS_PATTERN})\s+de\s+{YEAR_WORDS_PATTERN}\b',
        "date_roman_day_written_year",
        0.90,
    ),
    # Written day + month + written year: "quince de marzo de dos mil veinticuatro"
    (
        rf'\b({DAY_CARDINAL_PATTERN})\s+de\s+({MONTHS_PATTERN})\s+de\s+{YEAR_WORDS_PATTERN}\b',
        "date_written_full",
        0.95,
    ),
    # Ordinal day + month + written year: "primero de enero de dos mil veinticuatro"
    (
        rf'\b({DAY_ORDINAL_PATTERN})\s+de\s+({MONTHS_PATTERN})\s+de\s+{YEAR_WORDS_PATTERN}\b',
        "date_ordinal_full",
        0.95,
    ),
    # Written day + month + numeric year: "quince de marzo de 2024"
    (
        rf'\b({DAY_CARDINAL_PATTERN})\s+de\s+({MONTHS_PATTERN})\s+de\s+(\d{{4}})\b',
        "date_written_day_numeric_year",
        0.90,
    ),
    # Ordinal day + month + numeric year: "primero de enero de 2024"
    (
        rf'\b({DAY_ORDINAL_PATTERN})\s+de\s+({MONTHS_PATTERN})\s+de\s+(\d{{4}})\b',
        "date_ordinal_numeric_year",
        0.90,
    ),
    # "a X de mes de año" format (common in legal): "a quince de marzo de dos mil veinticuatro"
    (
        rf'\ba\s+({DAY_CARDINAL_PATTERN})\s+de\s+({MONTHS_PATTERN})\s+de\s+{YEAR_WORDS_PATTERN}\b',
        "date_a_written",
        0.90,
    ),
    # "el día X de mes de año": "el día quince de marzo de dos mil veinticuatro"
    (
        rf'\bel\s+día\s+({DAY_CARDINAL_PATTERN})\s+de\s+({MONTHS_PATTERN})\s+de\s+{YEAR_WORDS_PATTERN}\b',
        "date_el_dia_written",
        0.90,
    ),
    # Standard numeric with "de": "15 de marzo de 2024"
    (
        rf'\b(\d{{1,2}})\s+de\s+({MONTHS_PATTERN})\s+de\s+(\d{{4}})\b',
        "date_numeric_standard",
        0.85,
    ),
    # "día X del mes de Y del año Z": formal legal
    (
        rf'\bdía\s+(\d{{1,2}})\s+del\s+mes\s+de\s+({MONTHS_PATTERN})\s+del\s+año\s+(\d{{4}})\b',
        "date_formal_legal",
        0.90,
    ),
]


# =============================================================================
# COMPILED PATTERNS
# =============================================================================

COMPILED_DATE_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), name, conf)
    for pattern, name, conf in DATE_PATTERNS
]


# =============================================================================
# PATTERN MATCHER
# =============================================================================

def find_date_matches(text: str) -> list[DateMatch]:
    """
    Find all date matches in text.

    Args:
        text: Input text to search

    Returns:
        List of DateMatch objects, sorted by position
    """
    if not text:
        return []

    matches = []

    for pattern, name, confidence in COMPILED_DATE_PATTERNS:
        for match in pattern.finditer(text):
            matched_text = match.group(0)

            # Remove leading "a " or "el día " if captured
            display_text = matched_text
            if name == "date_a_written" and display_text.lower().startswith("a "):
                display_text = display_text[2:]
            if name == "date_el_dia_written" and display_text.lower().startswith("el día "):
                display_text = display_text[7:]

            matches.append(DateMatch(
                text=matched_text,
                start=match.start(),
                end=match.end(),
                confidence=confidence,
                pattern_name=name,
            ))

    # Sort by position, then by confidence (higher first)
    matches.sort(key=lambda m: (m.start, -m.confidence))

    # Remove overlapping matches (keep highest confidence)
    filtered = []
    last_end = -1
    for match in matches:
        if match.start >= last_end:
            filtered.append(match)
            last_end = match.end

    return filtered


# =============================================================================
# STANDALONE TESTS
# =============================================================================

@dataclass
class DateTestCase:
    """Test case for date pattern matching."""
    name: str
    text: str
    expected_count: int
    expected_text: str | None
    description: str


TEST_CASES = [
    # Roman numerals
    DateTestCase(
        "roman_full",
        "Otorgado el día XV de marzo del año MMXXIV.",
        1, "XV de marzo del año MMXXIV",
        "Roman day + month + Roman year",
    ),
    DateTestCase(
        "roman_day_only",
        "El día X de abril de dos mil veinticuatro.",
        1, "X de abril de dos mil veinticuatro",
        "Roman day + month + written year",
    ),

    # Fully written dates
    DateTestCase(
        "written_full",
        "A quince de marzo de dos mil veinticuatro.",
        1, "quince de marzo de dos mil veinticuatro",
        "Written day + month + written year",
    ),
    DateTestCase(
        "written_full_2",
        "El veintiocho de febrero de dos mil veinticinco.",
        1, "veintiocho de febrero de dos mil veinticinco",
        "Written day 28 + month + year",
    ),

    # Ordinal dates
    DateTestCase(
        "ordinal_full",
        "El primero de enero de dos mil veinticuatro.",
        1, "primero de enero de dos mil veinticuatro",
        "Ordinal day + month + written year",
    ),
    DateTestCase(
        "ordinal_segundo",
        "A segundo de mayo de dos mil veinticuatro.",
        1, "segundo de mayo de dos mil veinticuatro",
        "Segundo as ordinal",
    ),

    # Mixed formats
    DateTestCase(
        "written_numeric_year",
        "El quince de marzo de 2024.",
        1, "quince de marzo de 2024",
        "Written day + numeric year",
    ),
    DateTestCase(
        "numeric_standard",
        "Firmado el 15 de marzo de 2024.",
        1, "15 de marzo de 2024",
        "Standard numeric date",
    ),

    # Legal formats
    DateTestCase(
        "legal_a_format",
        "En Madrid, a veinte de abril de dos mil veinticuatro.",
        1, "a veinte de abril de dos mil veinticuatro",
        "Legal 'a X de mes de año' format",
    ),
    DateTestCase(
        "formal_legal",
        "El día 15 del mes de marzo del año 2024.",
        1, "día 15 del mes de marzo del año 2024",
        "Formal legal format",
    ),

    # Notarial style (from adversarial tests)
    DateTestCase(
        "notarial_header",
        "En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí.",
        1, "quince de marzo de dos mil veinticuatro",
        "Notarial deed date",
    ),

    # Multiple dates
    DateTestCase(
        "multiple_dates",
        "Desde el uno de enero de dos mil veinticuatro hasta el treinta y uno de diciembre de dos mil veinticuatro.",
        2, None,
        "Multiple dates in text",
    ),

    # Edge cases
    DateTestCase(
        "no_date",
        "El documento fue firmado por José García.",
        0, None,
        "Text without dates",
    ),
    DateTestCase(
        "partial_month_only",
        "En marzo de 2024.",
        0, None,
        "Month + year without day (not full date)",
    ),
]


def run_tests() -> tuple[int, int, list[str]]:
    """Run all date pattern tests."""
    passed = 0
    failures = []

    for test in TEST_CASES:
        matches = find_date_matches(test.text)
        actual_count = len(matches)

        # Check count
        count_ok = actual_count == test.expected_count

        # Check text if expected
        text_ok = True
        if test.expected_text and matches:
            # Allow match to contain expected or be contained
            found = any(
                test.expected_text.lower() in m.text.lower() or
                m.text.lower() in test.expected_text.lower()
                for m in matches
            )
            text_ok = found

        if count_ok and text_ok:
            passed += 1
            status = "✅"
        else:
            if not count_ok:
                failures.append(f"{test.name}: expected {test.expected_count} matches, got {actual_count}")
            elif not text_ok:
                failures.append(f"{test.name}: expected '{test.expected_text}', got {[m.text for m in matches]}")
            status = "❌"

        print(f"  {status} {test.name}: {test.description}")
        if status == "❌":
            print(f"      Input: '{test.text}'")
            print(f"      Matches: {[m.text for m in matches]}")

    return passed, len(TEST_CASES), failures


def demo_patterns():
    """Demo date pattern matching with examples."""
    print("\n" + "=" * 60)
    print("DATE PATTERN MATCHING DEMO")
    print("=" * 60)

    examples = [
        "Otorgado el día XV de marzo del año MMXXIV.",
        "El primero de enero de dos mil veinticuatro compareció.",
        "En Sevilla, a quince de marzo de dos mil veinticuatro.",
        "Firmado el 15 de marzo de 2024 en Madrid.",
        "El día 10 del mes de abril del año 2024.",
    ]

    for text in examples:
        print(f"\n>>> {text}")
        matches = find_date_matches(text)
        if matches:
            for m in matches:
                print(f"    [DATE] '{m.text}'")
                print(f"        pattern: {m.pattern_name}, conf: {m.confidence:.2f}")
        else:
            print("    (no dates detected)")


if __name__ == "__main__":
    start_time = time.time()

    print("=" * 60)
    print("SPANISH DATE PATTERNS - STANDALONE TESTS")
    print("=" * 60)
    print(f"\nTotal patterns: {len(DATE_PATTERNS)}")
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
