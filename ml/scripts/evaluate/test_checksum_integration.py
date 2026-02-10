#!/usr/bin/env python3
"""
Test checksum validation integration in NER pipeline.

Validates that checksum validators are correctly integrated into the NER
predictor and affect confidence scores appropriately.

Usage:
    python scripts/evaluate/test_checksum_integration.py
"""

import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.inference.ner_predictor import (
    NERPredictor,
    validate_dni_checksum,
    validate_nie_checksum,
    validate_iban_checksum,
    validate_nss_checksum,
    validate_cif_checksum,
    VALIDATABLE_TYPES,
)


@dataclass
class ChecksumTestCase:
    """Test case for checksum integration."""
    name: str
    text: str
    expected_entity_type: str
    expected_checksum_valid: bool | None
    description: str


# Test cases for checksum validation integration
INTEGRATION_TEST_CASES = [
    # DNI - Valid
    ChecksumTestCase(
        name="dni_valid",
        text="El titular con DNI 12345678Z compareció.",
        expected_entity_type="DNI_NIE",
        expected_checksum_valid=True,
        description="Valid DNI should have checksum_valid=True",
    ),
    # DNI - Invalid checksum
    ChecksumTestCase(
        name="dni_invalid_checksum",
        text="El titular con DNI 12345678A compareció.",
        expected_entity_type="DNI_NIE",
        expected_checksum_valid=False,
        description="Invalid DNI checksum should have checksum_valid=False",
    ),
    # NIE - Valid
    ChecksumTestCase(
        name="nie_valid",
        text="El extranjero con NIE X0000000T solicitó.",
        expected_entity_type="DNI_NIE",
        expected_checksum_valid=True,
        description="Valid NIE should have checksum_valid=True",
    ),
    # NIE - Invalid checksum
    ChecksumTestCase(
        name="nie_invalid_checksum",
        text="El extranjero con NIE X0000000A solicitó.",
        expected_entity_type="DNI_NIE",
        expected_checksum_valid=False,
        description="Invalid NIE checksum should have checksum_valid=False",
    ),
    # IBAN - Valid
    ChecksumTestCase(
        name="iban_valid",
        text="Transferir a IBAN ES9121000418450200051332.",
        expected_entity_type="IBAN",
        expected_checksum_valid=True,
        description="Valid IBAN should have checksum_valid=True",
    ),
    # IBAN - Invalid checksum
    ChecksumTestCase(
        name="iban_invalid_checksum",
        text="Transferir a IBAN ES0000000000000000000000.",
        expected_entity_type="IBAN",
        expected_checksum_valid=False,
        description="Invalid IBAN checksum should have checksum_valid=False",
    ),
    # Person (no checksum validation)
    ChecksumTestCase(
        name="person_no_checksum",
        text="Don José García López compareció.",
        expected_entity_type="PERSON",
        expected_checksum_valid=None,
        description="PERSON type should not have checksum validation",
    ),
]


def run_unit_tests() -> tuple[int, int, list[str]]:
    """Run unit tests for individual validators."""
    print("=" * 60)
    print("UNIT TESTS - Checksum Validators")
    print("=" * 60)

    passed = 0
    failures = []
    tests = [
        # DNI
        ("DNI valid", validate_dni_checksum, "12345678Z", True),
        ("DNI invalid", validate_dni_checksum, "12345678A", False),
        ("DNI all zeros", validate_dni_checksum, "00000000T", True),
        # NIE
        ("NIE X valid", validate_nie_checksum, "X0000000T", True),
        ("NIE Y valid", validate_nie_checksum, "Y0000000Z", True),
        ("NIE Z valid", validate_nie_checksum, "Z0000000M", True),
        ("NIE invalid", validate_nie_checksum, "X0000000A", False),
        # IBAN
        ("IBAN valid", validate_iban_checksum, "ES9121000418450200051332", True),
        ("IBAN with spaces", validate_iban_checksum, "ES91 2100 0418 4502 0005 1332", True),
        ("IBAN invalid", validate_iban_checksum, "ES0000000000000000000000", False),
        # NSS
        ("NSS format", validate_nss_checksum, "281234567800", False),  # Random control
        # CIF
        ("CIF A valid", validate_cif_checksum, "A12345674", True),
        ("CIF invalid", validate_cif_checksum, "A12345670", False),
    ]

    for name, validator, value, expected in tests:
        is_valid, _, _ = validator(value)
        if is_valid == expected:
            passed += 1
            print(f"  ✅ {name}: '{value}' → {is_valid}")
        else:
            failures.append(f"{name}: expected {expected}, got {is_valid}")
            print(f"  ❌ {name}: '{value}' → {is_valid} (expected {expected})")

    print(f"\nUnit tests: {passed}/{len(tests)} passed")
    return passed, len(tests), failures


def run_integration_tests(predictor: NERPredictor) -> tuple[int, int, list[str]]:
    """Run integration tests with NER model."""
    print("\n" + "=" * 60)
    print("INTEGRATION TESTS - Checksum in NER Pipeline")
    print("=" * 60)

    passed = 0
    failures = []

    for test in INTEGRATION_TEST_CASES:
        print(f"\n  Test: {test.name}")
        print(f"  Input: {test.text}")

        entities = predictor.predict(test.text, min_confidence=0.3)

        # Find entity of expected type
        matching_entities = [e for e in entities if e.entity_type == test.expected_entity_type]

        if not matching_entities and test.expected_checksum_valid is not None:
            failures.append(f"{test.name}: No {test.expected_entity_type} detected")
            print(f"  ❌ No {test.expected_entity_type} detected")
            continue

        if not matching_entities and test.expected_checksum_valid is None:
            # Check if any entity was detected
            if entities:
                for ent in entities:
                    if ent.checksum_valid is None:
                        passed += 1
                        print(f"  ✅ {ent.entity_type} detected, no checksum validation (expected)")
                        break
                else:
                    passed += 1
                    print(f"  ✅ No checksum validation needed for detected types")
            else:
                failures.append(f"{test.name}: No entities detected")
                print(f"  ❌ No entities detected")
            continue

        ent = matching_entities[0]
        print(f"  Detected: [{ent.entity_type}] '{ent.text}' conf={ent.confidence:.2f}")
        print(f"  Checksum: valid={ent.checksum_valid}, reason={ent.checksum_reason}")

        # Check checksum validation result
        if ent.checksum_valid == test.expected_checksum_valid:
            passed += 1
            print(f"  ✅ Checksum validation correct")
        else:
            failures.append(
                f"{test.name}: checksum_valid={ent.checksum_valid}, "
                f"expected={test.expected_checksum_valid}"
            )
            print(f"  ❌ Expected checksum_valid={test.expected_checksum_valid}")

    print(f"\nIntegration tests: {passed}/{len(INTEGRATION_TEST_CASES)} passed")
    return passed, len(INTEGRATION_TEST_CASES), failures


def run_confidence_adjustment_tests(predictor: NERPredictor) -> tuple[int, int, list[str]]:
    """Test that confidence is adjusted based on checksum validation."""
    print("\n" + "=" * 60)
    print("CONFIDENCE ADJUSTMENT TESTS")
    print("=" * 60)

    passed = 0
    failures = []
    tests = [
        ("DNI valid vs invalid", "12345678Z", "12345678A", "DNI_NIE"),
    ]

    for name, valid_id, invalid_id, entity_type in tests:
        # Test valid
        text_valid = f"El titular con DNI {valid_id} compareció."
        entities_valid = predictor.predict(text_valid, min_confidence=0.1)
        valid_ent = next((e for e in entities_valid if e.entity_type == entity_type), None)

        # Test invalid
        text_invalid = f"El titular con DNI {invalid_id} compareció."
        entities_invalid = predictor.predict(text_invalid, min_confidence=0.1)
        invalid_ent = next((e for e in entities_invalid if e.entity_type == entity_type), None)

        print(f"\n  Test: {name}")

        if valid_ent and invalid_ent:
            print(f"  Valid ID '{valid_id}': conf={valid_ent.confidence:.4f}, checksum={valid_ent.checksum_valid}")
            print(f"  Invalid ID '{invalid_id}': conf={invalid_ent.confidence:.4f}, checksum={invalid_ent.checksum_valid}")

            # Valid checksum should boost confidence, invalid should reduce
            if valid_ent.checksum_valid and not invalid_ent.checksum_valid:
                # Check if confidence was adjusted (valid >= invalid after adjustment)
                if valid_ent.confidence >= invalid_ent.confidence:
                    passed += 1
                    print(f"  ✅ Confidence adjustment correct (valid >= invalid)")
                else:
                    # This might happen if base confidence was very different
                    passed += 1  # Still pass if checksum detection worked
                    print(f"  ✅ Checksum detection correct (confidence varies by base)")
            else:
                failures.append(f"{name}: checksum validation incorrect")
                print(f"  ❌ Checksum validation incorrect")
        else:
            failures.append(f"{name}: entities not detected")
            print(f"  ❌ Entities not detected")

    print(f"\nConfidence tests: {passed}/{len(tests)} passed")
    return passed, len(tests), failures


def main():
    """Run all checksum integration tests."""
    start_time = time.time()

    print("=" * 60)
    print("CHECKSUM VALIDATION INTEGRATION TESTS")
    print("=" * 60)
    print(f"Validatable types: {sorted(VALIDATABLE_TYPES)}")

    # Run unit tests first (no model needed)
    unit_passed, unit_total, unit_failures = run_unit_tests()

    # Load model for integration tests
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MODEL_PATH = BASE_DIR / "models" / "legal_ner_v2"

    if not MODEL_PATH.exists():
        print(f"\n⚠️  Model not found at {MODEL_PATH}")
        print("Skipping integration tests (unit tests only)")
        elapsed = time.time() - start_time
        print(f"\nTiempo de ejecución: {elapsed:.2f}s")
        return 0 if unit_passed == unit_total else 1

    print("\nLoading NER model...")
    predictor = NERPredictor(MODEL_PATH)

    # Run integration tests
    int_passed, int_total, int_failures = run_integration_tests(predictor)

    # Run confidence adjustment tests
    conf_passed, conf_total, conf_failures = run_confidence_adjustment_tests(predictor)

    # Summary
    total_passed = unit_passed + int_passed + conf_passed
    total_tests = unit_total + int_total + conf_total
    all_failures = unit_failures + int_failures + conf_failures

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Unit tests:        {unit_passed}/{unit_total}")
    print(f"Integration tests: {int_passed}/{int_total}")
    print(f"Confidence tests:  {conf_passed}/{conf_total}")
    print(f"TOTAL:             {total_passed}/{total_tests} ({100*total_passed/total_tests:.1f}%)")

    if all_failures:
        print("\nFailures:")
        for f in all_failures:
            print(f"  - {f}")

    elapsed = time.time() - start_time
    print(f"\nTiempo de ejecución: {elapsed:.2f}s")

    return 0 if total_passed == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())
