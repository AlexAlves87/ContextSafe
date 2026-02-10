#!/usr/bin/env python3
"""
Adversarial evaluation for NER Predictor.

Runs 35 adversarial tests against the NER model and generates a report.
Tests are grouped by category: edge_case, adversarial, ocr_corruption,
unicode_evasion, real_world.

Based on best practices from:
- NoiseBench (ICLR 2024): Real noise vs simulated noise
- seqeval: Entity-level evaluation metrics
- HAL Science: OCR impact assessment (~10pt F1 degradation expected)

Usage:
    cd ml
    source .venv/bin/activate
    python scripts/evaluate/test_ner_predictor_adversarial.py
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Adversarial test cases (35 total)
ADVERSARIAL_TESTS = [
    # === EDGE CASE (9 tests) ===
    {
        "id": "single_letter_name",
        "category": "edge_case",
        "difficulty": "medium",
        "text": "El demandante J. García presentó recurso.",
        "expected": [{"text": "J. García", "type": "PERSON"}],
        "notes": "Initial + surname pattern",
    },
    {
        "id": "very_long_name",
        "category": "edge_case",
        "difficulty": "hard",
        "text": "Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.",
        "expected": [{"text": "José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón", "type": "PERSON"}],
        "notes": "Compound noble name with particles",
    },
    {
        "id": "dni_without_letter",
        "category": "edge_case",
        "difficulty": "medium",
        "text": "DNI número 12345678 (pendiente de verificación).",
        "expected": [{"text": "12345678", "type": "DNI_NIE"}],
        "notes": "DNI missing control letter",
    },
    {
        "id": "dni_with_spaces",
        "category": "edge_case",
        "difficulty": "hard",
        "text": "Su documento de identidad es 12 345 678 Z.",
        "expected": [{"text": "12 345 678 Z", "type": "DNI_NIE"}],
        "notes": "DNI with internal spaces",
    },
    {
        "id": "iban_with_spaces",
        "category": "edge_case",
        "difficulty": "easy",
        "text": "Transferir a ES91 2100 0418 4502 0005 1332.",
        "expected": [{"text": "ES91 2100 0418 4502 0005 1332", "type": "IBAN"}],
        "notes": "Standard IBAN format with spaces",
    },
    {
        "id": "phone_international",
        "category": "edge_case",
        "difficulty": "medium",
        "text": "Contacto: +34 612 345 678 o 0034612345678.",
        "expected": [
            {"text": "+34 612 345 678", "type": "PHONE"},
            {"text": "0034612345678", "type": "PHONE"},
        ],
        "notes": "International phone formats",
    },
    {
        "id": "date_roman_numerals",
        "category": "edge_case",
        "difficulty": "hard",
        "text": "Otorgado el día XV de marzo del año MMXXIV.",
        "expected": [{"text": "XV de marzo del año MMXXIV", "type": "DATE"}],
        "notes": "Date with Roman numerals (notarial style)",
    },
    {
        "id": "date_ordinal",
        "category": "edge_case",
        "difficulty": "medium",
        "text": "El primero de enero de dos mil veinticuatro.",
        "expected": [{"text": "primero de enero de dos mil veinticuatro", "type": "DATE"}],
        "notes": "Fully written out date",
    },
    {
        "id": "address_floor_door",
        "category": "edge_case",
        "difficulty": "medium",
        "text": "Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.",
        "expected": [
            {"text": "Calle Mayor 15, 3º B", "type": "ADDRESS"},
            {"text": "28001", "type": "POSTAL_CODE"},
            {"text": "Madrid", "type": "LOCATION"},
        ],
        "notes": "Address with floor and door",
    },
    # === ADVERSARIAL (8 tests) ===
    {
        "id": "negation_dni",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "El interesado manifiesta NO tener DNI ni NIE.",
        "expected": [],
        "notes": "Should NOT detect PII - negation context",
    },
    {
        "id": "example_dni",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "El formato del DNI es 12345678X (ejemplo ilustrativo).",
        "expected": [],
        "notes": "Example/illustrative context should be ignored",
    },
    {
        "id": "fictional_person",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "Como dijo Don Quijote de la Mancha en su célebre obra.",
        "expected": [],
        "notes": "Fictional/literary character - not PII",
    },
    {
        "id": "organization_as_person",
        "category": "adversarial",
        "difficulty": "medium",
        "text": "García y Asociados, S.L. interpone demanda.",
        "expected": [{"text": "García y Asociados, S.L.", "type": "ORGANIZATION"}],
        "notes": "Surname in company name - should be ORG not PERSON",
    },
    {
        "id": "location_as_person",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "El municipio de San Fernando del Valle de Catamarca.",
        "expected": [{"text": "San Fernando del Valle de Catamarca", "type": "LOCATION"}],
        "notes": "Location with person-like prefix (San)",
    },
    {
        "id": "date_in_reference",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "Según la Ley 15/2022, de 12 de julio, reguladora...",
        "expected": [],
        "notes": "Date in legal reference - not standalone PII",
    },
    {
        "id": "numbers_not_dni",
        "category": "adversarial",
        "difficulty": "medium",
        "text": "El expediente 12345678 consta de 9 folios.",
        "expected": [],
        "notes": "8-digit number that is NOT a DNI (expediente)",
    },
    {
        "id": "mixed_languages",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "Mr. John Smith, con pasaporte UK123456789, residente en Madrid.",
        "expected": [
            {"text": "John Smith", "type": "PERSON"},
            {"text": "UK123456789", "type": "DNI_NIE"},
            {"text": "Madrid", "type": "LOCATION"},
        ],
        "notes": "English name and foreign passport",
    },
    # === OCR CORRUPTION (5 tests) ===
    {
        "id": "ocr_letter_substitution",
        "category": "ocr_corruption",
        "difficulty": "medium",
        "text": "DNl 12345678Z perteneciente a María García.",
        "expected": [
            {"text": "12345678Z", "type": "DNI_NIE"},
            {"text": "María García", "type": "PERSON"},
        ],
        "notes": "OCR confused I with l",
    },
    {
        "id": "ocr_zero_o_confusion",
        "category": "ocr_corruption",
        "difficulty": "hard",
        "text": "IBAN ES91 21O0 0418 45O2 OOO5 1332.",
        "expected": [{"text": "ES91 21O0 0418 45O2 OOO5 1332", "type": "IBAN"}],
        "notes": "OCR confused 0 with O",
    },
    {
        "id": "ocr_missing_spaces",
        "category": "ocr_corruption",
        "difficulty": "hard",
        "text": "DonJoséGarcíaLópezconDNI12345678X.",
        "expected": [
            {"text": "JoséGarcíaLópez", "type": "PERSON"},
            {"text": "12345678X", "type": "DNI_NIE"},
        ],
        "notes": "OCR lost all spaces",
    },
    {
        "id": "ocr_extra_spaces",
        "category": "ocr_corruption",
        "difficulty": "hard",
        "text": "D N I  1 2 3 4 5 6 7 8 Z  de  M a r í a.",
        "expected": [
            {"text": "1 2 3 4 5 6 7 8 Z", "type": "DNI_NIE"},
            {"text": "M a r í a", "type": "PERSON"},
        ],
        "notes": "OCR added extra spaces",
    },
    {
        "id": "ocr_accent_loss",
        "category": "ocr_corruption",
        "difficulty": "easy",
        "text": "Jose Maria Garcia Lopez, vecino de Malaga.",
        "expected": [
            {"text": "Jose Maria Garcia Lopez", "type": "PERSON"},
            {"text": "Malaga", "type": "LOCATION"},
        ],
        "notes": "OCR lost accents (common)",
    },
    # === UNICODE EVASION (3 tests) ===
    {
        "id": "cyrillic_o",
        "category": "unicode_evasion",
        "difficulty": "hard",
        "text": "DNI 12345678Х pertenece a María.",
        "expected": [
            {"text": "12345678Х", "type": "DNI_NIE"},
            {"text": "María", "type": "PERSON"},
        ],
        "notes": "Cyrillic Х (U+0425) instead of Latin X",
    },
    {
        "id": "zero_width_space",
        "category": "unicode_evasion",
        "difficulty": "hard",
        "text": "DNI 123\u200b456\u200b78Z de María García.",
        "expected": [
            {"text": "12345678Z", "type": "DNI_NIE"},
            {"text": "María García", "type": "PERSON"},
        ],
        "notes": "Zero-width spaces inserted (U+200B)",
    },
    {
        "id": "fullwidth_numbers",
        "category": "unicode_evasion",
        "difficulty": "hard",
        "text": "DNI １２３４５６７８Z de María.",
        "expected": [
            {"text": "１２３４５６７８Z", "type": "DNI_NIE"},
            {"text": "María", "type": "PERSON"},
        ],
        "notes": "Fullwidth digits (U+FF11-U+FF19)",
    },
    # === REAL WORLD (10 tests) ===
    {
        "id": "notarial_header",
        "category": "real_world",
        "difficulty": "medium",
        "text": "NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.",
        "expected": [
            {"text": "Sevilla", "type": "LOCATION"},
            {"text": "quince de marzo de dos mil veinticuatro", "type": "DATE"},
            {"text": "JOSÉ GARCÍA LÓPEZ", "type": "PERSON"},
            {"text": "Sevilla", "type": "LOCATION"},
        ],
        "notes": "Standard notarial deed header",
    },
    {
        "id": "testament_comparecencia",
        "category": "real_world",
        "difficulty": "hard",
        "text": "COMPARECE: Doña MARÍA ANTONIA FERNÁNDEZ RUIZ, mayor de edad, viuda, natural de Córdoba, vecina de Madrid, con domicilio en Calle Alcalá número 123, piso 4º, puerta B, y con D.N.I. número 12345678-Z.",
        "expected": [
            {"text": "MARÍA ANTONIA FERNÁNDEZ RUIZ", "type": "PERSON"},
            {"text": "Córdoba", "type": "LOCATION"},
            {"text": "Madrid", "type": "LOCATION"},
            {"text": "Calle Alcalá número 123, piso 4º, puerta B", "type": "ADDRESS"},
            {"text": "12345678-Z", "type": "DNI_NIE"},
        ],
        "notes": "Testament appearance clause",
    },
    {
        "id": "judicial_sentence_header",
        "category": "real_world",
        "difficulty": "hard",
        "text": "SENTENCIA Nº 123/2024. En Madrid, a diez de enero de dos mil veinticuatro. Vistos por la Sala Primera del Tribunal Supremo los recursos interpuestos por D. ANTONIO PÉREZ MARTÍNEZ, representado por el Procurador D. CARLOS SÁNCHEZ GÓMEZ.",
        "expected": [
            {"text": "Madrid", "type": "LOCATION"},
            {"text": "diez de enero de dos mil veinticuatro", "type": "DATE"},
            {"text": "ANTONIO PÉREZ MARTÍNEZ", "type": "PERSON"},
            {"text": "CARLOS SÁNCHEZ GÓMEZ", "type": "PERSON"},
        ],
        "notes": "Supreme Court sentence header",
    },
    {
        "id": "contract_parties",
        "category": "real_world",
        "difficulty": "hard",
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
        "notes": "Contract parties clause",
    },
    {
        "id": "bank_account_clause",
        "category": "real_world",
        "difficulty": "medium",
        "text": "El pago se efectuará mediante transferencia a la cuenta IBAN ES12 0049 1234 5012 3456 7890 titularidad de CONSTRUCCIONES PÉREZ, S.A., con CIF A-98765432.",
        "expected": [
            {"text": "ES12 0049 1234 5012 3456 7890", "type": "IBAN"},
            {"text": "CONSTRUCCIONES PÉREZ, S.A.", "type": "ORGANIZATION"},
            {"text": "A-98765432", "type": "DNI_NIE"},
        ],
        "notes": "Bank transfer clause",
    },
    {
        "id": "cadastral_reference",
        "category": "real_world",
        "difficulty": "medium",
        "text": "Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.",
        "expected": [
            {"text": "Málaga", "type": "LOCATION"},
            {"text": "1234567AB1234S0001AB", "type": "CADASTRAL_REF"},
        ],
        "notes": "Property registration with cadastral reference",
    },
    {
        "id": "professional_ids",
        "category": "real_world",
        "difficulty": "hard",
        "text": "Interviene el Abogado D. LUIS SÁNCHEZ, colegiado nº 12345 del ICAM, y el Procurador D. MIGUEL TORRES, colegiado nº 67890 del Colegio de Procuradores de Madrid.",
        "expected": [
            {"text": "LUIS SÁNCHEZ", "type": "PERSON"},
            {"text": "12345", "type": "PROFESSIONAL_ID"},
            {"text": "MIGUEL TORRES", "type": "PERSON"},
            {"text": "67890", "type": "PROFESSIONAL_ID"},
        ],
        "notes": "Professional bar numbers",
    },
    {
        "id": "ecli_citation",
        "category": "real_world",
        "difficulty": "easy",
        "text": "Según doctrina del Tribunal Supremo (ECLI:ES:TS:2023:1234), confirmada en ECLI:ES:AN:2024:567.",
        "expected": [
            {"text": "ECLI:ES:TS:2023:1234", "type": "ECLI"},
            {"text": "ECLI:ES:AN:2024:567", "type": "ECLI"},
        ],
        "notes": "ECLI case citations",
    },
    {
        "id": "vehicle_clause",
        "category": "real_world",
        "difficulty": "medium",
        "text": "El vehículo marca SEAT, modelo Ibiza, matrícula 1234 ABC, propiedad de D. FRANCISCO LÓPEZ.",
        "expected": [
            {"text": "1234 ABC", "type": "LICENSE_PLATE"},
            {"text": "FRANCISCO LÓPEZ", "type": "PERSON"},
        ],
        "notes": "Vehicle description clause",
    },
    {
        "id": "social_security",
        "category": "real_world",
        "difficulty": "easy",
        "text": "Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.",
        "expected": [{"text": "281234567890", "type": "NSS"}],
        "notes": "Social security number in employment context",
    },
]


@dataclass
class EntityMetrics:
    """Entity-level precision, recall, F1 metrics (seqeval-style)."""

    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)

    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)


@dataclass
class TestResult:
    """Result of a single adversarial test."""

    test_id: str
    category: str
    difficulty: str
    passed: bool
    expected_count: int
    detected_count: int
    correct: int
    missed: int
    false_positives: int
    details: str
    overlap_score: float = 0.0  # Partial match quality (0-1)


def normalize_text(text: str) -> str:
    """Normalize text for comparison, handling OCR artifacts."""
    # Remove zero-width characters
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.lower().strip()


def calculate_overlap_ratio(text1: str, text2: str) -> float:
    """
    Calculate character-level overlap ratio between two strings.
    Used for partial match scoring.
    """
    if not text1 or not text2:
        return 0.0
    t1 = set(normalize_text(text1))
    t2 = set(normalize_text(text2))
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union if union > 0 else 0.0


def entities_match(expected: dict, detected: dict, tolerance: int = 5) -> bool:
    """
    Check if two entities match with fuzzy tolerance.

    Args:
        expected: Expected entity dict
        detected: Detected entity dict
        tolerance: Character tolerance for text matching

    Returns:
        True if entities match
    """
    # Type must match
    if expected["type"] != detected["type"]:
        return False

    # Text comparison with tolerance
    exp_text = normalize_text(expected["text"])
    det_text = normalize_text(detected["text"])

    # Exact match
    if exp_text == det_text:
        return True

    # Containment (detected contains expected or vice versa)
    if exp_text in det_text or det_text in exp_text:
        return True

    # Length difference tolerance
    if abs(len(exp_text) - len(det_text)) <= tolerance:
        # Check character overlap
        common = sum(1 for c in exp_text if c in det_text)
        if common >= len(exp_text) * 0.8:
            return True

    return False


def evaluate_test(test: dict, predictions: list) -> TestResult:
    """
    Evaluate a single test case with entity-level matching.

    Args:
        test: Test case dict
        predictions: List of predicted entities

    Returns:
        TestResult object with overlap scoring
    """
    expected = test["expected"]
    detected = [{"text": p.text, "type": p.entity_type} for p in predictions]

    # Match expected to detected
    matched_expected = set()
    matched_detected = set()
    overlap_scores = []

    for i, exp in enumerate(expected):
        best_overlap = 0.0
        best_j = -1
        for j, det in enumerate(detected):
            if j not in matched_detected and entities_match(exp, det):
                overlap = calculate_overlap_ratio(exp["text"], det["text"])
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_j = j
        if best_j >= 0:
            matched_expected.add(i)
            matched_detected.add(best_j)
            overlap_scores.append(best_overlap)

    correct = len(matched_expected)
    missed = len(expected) - correct
    false_positives = len(detected) - len(matched_detected)

    # Average overlap score for matched entities
    avg_overlap = sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0

    # Determine pass/fail
    if test["difficulty"] == "easy":
        passed = correct == len(expected)
    elif test["difficulty"] == "medium":
        passed = correct == len(expected)
    else:  # hard
        passed = correct == len(expected) and false_positives == 0

    # Build details
    details_parts = []
    if missed > 0:
        missed_texts = [expected[i]["text"] for i in range(len(expected)) if i not in matched_expected]
        details_parts.append(f"Missed: {missed_texts}")
    if false_positives > 0:
        fp_texts = [detected[j]["text"] for j in range(len(detected)) if j not in matched_detected]
        details_parts.append(f"FP: {fp_texts}")

    return TestResult(
        test_id=test["id"],
        category=test["category"],
        difficulty=test["difficulty"],
        passed=passed,
        expected_count=len(expected),
        detected_count=len(detected),
        correct=correct,
        missed=missed,
        false_positives=false_positives,
        details="; ".join(details_parts) if details_parts else "OK",
        overlap_score=avg_overlap,
    )


def calculate_aggregate_metrics(results: list[TestResult]) -> EntityMetrics:
    """Calculate aggregate entity-level metrics across all tests."""
    metrics = EntityMetrics()
    for r in results:
        metrics.true_positives += r.correct
        metrics.false_positives += r.false_positives
        metrics.false_negatives += r.missed
    return metrics


def calculate_noise_degradation(results: list[TestResult]) -> dict:
    """
    Calculate performance degradation due to noise (OCR, unicode).

    Based on HAL Science research: OCR typically causes ~10pt F1 drop.
    """
    clean_categories = {"edge_case", "adversarial", "real_world"}
    noise_categories = {"ocr_corruption", "unicode_evasion"}

    clean_results = [r for r in results if r.category in clean_categories]
    noise_results = [r for r in results if r.category in noise_categories]

    clean_metrics = calculate_aggregate_metrics(clean_results)
    noise_metrics = calculate_aggregate_metrics(noise_results)

    return {
        "clean_f1": clean_metrics.f1,
        "noise_f1": noise_metrics.f1,
        "degradation": clean_metrics.f1 - noise_metrics.f1,
        "expected_degradation": 0.10,  # HAL Science baseline
        "within_expected": (clean_metrics.f1 - noise_metrics.f1) <= 0.15,
    }


def generate_report(results: list[TestResult], model_name: str, elapsed_time: float) -> str:
    """Generate markdown report with entity-level metrics and noise analysis."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Calculate aggregate entity-level metrics
    aggregate = calculate_aggregate_metrics(results)
    noise_analysis = calculate_noise_degradation(results)

    # Calculate stats
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    # Average overlap score
    avg_overlap = sum(r.overlap_score for r in results if r.overlap_score > 0)
    overlap_count = sum(1 for r in results if r.overlap_score > 0)
    mean_overlap = avg_overlap / overlap_count if overlap_count > 0 else 0.0

    # By category
    categories = defaultdict(lambda: {"passed": 0, "total": 0, "tp": 0, "fp": 0, "fn": 0})
    for r in results:
        categories[r.category]["total"] += 1
        categories[r.category]["tp"] += r.correct
        categories[r.category]["fp"] += r.false_positives
        categories[r.category]["fn"] += r.missed
        if r.passed:
            categories[r.category]["passed"] += 1

    # By difficulty
    difficulties = {}
    for r in results:
        if r.difficulty not in difficulties:
            difficulties[r.difficulty] = {"passed": 0, "total": 0}
        difficulties[r.difficulty]["total"] += 1
        if r.passed:
            difficulties[r.difficulty]["passed"] += 1

    # Build report
    lines = [
        f"# Evaluación Adversarial - {model_name}",
        "",
        f"**Fecha:** {timestamp}",
        f"**Modelo:** {model_name}",
        f"**Tests:** {total}",
        f"**Tiempo total:** {elapsed_time:.1f}s",
        "",
        "---",
        "",
        "## Resumen Ejecutivo",
        "",
        "### Métricas Entity-Level (seqeval-style)",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| Precision | {aggregate.precision:.3f} |",
        f"| Recall | {aggregate.recall:.3f} |",
        f"| **F1-Score** | **{aggregate.f1:.3f}** |",
        f"| True Positives | {aggregate.true_positives} |",
        f"| False Positives | {aggregate.false_positives} |",
        f"| False Negatives | {aggregate.false_negatives} |",
        f"| Mean Overlap Score | {mean_overlap:.3f} |",
        "",
        "### Resistencia al Ruido (NoiseBench-style)",
        "",
        "| Métrica | Valor | Referencia |",
        "|---------|-------|------------|",
        f"| F1 (texto limpio) | {noise_analysis['clean_f1']:.3f} | - |",
        f"| F1 (con ruido) | {noise_analysis['noise_f1']:.3f} | - |",
        f"| Degradación | {noise_analysis['degradation']:.3f} | ≤0.10 esperado |",
        f"| Estado | {'✅ OK' if noise_analysis['within_expected'] else '⚠️ Alta degradación'} | HAL Science ref |",
        "",
        "### Tests por Resultado",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| Tests totales | {total} |",
        f"| Pasados | {passed} ({100*passed/total:.1f}%) |",
        f"| Fallados | {failed} ({100*failed/total:.1f}%) |",
        "",
        "### Por Categoría (con F1)",
        "",
        "| Categoría | Pass Rate | TP | FP | FN | F1 |",
        "|-----------|-----------|----|----|----|----|",
    ]

    for cat, stats in sorted(categories.items()):
        rate = 100 * stats["passed"] / stats["total"]
        tp, fp, fn = stats["tp"], stats["fp"], stats["fn"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        lines.append(f"| {cat} | {rate:.1f}% | {tp} | {fp} | {fn} | {f1:.3f} |")

    lines.extend([
        "",
        "### Por Dificultad",
        "",
        "| Dificultad | Pasados | Total | Tasa |",
        "|------------|---------|-------|------|",
    ])

    for diff in ["easy", "medium", "hard"]:
        if diff in difficulties:
            stats = difficulties[diff]
            rate = 100 * stats["passed"] / stats["total"]
            lines.append(f"| {diff} | {stats['passed']} | {stats['total']} | {rate:.1f}% |")

    lines.extend([
        "",
        "---",
        "",
        "## Análisis de Errores",
        "",
    ])

    # Failed tests summary
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        lines.extend([
            "### Tests Fallados",
            "",
            "| Test ID | Categoría | Missed | FP | Detalle |",
            "|---------|-----------|--------|----|---------| ",
        ])
        for r in failed_tests:
            detail = r.details[:50] + "..." if len(r.details) > 50 else r.details
            lines.append(f"| {r.test_id} | {r.category} | {r.missed} | {r.false_positives} | {detail} |")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Resultados Detallados",
        "",
    ])

    # Group by category
    current_cat = None
    for r in sorted(results, key=lambda x: (x.category, x.test_id)):
        if r.category != current_cat:
            current_cat = r.category
            lines.append(f"### {current_cat.upper()}")
            lines.append("")

        status = "✅ PASS" if r.passed else "❌ FAIL"
        lines.extend([
            f"#### {r.test_id} [{status}]",
            "",
            f"**Dificultad:** {r.difficulty} | **Overlap:** {r.overlap_score:.2f}",
            f"**Esperado:** {r.expected_count} | **Detectado:** {r.detected_count}",
            f"**Correctos:** {r.correct} | **Perdidos:** {r.missed} | **FP:** {r.false_positives}",
            f"**Detalles:** {r.details}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## Referencias",
        "",
        "- **seqeval**: Entity-level evaluation metrics for NER",
        "- **NoiseBench (ICLR 2024)**: Real vs simulated noise evaluation",
        "- **HAL Science**: OCR impact assessment (~10pt F1 degradation expected)",
        "",
        f"**Generado por:** `scripts/evaluate/test_ner_predictor_adversarial.py`",
        f"**Fecha:** {datetime.now().strftime('%Y-%m-%d')}",
    ])

    return "\n".join(lines)


def main():
    """Run adversarial evaluation."""
    import sys

    # Import predictor
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from scripts.inference.ner_predictor import NERPredictor

    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MODEL_PATH = BASE_DIR / "models" / "legal_ner_v2"
    REPORT_DIR = BASE_DIR / "docs" / "reports"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("ADVERSARIAL EVALUATION - NER PREDICTOR v2")
    print("=" * 60)

    # Load model
    print("\nLoading model...")
    start_load = time.time()
    predictor = NERPredictor(MODEL_PATH)
    load_time = time.time() - start_load
    print(f"Model loaded in {load_time:.1f}s")

    # Run tests
    print(f"\nRunning {len(ADVERSARIAL_TESTS)} adversarial tests...")
    start_eval = time.time()

    results = []
    for i, test in enumerate(ADVERSARIAL_TESTS):
        predictions = predictor.predict(test["text"], min_confidence=0.3)
        result = evaluate_test(test, predictions)
        results.append(result)

        status = "✅" if result.passed else "❌"
        print(f"  [{i+1:02d}/{len(ADVERSARIAL_TESTS)}] {status} {test['id']}")

    eval_time = time.time() - start_eval
    print(f"\nEvaluation completed in {eval_time:.1f}s")

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{total} ({100*passed/total:.1f}%)")
    print(f"{'=' * 60}")

    # Generate report
    report = generate_report(results, "legal_ner_v2", eval_time)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    report_path = REPORT_DIR / f"{timestamp}_adversarial_ner_v2.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")

    # Return exit code
    return 0 if passed / total >= 0.5 else 1


if __name__ == "__main__":
    exit(main())
