#!/usr/bin/env python3
"""
Boundary refinement for NER entity detection.

Post-processes detected entities to fix common boundary issues:
- OVER_EXTENDED: Strips honorific prefixes, trailing punctuation
- TRUNCATED: Extends partial matches (postal codes, DNI letters)

Research basis: SemEval 2013 Task 9 evaluation framework distinguishes
PAR (partial) from COR (correct) matches based on exact boundary alignment.

Usage:
    python scripts/preprocess/boundary_refinement.py
"""

import re
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class RefinedEntity:
    """Entity after boundary refinement."""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    source: str
    original_text: str | None = None
    refinement_applied: str | None = None


# =============================================================================
# HONORIFIC PREFIXES (Spanish legal documents)
# =============================================================================

# Order matters: longer prefixes first to avoid partial matches
PERSON_PREFIXES = [
    # Full honorifics
    r"(?:Compareció\s+)?Don\s+",
    r"(?:Compareció\s+)?Doña\s+",
    r"Dña\.\s*",
    r"D\.\s*",
    # English (mixed documents)
    r"Mr\.\s*",
    r"Mrs\.\s*",
    r"Ms\.\s*",
    # Titles
    r"(?:el\s+)?Notario\s+",
    r"(?:el\s+)?Testigo\s+",
    r"(?:la\s+)?Señora\s+",
    r"(?:el\s+)?Señor\s+",
]

# Compiled pattern for stripping prefixes
PERSON_PREFIX_PATTERN = re.compile(
    r"^(" + "|".join(PERSON_PREFIXES) + ")",
    re.IGNORECASE
)


# =============================================================================
# DATE PREFIXES
# =============================================================================

DATE_PREFIXES = [
    r"^a\s+",           # "a quince de marzo"
    r"^el\s+día\s+",    # "el día quince"
    r"^día\s+",         # "día quince"
    r"^en\s+",          # "en quince de marzo"
]

DATE_PREFIX_PATTERN = re.compile(
    r"(" + "|".join(DATE_PREFIXES) + ")",
    re.IGNORECASE
)


# =============================================================================
# ORGANIZATION SUFFIXES
# =============================================================================

ORG_SUFFIX_PATTERN = re.compile(r"[,;:]+\s*$")


# =============================================================================
# POSTAL CODE EXTENSION
# =============================================================================

# Spanish postal codes: 5 digits, first 2 are province (01-52)
POSTAL_CODE_EXTEND_PATTERN = re.compile(
    r"^(\d{2,4})$"  # Partial postal code (2-4 digits)
)


# =============================================================================
# DNI/NIE EXTENSION
# =============================================================================

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

DNI_EXTEND_PATTERN = re.compile(
    r"^(\d{8})[-\s]?$"  # 8 digits, possibly with trailing dash/space
)

NIE_EXTEND_PATTERN = re.compile(
    r"^([XYZ])[-\s]?(\d{7})[-\s]?$"  # X/Y/Z + 7 digits, incomplete
)


# =============================================================================
# REFINEMENT FUNCTIONS
# =============================================================================

def refine_person(text: str, original_text: str) -> tuple[str, str | None]:
    """
    Refine PERSON entity boundaries.

    Strips honorific prefixes while preserving the actual name.

    Args:
        text: Detected entity text
        original_text: Full original text (for context extension)

    Returns:
        Tuple of (refined_text, refinement_type or None)
    """
    match = PERSON_PREFIX_PATTERN.match(text)
    if match:
        prefix = match.group(1)
        refined = text[len(prefix):].strip()
        if refined:  # Don't return empty string
            return refined, f"stripped_prefix:{prefix.strip()}"

    return text, None


def refine_date(text: str, original_text: str) -> tuple[str, str | None]:
    """
    Refine DATE entity boundaries.

    Strips common date prefixes in Spanish legal text.
    """
    match = DATE_PREFIX_PATTERN.match(text)
    if match:
        prefix = match.group(1)
        refined = text[len(prefix):].strip()
        if refined:
            return refined, f"stripped_prefix:{prefix.strip()}"

    return text, None


def refine_organization(text: str, original_text: str) -> tuple[str, str | None]:
    """
    Refine ORGANIZATION entity boundaries.

    Strips trailing punctuation.
    """
    match = ORG_SUFFIX_PATTERN.search(text)
    if match:
        refined = text[:match.start()].strip()
        if refined:
            return refined, f"stripped_suffix:{match.group()}"

    return text, None


def refine_postal_code(text: str, original_text: str, entity_end: int) -> tuple[str, str | None]:
    """
    Refine POSTAL_CODE entity boundaries.

    Extends partial postal codes to full 5 digits if available in context.
    """
    match = POSTAL_CODE_EXTEND_PATTERN.match(text)
    if match and len(text) < 5:
        # Look ahead in original text for remaining digits
        remaining_needed = 5 - len(text)
        if entity_end < len(original_text):
            lookahead = original_text[entity_end:entity_end + remaining_needed + 2]
            # Find consecutive digits
            digit_match = re.match(r"(\d+)", lookahead)
            if digit_match:
                extra_digits = digit_match.group(1)[:remaining_needed]
                extended = text + extra_digits
                if len(extended) == 5:
                    return extended, f"extended_postal:{remaining_needed}_digits"

    return text, None


def refine_dni_nie(text: str, original_text: str, entity_end: int) -> tuple[str, str | None]:
    """
    Refine DNI_NIE entity boundaries.

    Extends to include control letter if missing.
    """
    # Check if DNI missing letter
    dni_match = DNI_EXTEND_PATTERN.match(text)
    if dni_match:
        number = dni_match.group(1)
        # Look for letter after entity
        if entity_end < len(original_text):
            next_char = original_text[entity_end:entity_end + 2].strip()
            if next_char and next_char[0].upper() in DNI_LETTERS:
                extended = number + next_char[0].upper()
                return extended, "extended_dni_letter"

    # Check if NIE missing letter
    nie_match = NIE_EXTEND_PATTERN.match(text)
    if nie_match:
        prefix, number = nie_match.groups()
        # Look for letter after entity
        if entity_end < len(original_text):
            next_char = original_text[entity_end:entity_end + 2].strip()
            if next_char and next_char[0].upper() in DNI_LETTERS:
                extended = prefix + number + next_char[0].upper()
                return extended, "extended_nie_letter"

    return text, None


def refine_address(text: str, original_text: str) -> tuple[str, str | None]:
    """
    Refine ADDRESS entity boundaries.

    Handles addresses that incorrectly include postal code or city.
    """
    # Pattern: Address ending with postal code and/or city
    # "Calle Mayor 15, 3º B, 28001 Madrid" -> "Calle Mayor 15, 3º B"

    # Check for trailing postal code + city
    postal_city_pattern = re.compile(
        r",?\s*\d{5}\s+[A-ZÁÉÍÓÚ][a-záéíóú]+\.?$",
        re.IGNORECASE
    )
    match = postal_city_pattern.search(text)
    if match:
        refined = text[:match.start()].strip().rstrip(",")
        if refined:
            return refined, "stripped_postal_city"

    # Check for just postal code at end
    postal_pattern = re.compile(r",?\s*\d{5}$")
    match = postal_pattern.search(text)
    if match:
        refined = text[:match.start()].strip().rstrip(",")
        if refined:
            return refined, "stripped_postal"

    return text, None


# =============================================================================
# REFINEMENT REGISTRY
# =============================================================================

REFINEMENT_FUNCTIONS: dict[str, Callable] = {
    "PERSON": refine_person,
    "DATE": refine_date,
    "ORGANIZATION": refine_organization,
    "ADDRESS": refine_address,
}

# Special handlers that need entity position
POSITION_AWARE_REFINEMENTS: dict[str, Callable] = {
    "POSTAL_CODE": refine_postal_code,
    "DNI_NIE": refine_dni_nie,
}


# =============================================================================
# MAIN REFINEMENT FUNCTION
# =============================================================================

def refine_entity(
    text: str,
    entity_type: str,
    start: int,
    end: int,
    confidence: float,
    source: str,
    original_text: str,
) -> RefinedEntity:
    """
    Apply boundary refinement to a single entity.

    Args:
        text: Entity text
        entity_type: Entity type (PERSON, DATE, etc.)
        start: Start position in original text
        end: End position in original text
        confidence: Detection confidence
        source: Detection source (ner, regex, etc.)
        original_text: Full original text for context

    Returns:
        RefinedEntity with potentially adjusted boundaries
    """
    refined_text = text
    refinement_applied = None

    # Apply standard refinement if available
    if entity_type in REFINEMENT_FUNCTIONS:
        refined_text, refinement_applied = REFINEMENT_FUNCTIONS[entity_type](
            text, original_text
        )

    # Apply position-aware refinement if available
    if entity_type in POSITION_AWARE_REFINEMENTS and refinement_applied is None:
        refined_text, refinement_applied = POSITION_AWARE_REFINEMENTS[entity_type](
            text, original_text, end
        )

    # Calculate new positions if text changed
    new_start = start
    new_end = end

    if refined_text != text:
        # For prefix stripping, adjust start
        if refinement_applied and "stripped_prefix" in refinement_applied:
            prefix_len = len(text) - len(refined_text)
            new_start = start + prefix_len
            new_end = end
        # For suffix stripping, adjust end
        elif refinement_applied and "stripped_suffix" in refinement_applied:
            suffix_len = len(text) - len(refined_text)
            new_end = end - suffix_len
        # For extensions, adjust end
        elif refinement_applied and "extended" in refinement_applied:
            extension_len = len(refined_text) - len(text)
            new_end = end + extension_len

    return RefinedEntity(
        text=refined_text,
        entity_type=entity_type,
        start=new_start,
        end=new_end,
        confidence=confidence,
        source=source,
        original_text=text if refinement_applied else None,
        refinement_applied=refinement_applied,
    )


def refine_entities(
    entities: list[dict],
    original_text: str,
) -> list[RefinedEntity]:
    """
    Apply boundary refinement to a list of entities.

    Args:
        entities: List of entity dicts with text, entity_type, start, end, confidence, source
        original_text: Full original text for context

    Returns:
        List of RefinedEntity objects
    """
    refined = []

    for entity in entities:
        refined_entity = refine_entity(
            text=entity.get("text", ""),
            entity_type=entity.get("entity_type", entity.get("type", "")),
            start=entity.get("start", 0),
            end=entity.get("end", 0),
            confidence=entity.get("confidence", 0.0),
            source=entity.get("source", "unknown"),
            original_text=original_text,
        )
        refined.append(refined_entity)

    return refined


# =============================================================================
# STANDALONE TESTS
# =============================================================================

@dataclass
class RefinementTestCase:
    """Test case for boundary refinement."""
    name: str
    entity_type: str
    text: str
    original_text: str
    entity_end: int
    expected_text: str
    expected_refinement: str | None
    description: str


TEST_CASES = [
    # PERSON prefix stripping
    RefinementTestCase(
        name="person_don",
        entity_type="PERSON",
        text="Don José García López",
        original_text="Compareció Don José García López ante el notario.",
        entity_end=22,
        expected_text="José García López",
        expected_refinement="stripped_prefix:Don",
        description="Strip 'Don' prefix",
    ),
    RefinementTestCase(
        name="person_dña",
        entity_type="PERSON",
        text="Dña. Ana Martínez",
        original_text="De otra parte, Dña. Ana Martínez con NIF...",
        entity_end=26,
        expected_text="Ana Martínez",
        expected_refinement="stripped_prefix:Dña.",
        description="Strip 'Dña.' prefix",
    ),
    RefinementTestCase(
        name="person_d_dot",
        entity_type="PERSON",
        text="D. Pedro García",
        original_text="representada por D. Pedro García López.",
        entity_end=25,
        expected_text="Pedro García",
        expected_refinement="stripped_prefix:D.",
        description="Strip 'D.' prefix",
    ),
    RefinementTestCase(
        name="person_mr",
        entity_type="PERSON",
        text="Mr. John Smith",
        original_text="Mr. John Smith, residente en...",
        entity_end=14,
        expected_text="John Smith",
        expected_refinement="stripped_prefix:Mr.",
        description="Strip 'Mr.' prefix (mixed language)",
    ),
    RefinementTestCase(
        name="person_no_change",
        entity_type="PERSON",
        text="José María Fernández",
        original_text="El señor José María Fernández compareció.",
        entity_end=29,
        expected_text="José María Fernández",
        expected_refinement=None,
        description="No prefix to strip",
    ),

    # DATE prefix stripping
    RefinementTestCase(
        name="date_a_prefix",
        entity_type="DATE",
        text="a quince de marzo de dos mil veinticuatro",
        original_text="En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro.",
        entity_end=65,
        expected_text="quince de marzo de dos mil veinticuatro",
        expected_refinement="stripped_prefix:a",
        description="Strip 'a' prefix from date",
    ),
    RefinementTestCase(
        name="date_el_dia",
        entity_type="DATE",
        text="el día veinte de abril",
        original_text="Firmado el día veinte de abril de dos mil.",
        entity_end=30,
        expected_text="veinte de abril",
        expected_refinement="stripped_prefix:el día",
        description="Strip 'el día' prefix",
    ),

    # ORGANIZATION suffix stripping
    RefinementTestCase(
        name="org_trailing_comma",
        entity_type="ORGANIZATION",
        text="INMOBILIARIA GARCÍA, S.L.,",
        original_text="De una parte, INMOBILIARIA GARCÍA, S.L., con CIF...",
        entity_end=40,
        expected_text="INMOBILIARIA GARCÍA, S.L.",
        expected_refinement="stripped_suffix:,",
        description="Strip trailing comma",
    ),

    # ADDRESS refinement
    RefinementTestCase(
        name="address_with_postal_city",
        entity_type="ADDRESS",
        text="Plaza Mayor 1, 28013 Madrid",
        original_text="domiciliada en Plaza Mayor 1, 28013 Madrid, representada...",
        entity_end=42,
        expected_text="Plaza Mayor 1",
        expected_refinement="stripped_postal_city",
        description="Strip postal code and city from address",
    ),

    # POSTAL_CODE extension
    RefinementTestCase(
        name="postal_extend",
        entity_type="POSTAL_CODE",
        text="28",
        original_text="código postal 28001 Madrid.",
        entity_end=16,
        expected_text="28001",
        expected_refinement="extended_postal:3_digits",
        description="Extend partial postal code",
    ),

    # DNI extension
    RefinementTestCase(
        name="dni_extend_letter",
        entity_type="DNI_NIE",
        text="12345678-",
        original_text="con DNI 12345678-Z compareció.",
        entity_end=17,
        expected_text="12345678Z",
        expected_refinement="extended_dni_letter",
        description="Extend DNI with missing letter",
    ),
    RefinementTestCase(
        name="dni_no_extend",
        entity_type="DNI_NIE",
        text="12345678Z",
        original_text="con DNI 12345678Z compareció.",
        entity_end=17,
        expected_text="12345678Z",
        expected_refinement=None,
        description="Complete DNI, no extension needed",
    ),
]


def run_tests() -> tuple[int, int, list[str]]:
    """Run all refinement tests."""
    passed = 0
    failures = []

    for test in TEST_CASES:
        refined = refine_entity(
            text=test.text,
            entity_type=test.entity_type,
            start=0,
            end=test.entity_end,
            confidence=0.9,
            source="test",
            original_text=test.original_text,
        )

        text_match = refined.text == test.expected_text

        # Check refinement type (handle None)
        if test.expected_refinement is None:
            refinement_match = refined.refinement_applied is None
        else:
            refinement_match = (
                refined.refinement_applied is not None and
                test.expected_refinement in refined.refinement_applied
            )

        if text_match and refinement_match:
            passed += 1
            status = "✅"
        else:
            failures.append(
                f"{test.name}: expected '{test.expected_text}' ({test.expected_refinement}), "
                f"got '{refined.text}' ({refined.refinement_applied})"
            )
            status = "❌"

        print(f"  {status} {test.name}: {test.description}")
        if not text_match or not refinement_match:
            print(f"      Input: '{test.text}'")
            print(f"      Expected: '{test.expected_text}' ({test.expected_refinement})")
            print(f"      Got: '{refined.text}' ({refined.refinement_applied})")

    return passed, len(TEST_CASES), failures


if __name__ == "__main__":
    start_time = time.time()

    print("=" * 60)
    print("BOUNDARY REFINEMENT - STANDALONE TESTS")
    print("=" * 60)
    print(f"\nEntity types with refinement: {list(REFINEMENT_FUNCTIONS.keys())}")
    print(f"Position-aware refinements: {list(POSITION_AWARE_REFINEMENTS.keys())}")
    print(f"\nRunning {len(TEST_CASES)} test cases...\n")

    passed, total, failures = run_tests()

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} passed ({100*passed/total:.1f}%)")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")

    elapsed = time.time() - start_time
    print(f"\nTiempo de ejecución: {elapsed:.3f}s")

    exit(0 if passed == total else 1)
