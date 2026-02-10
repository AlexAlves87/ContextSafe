#!/usr/bin/env python3
"""
Adversarial evaluation for Spanish Legal NER model.

Tests the model against challenging cases that may not appear in synthetic training data:
- Edge cases (unusual formats, boundary conditions)
- Adversarial examples (designed to confuse)
- OCR corruption (simulated scanning errors)
- Unicode evasion (lookalike characters)
- Real-world patterns (legal document idioms)

Usage:
    python scripts/adversarial/evaluate_adversarial.py

Output:
    docs/reports/YYYY-MM-DD_adversarial_evaluation.md
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent.parent.parent
MODEL_DIR = BASE_DIR / "models" / "legal_ner_v2"  # Updated to v2 with noise training
OUTPUT_DIR = BASE_DIR / "docs" / "reports"


@dataclass
class TestCase:
    """A single adversarial test case."""

    category: str
    name: str
    text: str
    expected_entities: list[dict]  # [{"text": "...", "type": "PERSON"}, ...]
    difficulty: str  # "easy", "medium", "hard"
    notes: str = ""


@dataclass
class TestResult:
    """Result of running a test case."""

    test_case: TestCase
    detected_entities: list[dict]
    correct: int
    missed: int
    false_positives: int
    passed: bool


# =============================================================================
# ADVERSARIAL TEST CASES
# =============================================================================

ADVERSARIAL_TESTS = [
    # -------------------------------------------------------------------------
    # EDGE CASES - Boundary conditions and unusual formats
    # -------------------------------------------------------------------------
    TestCase(
        category="edge_case",
        name="single_letter_name",
        text="El demandante J. García presentó recurso.",
        expected_entities=[{"text": "J. García", "type": "PERSON"}],
        difficulty="medium",
        notes="Initial + surname pattern",
    ),
    TestCase(
        category="edge_case",
        name="very_long_name",
        text="Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.",
        expected_entities=[
            {
                "text": "José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón",
                "type": "PERSON",
            }
        ],
        difficulty="hard",
        notes="Compound noble name with particles",
    ),
    TestCase(
        category="edge_case",
        name="dni_without_letter",
        text="DNI número 12345678 (pendiente de verificación).",
        expected_entities=[{"text": "12345678", "type": "DNI_NIE"}],
        difficulty="medium",
        notes="DNI missing control letter",
    ),
    TestCase(
        category="edge_case",
        name="dni_with_spaces",
        text="Su documento de identidad es 12 345 678 Z.",
        expected_entities=[{"text": "12 345 678 Z", "type": "DNI_NIE"}],
        difficulty="hard",
        notes="DNI with internal spaces",
    ),
    TestCase(
        category="edge_case",
        name="iban_with_spaces",
        text="Transferir a ES91 2100 0418 4502 0005 1332.",
        expected_entities=[
            {"text": "ES91 2100 0418 4502 0005 1332", "type": "IBAN"}
        ],
        difficulty="easy",
        notes="Standard IBAN format with spaces",
    ),
    TestCase(
        category="edge_case",
        name="phone_international",
        text="Contacto: +34 612 345 678 o 0034612345678.",
        expected_entities=[
            {"text": "+34 612 345 678", "type": "PHONE"},
            {"text": "0034612345678", "type": "PHONE"},
        ],
        difficulty="medium",
        notes="International phone formats",
    ),
    TestCase(
        category="edge_case",
        name="date_roman_numerals",
        text="Otorgado el día XV de marzo del año MMXXIV.",
        expected_entities=[{"text": "XV de marzo del año MMXXIV", "type": "DATE"}],
        difficulty="hard",
        notes="Date with Roman numerals (notarial style)",
    ),
    TestCase(
        category="edge_case",
        name="date_ordinal",
        text="El primero de enero de dos mil veinticuatro.",
        expected_entities=[
            {"text": "primero de enero de dos mil veinticuatro", "type": "DATE"}
        ],
        difficulty="medium",
        notes="Fully written out date",
    ),
    TestCase(
        category="edge_case",
        name="address_floor_door",
        text="Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.",
        expected_entities=[
            {"text": "Calle Mayor 15, 3º B", "type": "ADDRESS"},
            {"text": "28001", "type": "POSTAL_CODE"},
            {"text": "Madrid", "type": "LOCATION"},
        ],
        difficulty="medium",
        notes="Address with floor and door",
    ),
    # -------------------------------------------------------------------------
    # ADVERSARIAL - Designed to confuse the model
    # -------------------------------------------------------------------------
    TestCase(
        category="adversarial",
        name="negation_dni",
        text="El interesado manifiesta NO tener DNI ni NIE.",
        expected_entities=[],
        difficulty="hard",
        notes="Should NOT detect PII - negation context",
    ),
    TestCase(
        category="adversarial",
        name="example_dni",
        text="El formato del DNI es 12345678X (ejemplo ilustrativo).",
        expected_entities=[],
        difficulty="hard",
        notes="Example/illustrative context should be ignored",
    ),
    TestCase(
        category="adversarial",
        name="fictional_person",
        text="Como dijo Don Quijote de la Mancha en su célebre obra.",
        expected_entities=[],
        difficulty="hard",
        notes="Fictional/literary character - not PII",
    ),
    TestCase(
        category="adversarial",
        name="organization_as_person",
        text="García y Asociados, S.L. interpone demanda.",
        expected_entities=[
            {"text": "García y Asociados, S.L.", "type": "ORGANIZATION"}
        ],
        difficulty="medium",
        notes="Surname in company name - should be ORG not PERSON",
    ),
    TestCase(
        category="adversarial",
        name="location_as_person",
        text="El municipio de San Fernando del Valle de Catamarca.",
        expected_entities=[
            {"text": "San Fernando del Valle de Catamarca", "type": "LOCATION"}
        ],
        difficulty="hard",
        notes="Location with person-like prefix (San)",
    ),
    TestCase(
        category="adversarial",
        name="date_in_reference",
        text="Según la Ley 15/2022, de 12 de julio, reguladora...",
        expected_entities=[],
        difficulty="hard",
        notes="Date in legal reference - not standalone PII",
    ),
    TestCase(
        category="adversarial",
        name="numbers_not_dni",
        text="El expediente 12345678 consta de 9 folios.",
        expected_entities=[],
        difficulty="medium",
        notes="8-digit number that is NOT a DNI (expediente)",
    ),
    TestCase(
        category="adversarial",
        name="mixed_languages",
        text="Mr. John Smith, con pasaporte UK123456789, residente en Madrid.",
        expected_entities=[
            {"text": "John Smith", "type": "PERSON"},
            {"text": "UK123456789", "type": "DNI_NIE"},  # Foreign ID
            {"text": "Madrid", "type": "LOCATION"},
        ],
        difficulty="hard",
        notes="English name and foreign passport",
    ),
    # -------------------------------------------------------------------------
    # OCR CORRUPTION - Simulated scanning errors
    # -------------------------------------------------------------------------
    TestCase(
        category="ocr_corruption",
        name="ocr_letter_substitution",
        text="DNl 12345678Z perteneciente a María García.",  # DNl with lowercase L
        expected_entities=[
            {"text": "12345678Z", "type": "DNI_NIE"},
            {"text": "María García", "type": "PERSON"},
        ],
        difficulty="medium",
        notes="OCR confused I with l",
    ),
    TestCase(
        category="ocr_corruption",
        name="ocr_zero_o_confusion",
        text="IBAN ES91 21O0 0418 45O2 OOO5 1332.",  # O instead of 0
        expected_entities=[
            {"text": "ES91 21O0 0418 45O2 OOO5 1332", "type": "IBAN"}
        ],
        difficulty="hard",
        notes="OCR confused 0 with O",
    ),
    TestCase(
        category="ocr_corruption",
        name="ocr_missing_spaces",
        text="DonJoséGarcíaLópezconDNI12345678X.",
        expected_entities=[
            {"text": "JoséGarcíaLópez", "type": "PERSON"},
            {"text": "12345678X", "type": "DNI_NIE"},
        ],
        difficulty="hard",
        notes="OCR lost all spaces",
    ),
    TestCase(
        category="ocr_corruption",
        name="ocr_extra_spaces",
        text="D N I  1 2 3 4 5 6 7 8 Z  de  M a r í a.",
        expected_entities=[
            {"text": "1 2 3 4 5 6 7 8 Z", "type": "DNI_NIE"},
            {"text": "M a r í a", "type": "PERSON"},
        ],
        difficulty="hard",
        notes="OCR added extra spaces",
    ),
    TestCase(
        category="ocr_corruption",
        name="ocr_accent_loss",
        text="Jose Maria Garcia Lopez, vecino de Malaga.",
        expected_entities=[
            {"text": "Jose Maria Garcia Lopez", "type": "PERSON"},
            {"text": "Malaga", "type": "LOCATION"},
        ],
        difficulty="easy",
        notes="OCR lost accents (common)",
    ),
    # -------------------------------------------------------------------------
    # UNICODE EVASION - Lookalike characters
    # -------------------------------------------------------------------------
    TestCase(
        category="unicode_evasion",
        name="cyrillic_o",
        text="DNI 12345678Х pertenece a María.",  # Cyrillic Х instead of X
        expected_entities=[
            {"text": "12345678Х", "type": "DNI_NIE"},
            {"text": "María", "type": "PERSON"},
        ],
        difficulty="hard",
        notes="Cyrillic Х (U+0425) instead of Latin X",
    ),
    TestCase(
        category="unicode_evasion",
        name="zero_width_space",
        text="DNI 123\u200b456\u200b78Z de María García.",  # Zero-width spaces
        expected_entities=[
            {"text": "12345678Z", "type": "DNI_NIE"},
            {"text": "María García", "type": "PERSON"},
        ],
        difficulty="hard",
        notes="Zero-width spaces inserted (U+200B)",
    ),
    TestCase(
        category="unicode_evasion",
        name="fullwidth_numbers",
        text="DNI １２３４５６７８Z de María.",  # Fullwidth digits
        expected_entities=[
            {"text": "１２３４５６７８Z", "type": "DNI_NIE"},
            {"text": "María", "type": "PERSON"},
        ],
        difficulty="hard",
        notes="Fullwidth digits (U+FF11-U+FF19)",
    ),
    # -------------------------------------------------------------------------
    # REAL-WORLD PATTERNS - Legal document idioms
    # -------------------------------------------------------------------------
    TestCase(
        category="real_world",
        name="notarial_header",
        text="NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.",
        expected_entities=[
            {"text": "Sevilla", "type": "LOCATION"},
            {"text": "quince de marzo de dos mil veinticuatro", "type": "DATE"},
            {"text": "JOSÉ GARCÍA LÓPEZ", "type": "PERSON"},
            {"text": "Sevilla", "type": "LOCATION"},
        ],
        difficulty="medium",
        notes="Standard notarial deed header",
    ),
    TestCase(
        category="real_world",
        name="testament_comparecencia",
        text="COMPARECE: Doña MARÍA ANTONIA FERNÁNDEZ RUIZ, mayor de edad, viuda, natural de Córdoba, vecina de Madrid, con domicilio en Calle Alcalá número 123, piso 4º, puerta B, y con D.N.I. número 12345678-Z.",
        expected_entities=[
            {"text": "MARÍA ANTONIA FERNÁNDEZ RUIZ", "type": "PERSON"},
            {"text": "Córdoba", "type": "LOCATION"},
            {"text": "Madrid", "type": "LOCATION"},
            {"text": "Calle Alcalá número 123, piso 4º, puerta B", "type": "ADDRESS"},
            {"text": "12345678-Z", "type": "DNI_NIE"},
        ],
        difficulty="hard",
        notes="Testament appearance clause",
    ),
    TestCase(
        category="real_world",
        name="judicial_sentence_header",
        text="SENTENCIA Nº 123/2024. En Madrid, a diez de enero de dos mil veinticuatro. Vistos por la Sala Primera del Tribunal Supremo los recursos interpuestos por D. ANTONIO PÉREZ MARTÍNEZ, representado por el Procurador D. CARLOS SÁNCHEZ GÓMEZ.",
        expected_entities=[
            {"text": "Madrid", "type": "LOCATION"},
            {"text": "diez de enero de dos mil veinticuatro", "type": "DATE"},
            {"text": "ANTONIO PÉREZ MARTÍNEZ", "type": "PERSON"},
            {"text": "CARLOS SÁNCHEZ GÓMEZ", "type": "PERSON"},
        ],
        difficulty="hard",
        notes="Supreme Court sentence header",
    ),
    TestCase(
        category="real_world",
        name="contract_parties",
        text="De una parte, INMOBILIARIA GARCÍA, S.L., con CIF B-12345678, domiciliada en Plaza Mayor 1, 28013 Madrid, representada por D. PEDRO GARCÍA LÓPEZ. De otra parte, Dña. ANA MARTÍNEZ RUIZ, con NIF 87654321-X.",
        expected_entities=[
            {"text": "INMOBILIARIA GARCÍA, S.L.", "type": "ORGANIZATION"},
            {"text": "B-12345678", "type": "DNI_NIE"},  # CIF
            {"text": "Plaza Mayor 1", "type": "ADDRESS"},
            {"text": "28013", "type": "POSTAL_CODE"},
            {"text": "Madrid", "type": "LOCATION"},
            {"text": "PEDRO GARCÍA LÓPEZ", "type": "PERSON"},
            {"text": "ANA MARTÍNEZ RUIZ", "type": "PERSON"},
            {"text": "87654321-X", "type": "DNI_NIE"},
        ],
        difficulty="hard",
        notes="Contract parties clause",
    ),
    TestCase(
        category="real_world",
        name="bank_account_clause",
        text="El pago se efectuará mediante transferencia a la cuenta IBAN ES12 0049 1234 5012 3456 7890 titularidad de CONSTRUCCIONES PÉREZ, S.A., con CIF A-98765432.",
        expected_entities=[
            {"text": "ES12 0049 1234 5012 3456 7890", "type": "IBAN"},
            {"text": "CONSTRUCCIONES PÉREZ, S.A.", "type": "ORGANIZATION"},
            {"text": "A-98765432", "type": "DNI_NIE"},  # CIF
        ],
        difficulty="medium",
        notes="Bank transfer clause",
    ),
    TestCase(
        category="real_world",
        name="cadastral_reference",
        text="Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.",
        expected_entities=[
            {"text": "Málaga", "type": "LOCATION"},
            {"text": "1234567AB1234S0001AB", "type": "CADASTRAL_REF"},
        ],
        difficulty="medium",
        notes="Property registration with cadastral reference",
    ),
    TestCase(
        category="real_world",
        name="professional_ids",
        text="Interviene el Abogado D. LUIS SÁNCHEZ, colegiado nº 12345 del ICAM, y el Procurador D. MIGUEL TORRES, colegiado nº 67890 del Colegio de Procuradores de Madrid.",
        expected_entities=[
            {"text": "LUIS SÁNCHEZ", "type": "PERSON"},
            {"text": "12345", "type": "PROFESSIONAL_ID"},
            {"text": "MIGUEL TORRES", "type": "PERSON"},
            {"text": "67890", "type": "PROFESSIONAL_ID"},
        ],
        difficulty="hard",
        notes="Professional bar numbers",
    ),
    TestCase(
        category="real_world",
        name="ecli_citation",
        text="Según doctrina del Tribunal Supremo (ECLI:ES:TS:2023:1234), confirmada en ECLI:ES:AN:2024:567.",
        expected_entities=[
            {"text": "ECLI:ES:TS:2023:1234", "type": "ECLI"},
            {"text": "ECLI:ES:AN:2024:567", "type": "ECLI"},
        ],
        difficulty="easy",
        notes="ECLI case citations",
    ),
    TestCase(
        category="real_world",
        name="vehicle_clause",
        text="El vehículo marca SEAT, modelo Ibiza, matrícula 1234 ABC, propiedad de D. FRANCISCO LÓPEZ.",
        expected_entities=[
            {"text": "1234 ABC", "type": "LICENSE_PLATE"},
            {"text": "FRANCISCO LÓPEZ", "type": "PERSON"},
        ],
        difficulty="medium",
        notes="Vehicle description clause",
    ),
    TestCase(
        category="real_world",
        name="social_security",
        text="Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.",
        expected_entities=[{"text": "281234567890", "type": "NSS"}],
        difficulty="easy",
        notes="Social security number in employment context",
    ),
]


# =============================================================================
# MODEL INFERENCE
# =============================================================================


class NERPredictor:
    """Wrapper for NER model inference."""

    def __init__(self, model_path: Path):
        print(f"Loading model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model = AutoModelForTokenClassification.from_pretrained(str(model_path))
        self.model.eval()

        # Load label mappings
        with open(model_path / "label_mappings.json") as f:
            mappings = json.load(f)
        self.id2label = {int(k): v for k, v in mappings["id2label"].items()}

        # Move to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"  Model loaded on {self.device}")

    def predict(self, text: str) -> list[dict]:
        """
        Predict entities in text.

        Returns list of {"text": ..., "type": ..., "start": ..., "end": ...}
        """
        # Tokenize
        encoding = self.tokenizer(
            text,
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=512,
        )

        offset_mapping = encoding.pop("offset_mapping")[0].tolist()
        encoding = {k: v.to(self.device) for k, v in encoding.items()}

        # Predict
        with torch.no_grad():
            outputs = self.model(**encoding)
            predictions = torch.argmax(outputs.logits, dim=2)[0].cpu().tolist()

        # Extract entities
        entities = []
        current_entity = None

        for i, (pred_id, (start, end)) in enumerate(zip(predictions, offset_mapping)):
            if start == end:  # Special token
                continue

            label = self.id2label[pred_id]

            if label.startswith("B-"):
                # Save previous entity
                if current_entity:
                    entities.append(current_entity)

                # Start new entity
                entity_type = label[2:]
                current_entity = {
                    "text": text[start:end],
                    "type": entity_type,
                    "start": start,
                    "end": end,
                }

            elif label.startswith("I-") and current_entity:
                entity_type = label[2:]
                if entity_type == current_entity["type"]:
                    # Continue entity
                    current_entity["text"] = text[
                        current_entity["start"] : end
                    ]
                    current_entity["end"] = end
                else:
                    # Type mismatch - save and start new
                    entities.append(current_entity)
                    current_entity = {
                        "text": text[start:end],
                        "type": entity_type,
                        "start": start,
                        "end": end,
                    }

            else:  # O label
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None

        # Don't forget last entity
        if current_entity:
            entities.append(current_entity)

        return entities


# =============================================================================
# EVALUATION
# =============================================================================


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, collapse spaces)."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    # Remove zero-width characters
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    return text


def entity_matches(detected: dict, expected: dict, fuzzy: bool = True) -> bool:
    """Check if detected entity matches expected."""
    # Type must match exactly
    if detected["type"] != expected["type"]:
        return False

    # Text comparison
    det_text = normalize_text(detected["text"])
    exp_text = normalize_text(expected["text"])

    if det_text == exp_text:
        return True

    if fuzzy:
        # Allow partial matches (detected contains expected or vice versa)
        if det_text in exp_text or exp_text in det_text:
            return True

        # Allow minor differences (1-2 chars)
        if abs(len(det_text) - len(exp_text)) <= 2:
            common = sum(1 for a, b in zip(det_text, exp_text) if a == b)
            if common / max(len(det_text), len(exp_text)) > 0.8:
                return True

    return False


def evaluate_test_case(predictor: NERPredictor, test: TestCase) -> TestResult:
    """Evaluate a single test case."""
    detected = predictor.predict(test.text)

    # Match detected to expected
    matched_expected = set()
    matched_detected = set()

    for i, exp in enumerate(test.expected_entities):
        for j, det in enumerate(detected):
            if j not in matched_detected and entity_matches(det, exp):
                matched_expected.add(i)
                matched_detected.add(j)
                break

    correct = len(matched_expected)
    missed = len(test.expected_entities) - correct
    false_positives = len(detected) - len(matched_detected)

    # Test passes if all expected found and no false positives (for hard tests)
    if test.difficulty == "hard":
        passed = correct == len(test.expected_entities) and false_positives == 0
    else:
        passed = correct == len(test.expected_entities)

    return TestResult(
        test_case=test,
        detected_entities=detected,
        correct=correct,
        missed=missed,
        false_positives=false_positives,
        passed=passed,
    )


def run_evaluation(predictor: NERPredictor) -> list[TestResult]:
    """Run all adversarial tests."""
    results = []

    for test in ADVERSARIAL_TESTS:
        result = evaluate_test_case(predictor, test)
        results.append(result)

        # Print progress
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {test.category}/{test.name}")

    return results


# =============================================================================
# REPORT GENERATION
# =============================================================================


def generate_report(results: list[TestResult]) -> str:
    """Generate markdown report."""
    now = datetime.now()

    # Calculate statistics
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    by_category = {}
    by_difficulty = {}

    for r in results:
        cat = r.test_case.category
        diff = r.test_case.difficulty

        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0}
        by_category[cat]["total"] += 1
        if r.passed:
            by_category[cat]["passed"] += 1

        if diff not in by_difficulty:
            by_difficulty[diff] = {"total": 0, "passed": 0}
        by_difficulty[diff]["total"] += 1
        if r.passed:
            by_difficulty[diff]["passed"] += 1

    # Build report
    report = f"""# Evaluación Adversarial - NER Legal Español

**Fecha:** {now.strftime('%Y-%m-%d %H:%M')}
**Modelo:** legal_ner_v2
**Tests:** {total}

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Tests totales | {total} |
| Pasados | {passed} ({passed/total*100:.1f}%) |
| Fallados | {failed} ({failed/total*100:.1f}%) |

### Por Categoría

| Categoría | Pasados | Total | Tasa |
|-----------|---------|-------|------|
"""

    for cat, stats in sorted(by_category.items()):
        rate = stats["passed"] / stats["total"] * 100
        report += f"| {cat} | {stats['passed']} | {stats['total']} | {rate:.1f}% |\n"

    report += """
### Por Dificultad

| Dificultad | Pasados | Total | Tasa |
|------------|---------|-------|------|
"""

    for diff in ["easy", "medium", "hard"]:
        if diff in by_difficulty:
            stats = by_difficulty[diff]
            rate = stats["passed"] / stats["total"] * 100
            report += f"| {diff} | {stats['passed']} | {stats['total']} | {rate:.1f}% |\n"

    report += """
---

## Resultados Detallados

"""

    # Group by category
    current_category = None
    for r in results:
        if r.test_case.category != current_category:
            current_category = r.test_case.category
            report += f"### {current_category.upper().replace('_', ' ')}\n\n"

        status = "PASS" if r.passed else "FAIL"
        report += f"#### {r.test_case.name} [{status}]\n\n"
        report += f"**Dificultad:** {r.test_case.difficulty}\n\n"
        report += f"**Texto:**\n```\n{r.test_case.text}\n```\n\n"

        report += f"**Esperado ({len(r.test_case.expected_entities)}):**\n"
        if r.test_case.expected_entities:
            for e in r.test_case.expected_entities:
                report += f"- `{e['text']}` → {e['type']}\n"
        else:
            report += "- (ninguna entidad)\n"

        report += f"\n**Detectado ({len(r.detected_entities)}):**\n"
        if r.detected_entities:
            for e in r.detected_entities:
                report += f"- `{e['text']}` → {e['type']}\n"
        else:
            report += "- (ninguna entidad)\n"

        report += f"\n**Resultado:** {r.correct} correctos, {r.missed} perdidos, {r.false_positives} falsos positivos\n"

        if r.test_case.notes:
            report += f"\n**Notas:** {r.test_case.notes}\n"

        report += "\n---\n\n"

    report += f"""
## Conclusiones

### Fortalezas del Modelo

(Analizar tests pasados y patrones)

### Debilidades Identificadas

(Analizar tests fallados y patrones)

### Recomendaciones

1. (Basadas en los resultados)

---

**Generado automáticamente por:** `scripts/adversarial/evaluate_adversarial.py`
"""

    return report


# =============================================================================
# MAIN
# =============================================================================


def main():
    print("=" * 60)
    print("ADVERSARIAL EVALUATION - SPANISH LEGAL NER")
    print("=" * 60)

    # Load model
    predictor = NERPredictor(MODEL_DIR)

    # Run tests
    print(f"\nRunning {len(ADVERSARIAL_TESTS)} adversarial tests...")
    results = run_evaluation(predictor)

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)

    # Generate report
    report = generate_report(results)

    # Save report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / f"{datetime.now().strftime('%Y-%m-%d_%H%M')}_adversarial_evaluation_v2.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")

    # Return exit code
    if passed / total < 0.7:
        print("\nWARNING: Less than 70% tests passed. Model needs improvement.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
