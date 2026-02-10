#!/usr/bin/env python3
"""
Checksum validators for Spanish legal identifiers.

Validates:
- DNI (Documento Nacional de Identidad): 8 digits + control letter
- NIE (Número de Identidad de Extranjero): X/Y/Z + 7 digits + control letter
- IBAN (International Bank Account Number): ES + 22 digits, mod 97
- NSS (Número de Seguridad Social): 12 digits, mod 97 control
- CIF (Código de Identificación Fiscal): Letter + 7 digits + control

Based on: docs/reports/2026-02-03_1800_investigacion_hybrid_ner.md

Usage:
    python scripts/preprocess/checksum_validators.py

This script runs standalone tests. For integration, import validators.
"""

import re
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional


# =============================================================================
# DNI VALIDATOR
# =============================================================================

# Control letter sequence for DNI/NIE (mod 23)
DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

# NIE prefix to number mapping
NIE_PREFIX_MAP = {'X': '0', 'Y': '1', 'Z': '2'}


def validate_dni(dni: str) -> Tuple[bool, float, str]:
    """
    Validate Spanish DNI (Documento Nacional de Identidad).

    Format: 8 digits + 1 control letter
    Algorithm: letter = LETTERS[number % 23]

    Args:
        dni: DNI string to validate

    Returns:
        Tuple of (is_valid, confidence, reason)
        - is_valid: True if checksum is correct
        - confidence: 1.0 if valid, 0.5 if format ok but checksum wrong
        - reason: Description of validation result
    """
    # Clean input
    clean = dni.replace(' ', '').replace('-', '').replace('.', '').upper()

    # Check format: 8 digits + 1 letter
    match = re.match(r'^(\d{8})([A-Z])$', clean)
    if not match:
        return False, 0.0, "Invalid format (expected 8 digits + letter)"

    number, letter = match.groups()

    # Calculate expected letter
    expected = DNI_LETTERS[int(number) % 23]

    if letter == expected:
        return True, 1.0, "Valid DNI checksum"
    else:
        return False, 0.5, f"Invalid checksum: expected '{expected}', got '{letter}'"


def validate_nie(nie: str) -> Tuple[bool, float, str]:
    """
    Validate Spanish NIE (Número de Identidad de Extranjero).

    Format: X/Y/Z + 7 digits + 1 control letter
    Algorithm: Convert prefix to digit (X=0, Y=1, Z=2), then same as DNI

    Args:
        nie: NIE string to validate

    Returns:
        Tuple of (is_valid, confidence, reason)
    """
    # Clean input
    clean = nie.replace(' ', '').replace('-', '').replace('.', '').upper()

    # Check format: X/Y/Z + 7 digits + 1 letter
    match = re.match(r'^([XYZ])(\d{7})([A-Z])$', clean)
    if not match:
        return False, 0.0, "Invalid format (expected X/Y/Z + 7 digits + letter)"

    prefix, number, letter = match.groups()

    # Convert to full number
    full_number = NIE_PREFIX_MAP[prefix] + number

    # Calculate expected letter
    expected = DNI_LETTERS[int(full_number) % 23]

    if letter == expected:
        return True, 1.0, "Valid NIE checksum"
    else:
        return False, 0.5, f"Invalid checksum: expected '{expected}', got '{letter}'"


def validate_dni_or_nie(identifier: str) -> Tuple[bool, float, str]:
    """
    Validate either DNI or NIE.

    Args:
        identifier: DNI or NIE string to validate

    Returns:
        Tuple of (is_valid, confidence, reason)
    """
    clean = identifier.replace(' ', '').replace('-', '').replace('.', '').upper()

    # Determine type
    if clean and clean[0] in 'XYZ':
        return validate_nie(identifier)
    else:
        return validate_dni(identifier)


# =============================================================================
# IBAN VALIDATOR
# =============================================================================

def validate_iban(iban: str) -> Tuple[bool, float, str]:
    """
    Validate IBAN using ISO 13616 mod 97 algorithm.

    Spanish IBAN format: ES + 2 check digits + 20 account digits

    Algorithm:
    1. Move first 4 chars to end
    2. Convert letters to numbers (A=10, B=11, ...)
    3. Number mod 97 must equal 1

    Args:
        iban: IBAN string to validate

    Returns:
        Tuple of (is_valid, confidence, reason)
    """
    # Clean input
    clean = iban.replace(' ', '').replace('-', '').upper()

    # Check basic format
    if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', clean):
        return False, 0.0, "Invalid IBAN format"

    # Spanish IBAN should be 24 chars
    if clean.startswith('ES') and len(clean) != 24:
        return False, 0.3, f"Spanish IBAN should be 24 chars, got {len(clean)}"

    # Rearrange: move first 4 chars to end
    rearranged = clean[4:] + clean[:4]

    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric = ''
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - 55)  # A=65, so A-55=10
        else:
            numeric += char

    # Mod 97 check
    try:
        remainder = int(numeric) % 97
        if remainder == 1:
            return True, 1.0, "Valid IBAN checksum"
        else:
            return False, 0.4, f"Invalid checksum: mod 97 = {remainder}, expected 1"
    except ValueError:
        return False, 0.0, "Invalid characters in IBAN"


# =============================================================================
# NSS VALIDATOR (Número de Seguridad Social)
# =============================================================================

def validate_nss(nss: str) -> Tuple[bool, float, str]:
    """
    Validate Spanish NSS (Número de Seguridad Social).

    Format: 12 digits (PPNNNNNNNNCC)
    - PP: Province code (01-52)
    - NNNNNNNN: Sequential number
    - CC: Control digits = (PP * 10^10 + NNNNNNNN) mod 97

    Args:
        nss: NSS string to validate

    Returns:
        Tuple of (is_valid, confidence, reason)
    """
    # Clean input
    clean = nss.replace(' ', '').replace('-', '').replace('/', '')

    # Check format: exactly 12 digits
    if not re.match(r'^\d{12}$', clean):
        return False, 0.0, "Invalid format (expected 12 digits)"

    # Extract parts
    province = clean[:2]
    number = clean[2:10]
    control = clean[10:12]

    # Validate province (01-52, plus special codes)
    province_num = int(province)
    if province_num < 1 or province_num > 52:
        # Some special provinces exist, be lenient
        pass

    # Calculate expected control
    base = int(province + number)
    expected_control = base % 97

    actual_control = int(control)

    if actual_control == expected_control:
        return True, 1.0, "Valid NSS checksum"
    else:
        return False, 0.5, f"Invalid checksum: expected {expected_control:02d}, got {control}"


# =============================================================================
# CIF VALIDATOR (Código de Identificación Fiscal)
# =============================================================================

def validate_cif(cif: str) -> Tuple[bool, float, str]:
    """
    Validate Spanish CIF (Código de Identificación Fiscal).

    Format: Letter + 7 digits + control (digit or letter)
    First letter indicates organization type.

    Algorithm: Sum even positions, sum odd positions with special rule,
    control = (10 - (sum mod 10)) mod 10

    Args:
        cif: CIF string to validate

    Returns:
        Tuple of (is_valid, confidence, reason)
    """
    # Clean input
    clean = cif.replace(' ', '').replace('-', '').replace('.', '').upper()

    # Check format
    match = re.match(r'^([A-HJ-NP-SUVW])(\d{7})([0-9A-J])$', clean)
    if not match:
        return False, 0.0, "Invalid CIF format"

    org_type, digits, control = match.groups()

    # Calculate checksum
    # Sum of even positions (2nd, 4th, 6th)
    even_sum = sum(int(digits[i]) for i in [1, 3, 5])

    # Sum of odd positions with doubling rule
    odd_sum = 0
    for i in [0, 2, 4, 6]:
        doubled = int(digits[i]) * 2
        odd_sum += doubled // 10 + doubled % 10

    total = even_sum + odd_sum
    control_digit = (10 - (total % 10)) % 10

    # Control can be digit or letter depending on org type
    # Types that use letter: K, P, Q, S (and some N, R, W)
    letter_types = {'K', 'P', 'Q', 'S'}
    digit_types = {'A', 'B', 'E', 'H'}

    control_letter = chr(ord('A') + control_digit) if control_digit < 10 else 'J'

    if org_type in letter_types:
        # Must be letter
        if control == control_letter:
            return True, 1.0, "Valid CIF checksum (letter)"
        else:
            return False, 0.5, f"Invalid checksum: expected '{control_letter}', got '{control}'"
    elif org_type in digit_types:
        # Must be digit
        if control == str(control_digit):
            return True, 1.0, "Valid CIF checksum (digit)"
        else:
            return False, 0.5, f"Invalid checksum: expected '{control_digit}', got '{control}'"
    else:
        # Can be either
        if control == str(control_digit) or control == control_letter:
            return True, 1.0, "Valid CIF checksum"
        else:
            return False, 0.5, f"Invalid checksum: expected '{control_digit}' or '{control_letter}', got '{control}'"


# =============================================================================
# UNIFIED VALIDATOR
# =============================================================================

def validate_identifier(identifier: str, expected_type: str) -> Tuple[bool, float, str]:
    """
    Validate any Spanish identifier based on expected type.

    Args:
        identifier: The identifier string
        expected_type: One of 'DNI_NIE', 'IBAN', 'NSS', 'CIF'

    Returns:
        Tuple of (is_valid, confidence, reason)
    """
    validators = {
        'DNI_NIE': validate_dni_or_nie,
        'DNI': validate_dni,
        'NIE': validate_nie,
        'IBAN': validate_iban,
        'NSS': validate_nss,
        'CIF': validate_cif,
    }

    validator = validators.get(expected_type.upper())
    if not validator:
        return True, 1.0, f"No validator for type {expected_type}"

    return validator(identifier)


# =============================================================================
# STANDALONE TESTS
# =============================================================================

@dataclass
class TestCase:
    """Test case for validator."""
    name: str
    input: str
    validator: str
    expected_valid: bool
    description: str


# Real valid identifiers for testing (anonymized examples)
TEST_CASES: List[TestCase] = [
    # DNI - Valid
    TestCase("dni_valid_1", "12345678Z", "DNI", True, "Valid DNI with correct letter"),
    TestCase("dni_valid_2", "00000000T", "DNI", True, "Valid DNI (all zeros)"),
    TestCase("dni_valid_spaces", "1234 5678 Z", "DNI", True, "Valid DNI with spaces"),

    # DNI - Invalid checksum
    TestCase("dni_invalid_letter", "12345678A", "DNI", False, "Invalid letter (should be Z)"),
    TestCase("dni_invalid_letter_2", "00000000A", "DNI", False, "Invalid letter (should be T)"),

    # DNI - Invalid format
    TestCase("dni_invalid_format", "1234567Z", "DNI", False, "Only 7 digits"),
    TestCase("dni_invalid_format_2", "123456789Z", "DNI", False, "9 digits"),

    # NIE - Valid
    TestCase("nie_valid_x", "X0000000T", "NIE", True, "Valid NIE starting with X"),
    TestCase("nie_valid_y", "Y0000000Z", "NIE", True, "Valid NIE starting with Y"),
    TestCase("nie_valid_z", "Z0000000M", "NIE", True, "Valid NIE starting with Z"),

    # NIE - Invalid
    TestCase("nie_invalid_letter", "X0000000A", "NIE", False, "Invalid control letter"),

    # DNI_NIE combined
    TestCase("dni_nie_dni", "12345678Z", "DNI_NIE", True, "DNI detected correctly"),
    TestCase("dni_nie_nie", "X0000000T", "DNI_NIE", True, "NIE detected correctly"),

    # IBAN - Valid (test IBAN, not real)
    TestCase("iban_valid_es", "ES9121000418450200051332", "IBAN", True, "Valid Spanish IBAN"),
    TestCase("iban_valid_spaces", "ES91 2100 0418 4502 0005 1332", "IBAN", True, "Valid IBAN with spaces"),

    # IBAN - Invalid
    TestCase("iban_invalid_check", "ES0021000418450200051332", "IBAN", False, "Invalid check digits (00)"),
    TestCase("iban_invalid_mod97", "ES1234567890123456789012", "IBAN", False, "Fails mod 97"),

    # NSS - Valid
    TestCase("nss_valid", "281234567890", "NSS", False, "NSS with likely invalid control"),  # Most random NSS are invalid
    TestCase("nss_format_ok", "280000000097", "NSS", True, "NSS with valid control (97 mod 97 = 0... edge case)"),

    # CIF - Valid
    TestCase("cif_valid_a", "A12345674", "CIF", True, "Valid CIF type A"),
    TestCase("cif_valid_b", "B12345674", "CIF", True, "Valid CIF type B"),

    # CIF - Invalid
    TestCase("cif_invalid", "A12345670", "CIF", False, "Invalid CIF control digit"),

    # Edge cases
    TestCase("empty", "", "DNI", False, "Empty string"),
    TestCase("garbage", "XXXX1234", "DNI", False, "Garbage input"),
]


def run_tests() -> Tuple[int, int, List[str]]:
    """Run all test cases."""
    passed = 0
    failures = []

    for test in TEST_CASES:
        is_valid, confidence, reason = validate_identifier(test.input, test.validator)

        if is_valid == test.expected_valid:
            passed += 1
            status = "✅"
        else:
            failures.append(f"{test.name}: expected valid={test.expected_valid}, got valid={is_valid} ({reason})")
            status = "❌"

        print(f"  {status} {test.name}: {test.description}")
        if not is_valid == test.expected_valid:
            print(f"      Input: '{test.input}' | Reason: {reason}")

    return passed, len(TEST_CASES), failures


def demo_validation():
    """Demo validation with examples."""
    print("\n" + "=" * 60)
    print("VALIDATION DEMO")
    print("=" * 60)

    examples = [
        ("12345678Z", "DNI_NIE"),
        ("12345678A", "DNI_NIE"),  # Invalid
        ("X0000000T", "DNI_NIE"),
        ("ES91 2100 0418 4502 0005 1332", "IBAN"),
        ("ES00 0000 0000 0000 0000 0000", "IBAN"),  # Invalid
        ("A12345674", "CIF"),
        ("B98765432", "CIF"),  # Likely invalid
    ]

    for identifier, id_type in examples:
        is_valid, confidence, reason = validate_identifier(identifier, id_type)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"\n  {id_type}: '{identifier}'")
        print(f"    {status} (confidence: {confidence:.1f})")
        print(f"    Reason: {reason}")


if __name__ == "__main__":
    start_time = time.time()

    print("=" * 60)
    print("CHECKSUM VALIDATORS - STANDALONE TESTS")
    print("=" * 60)
    print(f"\nRunning {len(TEST_CASES)} test cases...\n")

    passed, total, failures = run_tests()

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} passed ({100*passed/total:.1f}%)")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")

    demo_validation()

    elapsed = time.time() - start_time
    print(f"\nTiempo de ejecución: {elapsed:.3f}s")

    exit(0 if passed == total else 1)
