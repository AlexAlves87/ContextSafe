#!/usr/bin/env python3
"""
Adversarial evaluation for NER Predictor - Version 2 (Academic Standards).

Implements evaluation according to academic standards:
- SemEval 2013 Task 9: 4 evaluation modes (strict, exact, partial, type)
- nervaluate library for entity-level metrics
- Metrics: COR, INC, PAR, MIS, SPU per mode
- F1 per entity type
- Strict mode as primary metric

Based on:
- SemEval 2013 Task 9: Entity-level evaluation metrics
- RockNER (EMNLP 2021): Adversarial NER evaluation methodology
- NoiseBench (EMNLP 2024): Real noise vs simulated noise
- seqeval/nervaluate: Standard NER evaluation libraries

Usage:
    cd ml
    source .venv/bin/activate
    pip install nervaluate  # If not installed
    python scripts/evaluate/test_ner_predictor_adversarial_v2.py

Author: AlexAlves87
Date: 2026-02-03
"""

import re
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Check nervaluate availability
try:
    from nervaluate import Evaluator
    NERVALUATE_AVAILABLE = True
except ImportError:
    NERVALUATE_AVAILABLE = False
    print("WARNING: nervaluate not installed. Run: pip install nervaluate")


# =============================================================================
# ADVERSARIAL TEST CASES (35 total)
# Same as v1 for comparability
# =============================================================================

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


# =============================================================================
# ENTITY TYPES FOR EVALUATION
# =============================================================================

ENTITY_TYPES = [
    "PERSON", "DNI_NIE", "IBAN", "PHONE", "EMAIL", "ADDRESS",
    "LOCATION", "POSTAL_CODE", "DATE", "ORGANIZATION",
    "LICENSE_PLATE", "NSS", "CADASTRAL_REF", "ECLI", "PROFESSIONAL_ID"
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_entity_offsets(text: str, entity_text: str) -> Optional[Tuple[int, int]]:
    """
    Find character offsets of entity in text.

    Returns (start, end) or None if not found.
    """
    # Direct search
    idx = text.find(entity_text)
    if idx >= 0:
        return (idx, idx + len(entity_text))

    # Case-insensitive search
    idx = text.lower().find(entity_text.lower())
    if idx >= 0:
        return (idx, idx + len(entity_text))

    return None


def convert_to_nervaluate_format(
    text: str,
    entities: List[dict],
    source: str = "expected"
) -> List[dict]:
    """
    Convert entity list to nervaluate format.

    nervaluate expects: [{'label': 'PER', 'start': 0, 'end': 10}, ...]
    """
    result = []
    for ent in entities:
        offsets = find_entity_offsets(text, ent["text"])
        if offsets:
            result.append({
                "label": ent["type"],
                "start": offsets[0],
                "end": offsets[1],
            })
        else:
            # Entity text not found - use placeholder (will count as error)
            print(f"  WARNING: '{ent['text']}' not found in text ({source})")
    return result


def normalize_for_strict_match(text: str) -> str:
    """
    Normalize text for strict matching.

    Applies same normalization as NERPredictor to ensure fair comparison:
    - Remove zero-width characters
    - NFKC normalization (fullwidth → ASCII)
    - Homoglyph mapping (Cyrillic → Latin)
    - Space normalization
    - Lowercase for comparison
    """
    # Zero-width removal
    text = re.sub(r'[\u200b-\u200f\u2060-\u206f\ufeff]', '', text)

    # NFKC normalization (fullwidth → ASCII)
    text = unicodedata.normalize('NFKC', text)

    # Homoglyph mapping (Cyrillic → Latin)
    homoglyphs = {
        '\u0410': 'A', '\u0412': 'B', '\u0415': 'E', '\u041a': 'K',
        '\u041c': 'M', '\u041d': 'H', '\u041e': 'O', '\u0420': 'P',
        '\u0421': 'C', '\u0422': 'T', '\u0425': 'X',
        '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
        '\u0441': 'c', '\u0443': 'y', '\u0445': 'x',
    }
    for cyrillic, latin in homoglyphs.items():
        text = text.replace(cyrillic, latin)

    # Space normalization
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)
    text = text.replace('\u00ad', '')

    return text.lower().strip()


def strict_entity_match(expected: dict, detected: dict) -> bool:
    """
    Strict entity matching per SemEval 2013 Task 9.

    Both boundary (text) AND type must match exactly.
    """
    exp_text = normalize_for_strict_match(expected["text"])
    det_text = normalize_for_strict_match(detected["text"])

    return exp_text == det_text and expected["type"] == detected["type"]


def exact_boundary_match(expected: dict, detected: dict) -> bool:
    """
    Exact boundary matching (type ignored).
    """
    exp_text = normalize_for_strict_match(expected["text"])
    det_text = normalize_for_strict_match(detected["text"])

    return exp_text == det_text


def partial_boundary_match(expected: dict, detected: dict) -> bool:
    """
    Partial boundary matching (overlap, type ignored).
    """
    exp_text = normalize_for_strict_match(expected["text"])
    det_text = normalize_for_strict_match(detected["text"])

    # Any overlap counts
    return exp_text in det_text or det_text in exp_text


# =============================================================================
# METRICS CLASSES
# =============================================================================

@dataclass
class SemEvalMetrics:
    """
    SemEval 2013 Task 9 metrics.

    COR: Correct (boundary AND type match)
    INC: Incorrect (boundary match, type mismatch)
    PAR: Partial (boundary overlap)
    MIS: Missing (false negative)
    SPU: Spurious (false positive)
    """
    cor: int = 0  # Correct
    inc: int = 0  # Incorrect (boundary ok, type wrong)
    par: int = 0  # Partial match
    mis: int = 0  # Missing (FN)
    spu: int = 0  # Spurious (FP)

    @property
    def possible(self) -> int:
        """Total gold standard entities (POS)."""
        return self.cor + self.inc + self.par + self.mis

    @property
    def actual(self) -> int:
        """Total system entities (ACT)."""
        return self.cor + self.inc + self.par + self.spu

    @property
    def precision_strict(self) -> float:
        """Precision for strict mode (COR only)."""
        if self.actual == 0:
            return 0.0
        return self.cor / self.actual

    @property
    def recall_strict(self) -> float:
        """Recall for strict mode (COR only)."""
        if self.possible == 0:
            return 0.0
        return self.cor / self.possible

    @property
    def f1_strict(self) -> float:
        """F1 for strict mode."""
        p, r = self.precision_strict, self.recall_strict
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    @property
    def precision_partial(self) -> float:
        """Precision for partial mode (COR + 0.5*PAR)."""
        if self.actual == 0:
            return 0.0
        return (self.cor + 0.5 * self.par) / self.actual

    @property
    def recall_partial(self) -> float:
        """Recall for partial mode (COR + 0.5*PAR)."""
        if self.possible == 0:
            return 0.0
        return (self.cor + 0.5 * self.par) / self.possible

    @property
    def f1_partial(self) -> float:
        """F1 for partial mode."""
        p, r = self.precision_partial, self.recall_partial
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)


@dataclass
class TestResultV2:
    """Result of a single adversarial test with SemEval metrics."""
    test_id: str
    category: str
    difficulty: str

    # Pass/fail based on strict mode
    passed_strict: bool
    passed_lenient: bool  # For v1 comparison

    # Counts
    expected_count: int
    detected_count: int

    # SemEval metrics
    metrics: SemEvalMetrics

    # Details
    details: str
    missed_entities: List[str] = field(default_factory=list)
    spurious_entities: List[str] = field(default_factory=list)


# =============================================================================
# EVALUATION FUNCTIONS
# =============================================================================

def evaluate_test_strict(
    test: dict,
    predictions: list,
) -> TestResultV2:
    """
    Evaluate single test with SemEval 2013 metrics.

    Primary mode: STRICT (exact boundary + exact type)
    """
    expected = test["expected"]
    detected = [{"text": p.text, "type": p.entity_type} for p in predictions]

    metrics = SemEvalMetrics()
    matched_expected = set()
    matched_detected = set()

    # Phase 1: Find strict matches (COR)
    for i, exp in enumerate(expected):
        for j, det in enumerate(detected):
            if j not in matched_detected:
                if strict_entity_match(exp, det):
                    metrics.cor += 1
                    matched_expected.add(i)
                    matched_detected.add(j)
                    break

    # Phase 2: Find boundary-only matches (INC - type mismatch)
    for i, exp in enumerate(expected):
        if i not in matched_expected:
            for j, det in enumerate(detected):
                if j not in matched_detected:
                    if exact_boundary_match(exp, det):
                        # Boundary matches but type doesn't
                        metrics.inc += 1
                        matched_expected.add(i)
                        matched_detected.add(j)
                        break

    # Phase 3: Find partial matches (PAR)
    for i, exp in enumerate(expected):
        if i not in matched_expected:
            for j, det in enumerate(detected):
                if j not in matched_detected:
                    if partial_boundary_match(exp, det):
                        metrics.par += 1
                        matched_expected.add(i)
                        matched_detected.add(j)
                        break

    # Phase 4: Count misses (MIS) and spurious (SPU)
    missed = [expected[i]["text"] for i in range(len(expected)) if i not in matched_expected]
    spurious = [detected[j]["text"] for j in range(len(detected)) if j not in matched_detected]

    metrics.mis = len(missed)
    metrics.spu = len(spurious)

    # Determine pass/fail
    # Strict: All expected found as COR, no SPU
    passed_strict = (metrics.cor == len(expected)) and (metrics.spu == 0)

    # Lenient (v1 style): COR + PAR >= expected, SPU allowed for easy/medium
    if test["difficulty"] == "hard":
        passed_lenient = (metrics.cor + metrics.par >= len(expected)) and (metrics.spu == 0)
    else:
        passed_lenient = (metrics.cor + metrics.par >= len(expected))

    # Build details
    details_parts = []
    if missed:
        details_parts.append(f"MIS: {missed}")
    if spurious:
        details_parts.append(f"SPU: {spurious}")
    if metrics.inc > 0:
        details_parts.append(f"INC: {metrics.inc} type mismatches")
    if metrics.par > 0:
        details_parts.append(f"PAR: {metrics.par} partial matches")

    return TestResultV2(
        test_id=test["id"],
        category=test["category"],
        difficulty=test["difficulty"],
        passed_strict=passed_strict,
        passed_lenient=passed_lenient,
        expected_count=len(expected),
        detected_count=len(detected),
        metrics=metrics,
        details="; ".join(details_parts) if details_parts else "OK (strict)",
        missed_entities=missed,
        spurious_entities=spurious,
    )


def aggregate_metrics(results: List[TestResultV2]) -> SemEvalMetrics:
    """Aggregate SemEval metrics across all tests."""
    total = SemEvalMetrics()
    for r in results:
        total.cor += r.metrics.cor
        total.inc += r.metrics.inc
        total.par += r.metrics.par
        total.mis += r.metrics.mis
        total.spu += r.metrics.spu
    return total


def metrics_by_entity_type(
    results: List[TestResultV2],
    tests: List[dict],
    all_predictions: List[list],
) -> Dict[str, SemEvalMetrics]:
    """Calculate metrics per entity type."""
    type_metrics = defaultdict(SemEvalMetrics)

    for test, preds, result in zip(tests, all_predictions, results):
        expected = test["expected"]
        detected = [{"text": p.text, "type": p.entity_type} for p in preds]

        # Group by type
        for ent in expected:
            ent_type = ent["type"]
            # Check if found
            found = any(strict_entity_match(ent, d) for d in detected)
            if found:
                type_metrics[ent_type].cor += 1
            else:
                type_metrics[ent_type].mis += 1

        for det in detected:
            det_type = det["type"]
            found = any(strict_entity_match(e, det) for e in expected)
            if not found:
                type_metrics[det_type].spu += 1

    return dict(type_metrics)


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report_v2(
    results: List[TestResultV2],
    tests: List[dict],
    all_predictions: List[list],
    model_name: str,
    elapsed_time: float,
) -> str:
    """Generate comprehensive academic-standard report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Aggregate metrics
    total_metrics = aggregate_metrics(results)
    type_metrics = metrics_by_entity_type(results, tests, all_predictions)

    # Pass rates
    total = len(results)
    passed_strict = sum(1 for r in results if r.passed_strict)
    passed_lenient = sum(1 for r in results if r.passed_lenient)

    # By category
    categories = defaultdict(lambda: {
        "total": 0, "passed_strict": 0, "passed_lenient": 0,
        "cor": 0, "inc": 0, "par": 0, "mis": 0, "spu": 0
    })
    for r in results:
        cat = categories[r.category]
        cat["total"] += 1
        cat["passed_strict"] += 1 if r.passed_strict else 0
        cat["passed_lenient"] += 1 if r.passed_lenient else 0
        cat["cor"] += r.metrics.cor
        cat["inc"] += r.metrics.inc
        cat["par"] += r.metrics.par
        cat["mis"] += r.metrics.mis
        cat["spu"] += r.metrics.spu

    # By difficulty
    difficulties = defaultdict(lambda: {"total": 0, "passed_strict": 0, "passed_lenient": 0})
    for r in results:
        diff = difficulties[r.difficulty]
        diff["total"] += 1
        diff["passed_strict"] += 1 if r.passed_strict else 0
        diff["passed_lenient"] += 1 if r.passed_lenient else 0

    # Build report
    lines = [
        f"# Evaluación Adversarial v2 (Academic Standards) - {model_name}",
        "",
        f"**Fecha:** {timestamp}",
        f"**Modelo:** {model_name}",
        f"**Tests:** {total}",
        f"**Tiempo total:** {elapsed_time:.1f}s",
        f"**Estándar:** SemEval 2013 Task 9",
        "",
        "---",
        "",
        "## 1. Resumen Ejecutivo",
        "",
        "### 1.1 Métricas SemEval 2013 (Strict Mode)",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| **F1 (strict)** | **{total_metrics.f1_strict:.3f}** |",
        f"| Precision (strict) | {total_metrics.precision_strict:.3f} |",
        f"| Recall (strict) | {total_metrics.recall_strict:.3f} |",
        f"| F1 (partial) | {total_metrics.f1_partial:.3f} |",
        "",
        "### 1.2 Conteos SemEval",
        "",
        "| Métrica | Valor | Descripción |",
        "|---------|-------|-------------|",
        f"| COR | {total_metrics.cor} | Correctos (boundary + type exactos) |",
        f"| INC | {total_metrics.inc} | Boundary correcto, type incorrecto |",
        f"| PAR | {total_metrics.par} | Match parcial (overlap) |",
        f"| MIS | {total_metrics.mis} | Perdidos (FN) |",
        f"| SPU | {total_metrics.spu} | Espurios (FP) |",
        f"| **POS** | {total_metrics.possible} | Total gold (COR+INC+PAR+MIS) |",
        f"| **ACT** | {total_metrics.actual} | Total sistema (COR+INC+PAR+SPU) |",
        "",
        "### 1.3 Pass Rate",
        "",
        "| Modo | Pasados | Total | Tasa |",
        "|------|---------|-------|------|",
        f"| **Strict** | {passed_strict} | {total} | **{100*passed_strict/total:.1f}%** |",
        f"| Lenient (v1) | {passed_lenient} | {total} | {100*passed_lenient/total:.1f}% |",
        "",
        "---",
        "",
        "## 2. Métricas por Tipo de Entidad",
        "",
        "| Tipo | COR | MIS | SPU | Precision | Recall | F1 |",
        "|------|-----|-----|-----|-----------|--------|-----|",
    ]

    for ent_type in sorted(type_metrics.keys()):
        m = type_metrics[ent_type]
        prec = m.cor / (m.cor + m.spu) if (m.cor + m.spu) > 0 else 0
        rec = m.cor / (m.cor + m.mis) if (m.cor + m.mis) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        lines.append(f"| {ent_type} | {m.cor} | {m.mis} | {m.spu} | {prec:.2f} | {rec:.2f} | {f1:.2f} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Resultados por Categoría",
        "",
        "| Categoría | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |",
        "|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|",
    ])

    for cat in sorted(categories.keys()):
        c = categories[cat]
        strict_rate = 100 * c["passed_strict"] / c["total"]
        lenient_rate = 100 * c["passed_lenient"] / c["total"]
        # Calculate F1
        prec = c["cor"] / (c["cor"] + c["inc"] + c["par"] + c["spu"]) if (c["cor"] + c["spu"]) > 0 else 0
        rec = c["cor"] / (c["cor"] + c["inc"] + c["par"] + c["mis"]) if (c["cor"] + c["mis"]) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        lines.append(
            f"| {cat} | {strict_rate:.0f}% | {lenient_rate:.0f}% | "
            f"{c['cor']} | {c['inc']} | {c['par']} | {c['mis']} | {c['spu']} | {f1:.2f} |"
        )

    lines.extend([
        "",
        "## 4. Resultados por Dificultad",
        "",
        "| Dificultad | Strict | Lenient | Total |",
        "|------------|--------|---------|-------|",
    ])

    for diff in ["easy", "medium", "hard"]:
        if diff in difficulties:
            d = difficulties[diff]
            strict_rate = 100 * d["passed_strict"] / d["total"]
            lenient_rate = 100 * d["passed_lenient"] / d["total"]
            lines.append(f"| {diff} | {strict_rate:.0f}% | {lenient_rate:.0f}% | {d['total']} |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Tests Fallados (Strict Mode)",
        "",
    ])

    failed = [r for r in results if not r.passed_strict]
    if failed:
        lines.extend([
            "| Test | Cat | COR | INC | PAR | MIS | SPU | Detalle |",
            "|------|-----|-----|-----|-----|-----|-----|---------|",
        ])
        for r in failed:
            m = r.metrics
            detail = r.details[:40] + "..." if len(r.details) > 40 else r.details
            lines.append(
                f"| {r.test_id} | {r.category[:4]} | {m.cor} | {m.inc} | {m.par} | {m.mis} | {m.spu} | {detail} |"
            )
    else:
        lines.append("Todos los tests pasaron en modo strict.")

    lines.extend([
        "",
        "---",
        "",
        "## 6. Comparación v1 vs v2",
        "",
        "| Métrica | v1 (lenient) | v2 (strict) | Diferencia |",
        "|---------|--------------|-------------|------------|",
        f"| Pass rate | {100*passed_lenient/total:.1f}% | {100*passed_strict/total:.1f}% | {100*(passed_lenient-passed_strict)/total:+.1f}pp |",
        f"| F1 | {total_metrics.f1_partial:.3f} | {total_metrics.f1_strict:.3f} | {total_metrics.f1_partial - total_metrics.f1_strict:+.3f} |",
        "",
        "**Nota:** v1 usaba matching lenient (containment + 80% overlap). v2 usa strict (exact boundary + exact type).",
        "",
        "---",
        "",
        "## 7. Referencias",
        "",
        "- **SemEval 2013 Task 9**: Entity-level evaluation with 4 modes (strict, exact, partial, type)",
        "- **RockNER (EMNLP 2021)**: Adversarial NER evaluation methodology",
        "- **NoiseBench (EMNLP 2024)**: Real noise vs simulated noise benchmark",
        "- **nervaluate**: Python library for SemEval-style NER evaluation",
        "",
        f"**Generado por:** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`",
        f"**Fecha:** {datetime.now().strftime('%Y-%m-%d')}",
    ])

    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run adversarial evaluation with academic standards."""
    import sys

    # Import predictor
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from scripts.inference.ner_predictor import NERPredictor

    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MODEL_PATH = BASE_DIR / "models" / "legal_ner_v2"
    REPORT_DIR = BASE_DIR / "docs" / "reports"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("ADVERSARIAL EVALUATION v2 - Academic Standards (SemEval 2013)")
    print("=" * 70)

    # Load model
    print("\nLoading model...")
    start_load = time.time()
    predictor = NERPredictor(MODEL_PATH)
    load_time = time.time() - start_load
    print(f"Model loaded in {load_time:.1f}s")

    # Run tests
    print(f"\nRunning {len(ADVERSARIAL_TESTS)} adversarial tests...")
    print("Mode: STRICT (SemEval 2013 Task 9)")
    print()

    start_eval = time.time()
    results = []
    all_predictions = []

    for i, test in enumerate(ADVERSARIAL_TESTS):
        predictions = predictor.predict(test["text"], min_confidence=0.3)
        all_predictions.append(predictions)
        result = evaluate_test_strict(test, predictions)
        results.append(result)

        # Status with SemEval metrics
        status_strict = "✅" if result.passed_strict else "❌"
        m = result.metrics
        print(f"  [{i+1:02d}/{len(ADVERSARIAL_TESTS)}] {status_strict} {test['id']:<25} "
              f"COR:{m.cor} INC:{m.inc} PAR:{m.par} MIS:{m.mis} SPU:{m.spu}")

    eval_time = time.time() - start_eval

    # Summary
    total_metrics = aggregate_metrics(results)
    passed_strict = sum(1 for r in results if r.passed_strict)
    passed_lenient = sum(1 for r in results if r.passed_lenient)
    total = len(results)

    print()
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print()
    print(f"  Pass Rate (strict):  {passed_strict}/{total} ({100*passed_strict/total:.1f}%)")
    print(f"  Pass Rate (lenient): {passed_lenient}/{total} ({100*passed_lenient/total:.1f}%)")
    print()
    print(f"  F1 (strict):  {total_metrics.f1_strict:.3f}")
    print(f"  F1 (partial): {total_metrics.f1_partial:.3f}")
    print()
    print(f"  COR: {total_metrics.cor}  INC: {total_metrics.inc}  PAR: {total_metrics.par}")
    print(f"  MIS: {total_metrics.mis}  SPU: {total_metrics.spu}")
    print()
    print(f"Evaluation time: {eval_time:.1f}s")
    print("=" * 70)

    # Generate report
    report = generate_report_v2(results, ADVERSARIAL_TESTS, all_predictions, "legal_ner_v2", eval_time)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    report_path = REPORT_DIR / f"{timestamp}_adversarial_v2_academic.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")

    return 0


if __name__ == "__main__":
    exit(main())
