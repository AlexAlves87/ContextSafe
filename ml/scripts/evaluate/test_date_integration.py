#!/usr/bin/env python3
"""
Test date pattern integration in NER pipeline.

Validates that date patterns correctly complement NER for detecting
textual dates that transformer models miss.

Usage:
    python scripts/evaluate/test_date_integration.py
"""

import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "preprocess"))

from scripts.inference.ner_predictor import NERPredictor, REGEX_AVAILABLE


@dataclass
class DateIntegrationTestCase:
    """Test case for date integration."""
    name: str
    text: str
    expected_date: str | None
    description: str


# Test cases focusing on date formats from adversarial tests
INTEGRATION_TEST_CASES = [
    # Roman numerals (from adversarial test)
    DateIntegrationTestCase(
        name="roman_full",
        text="Otorgado el día XV de marzo del año MMXXIV.",
        expected_date="XV de marzo del año MMXXIV",
        description="Roman day + month + Roman year",
    ),
    # Ordinal dates (from adversarial test)
    DateIntegrationTestCase(
        name="ordinal_full",
        text="El primero de enero de dos mil veinticuatro.",
        expected_date="primero de enero de dos mil veinticuatro",
        description="Ordinal day (primero)",
    ),
    # Notarial header date (from adversarial test)
    DateIntegrationTestCase(
        name="notarial_date",
        text="En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí.",
        expected_date="quince de marzo de dos mil veinticuatro",
        description="Notarial deed date",
    ),
    # Testament date (from adversarial test)
    DateIntegrationTestCase(
        name="testament_date",
        text="En Madrid, a diez de enero de dos mil veinticuatro, comparece.",
        expected_date="diez de enero de dos mil veinticuatro",
        description="Testament comparecencia date",
    ),
    # Written out full date
    DateIntegrationTestCase(
        name="written_full",
        text="El veintiocho de febrero de dos mil veinticinco se firmó.",
        expected_date="veintiocho de febrero de dos mil veinticinco",
        description="Written day 28 + month + year",
    ),
    # Numeric standard (NER should handle)
    DateIntegrationTestCase(
        name="numeric_standard",
        text="Firmado el 15 de marzo de 2024 en Madrid.",
        expected_date="15 de marzo de 2024",
        description="Standard numeric date",
    ),
    # Multiple dates
    DateIntegrationTestCase(
        name="multiple_dates",
        text="Desde uno de enero hasta treinta y uno de diciembre de dos mil veinticuatro.",
        expected_date="uno de enero",  # At least one
        description="Multiple textual dates",
    ),
]


def run_integration_tests(predictor: NERPredictor) -> tuple[int, int, list[str]]:
    """Run integration tests with NER model + date patterns."""
    print("=" * 60)
    print("DATE INTEGRATION TESTS")
    print("=" * 60)
    print(f"Regex available: {REGEX_AVAILABLE}")

    passed = 0
    failures = []

    for test in INTEGRATION_TEST_CASES:
        print(f"\n  Test: {test.name}")
        print(f"  Input: {test.text[:60]}...")

        entities = predictor.predict(test.text, min_confidence=0.3)

        # Find DATE entities
        date_entities = [e for e in entities if e.entity_type == "DATE"]

        if test.expected_date is None:
            if not date_entities:
                passed += 1
                print(f"  ✅ Correctly no date detected")
            else:
                failures.append(f"{test.name}: should not detect, got {[e.text for e in date_entities]}")
                print(f"  ❌ Should not detect")
        else:
            # Check if expected date is found (partial match ok)
            found = any(
                test.expected_date.lower() in e.text.lower() or
                e.text.lower() in test.expected_date.lower()
                for e in date_entities
            )

            if found:
                passed += 1
                detected = date_entities[0]
                print(f"  ✅ Detected: '{detected.text}' (source={detected.source})")
            else:
                failures.append(
                    f"{test.name}: expected '{test.expected_date}', "
                    f"got {[e.text for e in date_entities] if date_entities else 'nothing'}"
                )
                print(f"  ❌ Expected: '{test.expected_date}'")
                print(f"      Got: {[e.text for e in date_entities] if date_entities else 'nothing'}")
                # Show all entities for debugging
                if entities:
                    print(f"      All entities: {[(e.entity_type, e.text[:30]) for e in entities]}")

    print(f"\nIntegration tests: {passed}/{len(INTEGRATION_TEST_CASES)} passed")
    return passed, len(INTEGRATION_TEST_CASES), failures


def run_adversarial_date_tests(predictor: NERPredictor) -> tuple[int, int, list[str]]:
    """Run the specific adversarial tests that involve dates."""
    print("\n" + "=" * 60)
    print("ADVERSARIAL DATE TESTS (from test suite)")
    print("=" * 60)

    passed = 0
    failures = []

    # These are the exact tests from the adversarial suite
    adversarial_cases = [
        {
            "id": "date_roman_numerals",
            "text": "Otorgado el día XV de marzo del año MMXXIV.",
            "expected": [{"text": "XV de marzo del año MMXXIV", "type": "DATE"}],
        },
        {
            "id": "date_ordinal",
            "text": "El primero de enero de dos mil veinticuatro.",
            "expected": [{"text": "primero de enero de dos mil veinticuatro", "type": "DATE"}],
        },
    ]

    for test in adversarial_cases:
        print(f"\n  Test: {test['id']}")
        print(f"  Input: {test['text']}")

        entities = predictor.predict(test["text"], min_confidence=0.3)
        expected = test["expected"]

        # Check each expected entity
        all_found = True
        for exp in expected:
            exp_text = exp["text"].lower()
            exp_type = exp["type"]

            found = any(
                e.entity_type == exp_type and (
                    exp_text in e.text.lower() or e.text.lower() in exp_text
                )
                for e in entities
            )

            if not found:
                all_found = False
                break

        if all_found:
            passed += 1
            print(f"  ✅ All expected entities found")
            for e in entities:
                if e.entity_type == "DATE":
                    print(f"      [DATE] '{e.text}' (source={e.source})")
        else:
            failures.append(f"{test['id']}: missing expected entities")
            print(f"  ❌ Missing expected entities")
            print(f"      Expected: {expected}")
            print(f"      Got: {[(e.entity_type, e.text) for e in entities]}")

    print(f"\nAdversarial date tests: {passed}/{len(adversarial_cases)} passed")
    return passed, len(adversarial_cases), failures


def main():
    """Run all date integration tests."""
    start_time = time.time()

    print("=" * 60)
    print("DATE PATTERN INTEGRATION TESTS")
    print("=" * 60)

    # Load model
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MODEL_PATH = BASE_DIR / "models" / "legal_ner_v2"

    if not MODEL_PATH.exists():
        print(f"\n⚠️  Model not found at {MODEL_PATH}")
        return 1

    print("\nLoading NER model...")
    predictor = NERPredictor(MODEL_PATH)

    # Run tests
    int_passed, int_total, int_failures = run_integration_tests(predictor)
    adv_passed, adv_total, adv_failures = run_adversarial_date_tests(predictor)

    # Summary
    total_passed = int_passed + adv_passed
    total_tests = int_total + adv_total
    all_failures = int_failures + adv_failures

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Integration tests:   {int_passed}/{int_total}")
    print(f"Adversarial tests:   {adv_passed}/{adv_total}")
    print(f"TOTAL:               {total_passed}/{total_tests} ({100*total_passed/total_tests:.1f}%)")

    if all_failures:
        print("\nFailures:")
        for f in all_failures:
            print(f"  - {f}")

    elapsed = time.time() - start_time
    print(f"\nTiempo de ejecución: {elapsed:.2f}s")

    return 0 if total_passed == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())
