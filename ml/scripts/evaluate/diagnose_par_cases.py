#!/usr/bin/env python3
"""
Diagnose PAR (partial match) cases in adversarial tests.

Analyzes what the model detects vs what's expected to understand
boundary issues that cause partial matches.

Usage:
    python scripts/evaluate/diagnose_par_cases.py
"""

import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.inference.ner_predictor import NERPredictor


# Cases with PAR matches to diagnose
PAR_CASES = [
    {
        "id": "very_long_name",
        "text": "Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.",
        "expected": [
            {"text": "José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón", "type": "PERSON"}
        ],
    },
    {
        "id": "address_floor_door",
        "text": "Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.",
        "expected": [
            {"text": "Calle Mayor 15, 3º B", "type": "ADDRESS"},
            {"text": "28001", "type": "POSTAL_CODE"},
            {"text": "Madrid", "type": "LOCATION"},
        ],
    },
    {
        "id": "mixed_languages",
        "text": "Mr. John Smith, residente en Calle Alcalá 50, Madrid.",
        "expected": [
            {"text": "John Smith", "type": "PERSON"},
            {"text": "Calle Alcalá 50", "type": "ADDRESS"},
            {"text": "Madrid", "type": "LOCATION"},
        ],
    },
    {
        "id": "notarial_header",
        "text": "NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.",
        "expected": [
            {"text": "Sevilla", "type": "LOCATION"},
            {"text": "quince de marzo de dos mil veinticuatro", "type": "DATE"},
            {"text": "JOSÉ GARCÍA LÓPEZ", "type": "PERSON"},
            {"text": "Sevilla", "type": "LOCATION"},
        ],
    },
    {
        "id": "testament_comparecencia",
        "text": "COMPARECE: Don ANTONIO PÉREZ MARTÍNEZ, mayor de edad, casado, jubilado, vecino de Madrid, con domicilio en Calle Gran Vía 100, 5º A, y con DNI 12345678-Z. TESTIGO: Don CARLOS SÁNCHEZ GÓMEZ.",
        "expected": [
            {"text": "ANTONIO PÉREZ MARTÍNEZ", "type": "PERSON"},
            {"text": "Madrid", "type": "LOCATION"},
            {"text": "Calle Gran Vía 100, 5º A", "type": "ADDRESS"},
            {"text": "12345678-Z", "type": "DNI_NIE"},
            {"text": "CARLOS SÁNCHEZ GÓMEZ", "type": "PERSON"},
        ],
    },
    {
        "id": "contract_parties",
        "text": "De una parte, INMOBILIARIA GARCÍA, S.L., con CIF B-12345678, domiciliada en Plaza Mayor 1, 28013 Madrid, representada por D. PEDRO GARCÍA LÓPEZ. De otra parte, Dña. ANA MARTÍNEZ RUIZ, con NIF 87654321-X.",
        "expected": [
            {"text": "INMOBILIARIA GARCÍA, S.L.", "type": "ORGANIZATION"},
            {"text": "B-12345678", "type": "DNI_NIE"},
            {"text": "Plaza Mayor 1", "type": "ADDRESS"},
            {"text": "28013", "type": "POSTAL_CODE"},
            {"text": "Madrid", "type": "LOCATION"},
            {"text": "PEDRO GARCÍA LÓPEZ", "type": "PERSON"},
            {"text": "ANA MARTÍNEZ RUIZ", "type": "PERSON"},
            {"text": "87654321-X", "type": "DNI_NIE"},
        ],
    },
]


def analyze_boundaries(expected_text: str, detected_text: str) -> dict:
    """Analyze boundary differences between expected and detected."""
    exp_lower = expected_text.lower().strip()
    det_lower = detected_text.lower().strip()

    result = {
        "expected": expected_text,
        "detected": detected_text,
        "match_type": "none",
        "issue": None,
    }

    if exp_lower == det_lower:
        result["match_type"] = "exact"
    elif exp_lower in det_lower:
        result["match_type"] = "over_extended"
        result["issue"] = f"Detected includes extra: '{detected_text.replace(expected_text, '[EXPECTED]')}'"
    elif det_lower in exp_lower:
        result["match_type"] = "truncated"
        # Find what's missing
        idx = exp_lower.find(det_lower)
        before = expected_text[:idx] if idx > 0 else ""
        after = expected_text[idx + len(detected_text):] if idx + len(detected_text) < len(expected_text) else ""
        if before:
            result["issue"] = f"Missing at start: '{before}'"
        if after:
            result["issue"] = f"Missing at end: '{after}'"
    else:
        # Check overlap
        for i in range(len(exp_lower)):
            if exp_lower[i:] in det_lower or det_lower in exp_lower[i:]:
                result["match_type"] = "partial_overlap"
                break

    return result


def diagnose_case(predictor: NERPredictor, case: dict) -> dict:
    """Diagnose a single PAR case."""
    text = case["text"]
    expected = case["expected"]

    # Get predictions
    entities = predictor.predict(text, min_confidence=0.3)

    results = {
        "id": case["id"],
        "text": text,
        "expected_count": len(expected),
        "detected_count": len(entities),
        "matches": [],
        "unmatched_expected": [],
        "unmatched_detected": [],
    }

    # Match expected to detected
    matched_detected = set()

    for exp in expected:
        exp_text = exp["text"]
        exp_type = exp["type"]

        # Find best matching detection
        best_match = None
        best_overlap = 0

        for i, det in enumerate(entities):
            if i in matched_detected:
                continue
            if det.entity_type != exp_type:
                continue

            # Check overlap
            exp_lower = exp_text.lower()
            det_lower = det.text.lower()

            if exp_lower == det_lower:
                best_match = (i, det, "exact")
                break
            elif exp_lower in det_lower or det_lower in exp_lower:
                overlap = min(len(exp_lower), len(det_lower))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = (i, det, "partial")

        if best_match:
            i, det, match_type = best_match
            matched_detected.add(i)

            analysis = analyze_boundaries(exp_text, det.text)
            results["matches"].append({
                "expected": exp_text,
                "expected_type": exp_type,
                "detected": det.text,
                "detected_type": det.entity_type,
                "source": det.source,
                "match_type": analysis["match_type"],
                "issue": analysis["issue"],
            })
        else:
            results["unmatched_expected"].append(exp)

    # Unmatched detections
    for i, det in enumerate(entities):
        if i not in matched_detected:
            results["unmatched_detected"].append({
                "text": det.text,
                "type": det.entity_type,
                "source": det.source,
            })

    return results


def main():
    """Run PAR case diagnosis."""
    start_time = time.time()

    print("=" * 70)
    print("PAR CASE DIAGNOSIS - Boundary Analysis")
    print("=" * 70)

    # Load model
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MODEL_PATH = BASE_DIR / "models" / "legal_ner_v2"

    if not MODEL_PATH.exists():
        print(f"\n⚠️  Model not found at {MODEL_PATH}")
        return 1

    print("\nLoading NER model...")
    predictor = NERPredictor(MODEL_PATH)

    # Analyze each case
    boundary_issues = {
        "truncated": [],
        "over_extended": [],
        "partial_overlap": [],
    }

    for case in PAR_CASES:
        print("\n" + "=" * 70)
        print(f"Case: {case['id']}")
        print("=" * 70)
        print(f"Text: {case['text'][:80]}...")

        results = diagnose_case(predictor, case)

        print(f"\nExpected: {results['expected_count']} | Detected: {results['detected_count']}")

        print("\n--- Matches ---")
        for m in results["matches"]:
            status = "✅" if m["match_type"] == "exact" else "⚠️"
            print(f"  {status} [{m['expected_type']}]")
            print(f"     Expected: '{m['expected']}'")
            print(f"     Detected: '{m['detected']}' (source={m['source']})")
            if m["issue"]:
                print(f"     Issue:    {m['issue']}")
                if m["match_type"] in boundary_issues:
                    boundary_issues[m["match_type"]].append({
                        "case": case["id"],
                        "expected": m["expected"],
                        "detected": m["detected"],
                        "issue": m["issue"],
                    })

        if results["unmatched_expected"]:
            print("\n--- Missing (not detected) ---")
            for u in results["unmatched_expected"]:
                print(f"  ❌ [{u['type']}] '{u['text']}'")

        if results["unmatched_detected"]:
            print("\n--- Extra (false positives) ---")
            for u in results["unmatched_detected"]:
                print(f"  🔸 [{u['type']}] '{u['text']}' (source={u['source']})")

    # Summary
    print("\n" + "=" * 70)
    print("BOUNDARY ISSUE SUMMARY")
    print("=" * 70)

    for issue_type, issues in boundary_issues.items():
        if issues:
            print(f"\n{issue_type.upper()} ({len(issues)} cases):")
            for iss in issues:
                print(f"  - [{iss['case']}] {iss['issue']}")

    elapsed = time.time() - start_time
    print(f"\nTiempo de ejecución: {elapsed:.2f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
