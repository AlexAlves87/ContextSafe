#!/usr/bin/env python3
"""
GLiNER-PII baseline evaluation against ContextSafe adversarial test set.

Evaluates knowledgator/gliner-pii-base-v1.0 (zero-shot PII detection) against
the same 35 adversarial test cases used for legal_ner_v2, using SemEval 2013
Task 9 metrics for fair comparison.

Objective: Establish zero-shot baseline (reported F1 ~81%) before fine-tuning
Legal-XLM-RoBERTa with LoRA.

Research:
- docs/reports/2026-02-04_1300_mejores_practicas_ml_2026.md (Section 3.4)
- GLiNER: NAACL 2024, Wordcab collaboration 2025
- SemEval 2013 Task 9: Entity-level evaluation

Usage:
    cd ml
    source .venv/bin/activate
    pip install gliner  # If not installed
    python scripts/evaluate/evaluate_gliner_baseline.py

Author: AlexAlves87
Date: 2026-02-04
"""

import re
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Check GLiNER availability
try:
    from gliner import GLiNER
    GLINER_AVAILABLE = True
except ImportError:
    GLINER_AVAILABLE = False
    print("ERROR: gliner not installed. Run: pip install gliner")
    exit(1)


# =============================================================================
# ENTITY TYPE MAPPING: ContextSafe → GLiNER labels
# =============================================================================

# Our 15 entity types mapped to GLiNER-PII trained labels
# GLiNER is zero-shot, so we can use descriptive labels
CONTEXTSAFE_TO_GLINER = {
    "PERSON": ["name", "first name", "last name"],
    "DNI_NIE": ["national_id", "ssn", "national id"],
    "IBAN": ["account_number", "bank account", "iban"],
    "PHONE": ["phone_number", "phone number"],
    "EMAIL": ["email", "email address"],
    "ADDRESS": ["street_address", "address", "location address"],
    "LOCATION": ["city", "location city", "location state", "country"],
    "POSTAL_CODE": ["postcode", "postal code", "zip code"],
    "DATE": ["date", "date_of_birth", "dob"],
    "ORGANIZATION": ["company_name", "organization", "company"],
    "LICENSE_PLATE": ["license_plate", "vehicle_identifier", "vehicle id"],
    "NSS": ["national_id", "ssn", "social security number"],
    "CADASTRAL_REF": ["unique_identifier", "property id", "cadastral reference"],
    "ECLI": ["unique_identifier", "case number", "court case id"],
    "PROFESSIONAL_ID": ["certificate_license_number", "professional id", "license number"],
}

# Reverse mapping: GLiNER label → ContextSafe type (first match)
GLINER_TO_CONTEXTSAFE = {}
for cs_type, gliner_labels in CONTEXTSAFE_TO_GLINER.items():
    for label in gliner_labels:
        if label not in GLINER_TO_CONTEXTSAFE:
            GLINER_TO_CONTEXTSAFE[label] = cs_type

# All GLiNER labels to request (union of all mappings)
ALL_GLINER_LABELS = list(set(
    label for labels in CONTEXTSAFE_TO_GLINER.values() for label in labels
))


# =============================================================================
# ADVERSARIAL TEST CASES (same 35 as v2 evaluation)
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
# ENTITY TYPES
# =============================================================================

ENTITY_TYPES = [
    "PERSON", "DNI_NIE", "IBAN", "PHONE", "EMAIL", "ADDRESS",
    "LOCATION", "POSTAL_CODE", "DATE", "ORGANIZATION",
    "LICENSE_PLATE", "NSS", "CADASTRAL_REF", "ECLI", "PROFESSIONAL_ID"
]


# =============================================================================
# NORMALIZATION (same as legal_ner_v2 for fair comparison)
# =============================================================================

ZERO_WIDTH_PATTERN = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

HOMOGLYPHS = {
    '\u0410': 'A', '\u0412': 'B', '\u0415': 'E', '\u041a': 'K',
    '\u041c': 'M', '\u041d': 'H', '\u041e': 'O', '\u0420': 'P',
    '\u0421': 'C', '\u0422': 'T', '\u0425': 'X',
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
    '\u0441': 'c', '\u0443': 'y', '\u0445': 'x',
}


def normalize_for_comparison(text: str) -> str:
    """Normalize text for entity comparison."""
    text = ZERO_WIDTH_PATTERN.sub('', text)
    text = unicodedata.normalize('NFKC', text)
    for cyrillic, latin in HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)
    text = text.replace('\u00ad', '')
    return text.lower().strip()


# =============================================================================
# METRICS
# =============================================================================

@dataclass
class SemEvalMetrics:
    """SemEval 2013 Task 9 metrics."""
    cor: int = 0  # Correct
    inc: int = 0  # Incorrect (boundary ok, type wrong)
    par: int = 0  # Partial match
    mis: int = 0  # Missing (FN)
    spu: int = 0  # Spurious (FP)

    @property
    def possible(self) -> int:
        return self.cor + self.inc + self.par + self.mis

    @property
    def actual(self) -> int:
        return self.cor + self.inc + self.par + self.spu

    @property
    def precision_strict(self) -> float:
        if self.actual == 0:
            return 0.0
        return self.cor / self.actual

    @property
    def recall_strict(self) -> float:
        if self.possible == 0:
            return 0.0
        return self.cor / self.possible

    @property
    def f1_strict(self) -> float:
        p, r = self.precision_strict, self.recall_strict
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    @property
    def f1_partial(self) -> float:
        if self.actual == 0 or self.possible == 0:
            return 0.0
        p = (self.cor + 0.5 * self.par) / self.actual
        r = (self.cor + 0.5 * self.par) / self.possible
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)


@dataclass
class TestResult:
    """Result of a single test."""
    test_id: str
    category: str
    difficulty: str
    passed_strict: bool
    passed_lenient: bool
    expected_count: int
    detected_count: int
    metrics: SemEvalMetrics
    details: str
    missed_entities: list = field(default_factory=list)
    spurious_entities: list = field(default_factory=list)


# =============================================================================
# MATCHING FUNCTIONS
# =============================================================================

def strict_entity_match(expected: dict, detected: dict) -> bool:
    """Strict match: exact text AND type."""
    exp_text = normalize_for_comparison(expected["text"])
    det_text = normalize_for_comparison(detected["text"])
    return exp_text == det_text and expected["type"] == detected["type"]


def exact_boundary_match(expected: dict, detected: dict) -> bool:
    """Boundary match: exact text, any type."""
    exp_text = normalize_for_comparison(expected["text"])
    det_text = normalize_for_comparison(detected["text"])
    return exp_text == det_text


def partial_boundary_match(expected: dict, detected: dict) -> bool:
    """Partial match: text overlap."""
    exp_text = normalize_for_comparison(expected["text"])
    det_text = normalize_for_comparison(detected["text"])
    return exp_text in det_text or det_text in exp_text


# =============================================================================
# GLINER PREDICTOR
# =============================================================================

class GLiNERPredictor:
    """Wrapper for GLiNER-PII model."""

    def __init__(self, model_name: str = "knowledgator/gliner-pii-base-v1.0"):
        """Load GLiNER model."""
        print(f"Loading GLiNER model: {model_name}...")
        start = time.time()

        # Check for local model first
        local_path = Path(__file__).parent.parent.parent / "models" / "pretrained" / "gliner-pii-base-v1.0"
        if local_path.exists():
            print(f"  Using local model: {local_path}")
            self.model = GLiNER.from_pretrained(str(local_path))
        else:
            print(f"  Downloading from HuggingFace Hub...")
            self.model = GLiNER.from_pretrained(model_name)

        elapsed = time.time() - start
        print(f"  Model loaded in {elapsed:.1f}s")

        self.labels = ALL_GLINER_LABELS
        self.threshold = 0.3  # Recommended balanced threshold

    def predict(self, text: str) -> list[dict]:
        """
        Predict entities in text.

        Returns list of dicts with:
        - text: entity text
        - type: ContextSafe entity type (mapped from GLiNER label)
        - start: start offset
        - end: end offset
        - confidence: prediction score
        - gliner_label: original GLiNER label
        """
        if not text or not text.strip():
            return []

        # Get GLiNER predictions
        raw_entities = self.model.predict_entities(
            text,
            self.labels,
            threshold=self.threshold
        )

        # Map to ContextSafe types
        entities = []
        for ent in raw_entities:
            gliner_label = ent["label"]
            cs_type = GLINER_TO_CONTEXTSAFE.get(gliner_label, "UNKNOWN")

            entities.append({
                "text": ent["text"],
                "type": cs_type,
                "start": ent["start"],
                "end": ent["end"],
                "confidence": ent["score"],
                "gliner_label": gliner_label,
            })

        return entities


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_test(test: dict, predictions: list[dict]) -> TestResult:
    """Evaluate single test with SemEval metrics."""
    expected = test["expected"]
    detected = [{"text": p["text"], "type": p["type"]} for p in predictions]

    metrics = SemEvalMetrics()
    matched_expected = set()
    matched_detected = set()

    # Phase 1: Strict matches (COR)
    for i, exp in enumerate(expected):
        for j, det in enumerate(detected):
            if j not in matched_detected:
                if strict_entity_match(exp, det):
                    metrics.cor += 1
                    matched_expected.add(i)
                    matched_detected.add(j)
                    break

    # Phase 2: Boundary-only matches (INC)
    for i, exp in enumerate(expected):
        if i not in matched_expected:
            for j, det in enumerate(detected):
                if j not in matched_detected:
                    if exact_boundary_match(exp, det):
                        metrics.inc += 1
                        matched_expected.add(i)
                        matched_detected.add(j)
                        break

    # Phase 3: Partial matches (PAR)
    for i, exp in enumerate(expected):
        if i not in matched_expected:
            for j, det in enumerate(detected):
                if j not in matched_detected:
                    if partial_boundary_match(exp, det):
                        metrics.par += 1
                        matched_expected.add(i)
                        matched_detected.add(j)
                        break

    # Phase 4: Count misses and spurious
    missed = [expected[i]["text"] for i in range(len(expected)) if i not in matched_expected]
    spurious = [detected[j]["text"] for j in range(len(detected)) if j not in matched_detected]

    metrics.mis = len(missed)
    metrics.spu = len(spurious)

    # Pass/fail
    passed_strict = (metrics.cor == len(expected)) and (metrics.spu == 0)
    if test["difficulty"] == "hard":
        passed_lenient = (metrics.cor + metrics.par >= len(expected)) and (metrics.spu == 0)
    else:
        passed_lenient = (metrics.cor + metrics.par >= len(expected))

    # Details
    details_parts = []
    if missed:
        details_parts.append(f"MIS: {missed}")
    if spurious:
        details_parts.append(f"SPU: {spurious}")
    if metrics.inc > 0:
        details_parts.append(f"INC: {metrics.inc}")
    if metrics.par > 0:
        details_parts.append(f"PAR: {metrics.par}")

    return TestResult(
        test_id=test["id"],
        category=test["category"],
        difficulty=test["difficulty"],
        passed_strict=passed_strict,
        passed_lenient=passed_lenient,
        expected_count=len(expected),
        detected_count=len(detected),
        metrics=metrics,
        details="; ".join(details_parts) if details_parts else "OK",
        missed_entities=missed,
        spurious_entities=spurious,
    )


def aggregate_metrics(results: list[TestResult]) -> SemEvalMetrics:
    """Aggregate metrics across all tests."""
    total = SemEvalMetrics()
    for r in results:
        total.cor += r.metrics.cor
        total.inc += r.metrics.inc
        total.par += r.metrics.par
        total.mis += r.metrics.mis
        total.spu += r.metrics.spu
    return total


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(
    results: list[TestResult],
    total_metrics: SemEvalMetrics,
    elapsed_time: float,
    legal_ner_f1: float = 0.788,
) -> str:
    """Generate markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(results)
    passed_strict = sum(1 for r in results if r.passed_strict)
    passed_lenient = sum(1 for r in results if r.passed_lenient)

    # Calculate delta vs legal_ner_v2
    delta_f1 = total_metrics.f1_strict - legal_ner_f1
    delta_sign = "+" if delta_f1 >= 0 else ""

    # By category
    categories = defaultdict(lambda: {
        "total": 0, "passed_strict": 0,
        "cor": 0, "inc": 0, "par": 0, "mis": 0, "spu": 0
    })
    for r in results:
        cat = categories[r.category]
        cat["total"] += 1
        cat["passed_strict"] += 1 if r.passed_strict else 0
        cat["cor"] += r.metrics.cor
        cat["inc"] += r.metrics.inc
        cat["par"] += r.metrics.par
        cat["mis"] += r.metrics.mis
        cat["spu"] += r.metrics.spu

    lines = [
        "# GLiNER-PII Baseline Evaluation",
        "",
        f"**Fecha:** {timestamp}",
        f"**Modelo:** knowledgator/gliner-pii-base-v1.0",
        f"**Threshold:** 0.3 (balanced)",
        f"**Tests:** {total}",
        f"**Tiempo:** {elapsed_time:.1f}s",
        "",
        "---",
        "",
        "## 1. Resumen Ejecutivo",
        "",
        "### Comparación con legal_ner_v2",
        "",
        "| Modelo | F1 Strict | Precision | Recall | Pass Rate |",
        "|--------|-----------|-----------|--------|-----------|",
        f"| **GLiNER-PII-base** | **{total_metrics.f1_strict:.3f}** | {total_metrics.precision_strict:.3f} | {total_metrics.recall_strict:.3f} | {100*passed_strict/total:.1f}% |",
        f"| legal_ner_v2 | {legal_ner_f1:.3f} | - | - | 60.0% |",
        f"| **Diferencia** | **{delta_sign}{delta_f1:.3f}** | - | - | {delta_sign}{100*(passed_strict/total - 0.60):.1f}pp |",
        "",
        "### Conteos SemEval",
        "",
        "| Métrica | Valor | Descripción |",
        "|---------|-------|-------------|",
        f"| COR | {total_metrics.cor} | Correctos (boundary + type) |",
        f"| INC | {total_metrics.inc} | Boundary OK, type incorrecto |",
        f"| PAR | {total_metrics.par} | Match parcial |",
        f"| MIS | {total_metrics.mis} | Perdidos (FN) |",
        f"| SPU | {total_metrics.spu} | Espurios (FP) |",
        "",
        "---",
        "",
        "## 2. Resultados por Categoría",
        "",
        "| Categoría | Strict | COR | INC | PAR | MIS | SPU |",
        "|-----------|--------|-----|-----|-----|-----|-----|",
    ]

    for cat in ["edge_case", "adversarial", "ocr_corruption", "unicode_evasion", "real_world"]:
        if cat in categories:
            c = categories[cat]
            rate = 100 * c["passed_strict"] / c["total"] if c["total"] > 0 else 0
            lines.append(
                f"| {cat} | {rate:.0f}% | {c['cor']} | {c['inc']} | {c['par']} | {c['mis']} | {c['spu']} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Tests Fallados (Strict)",
        "",
        "| Test | Cat | COR | INC | PAR | MIS | SPU | Detalle |",
        "|------|-----|-----|-----|-----|-----|-----|---------|",
    ])

    failed = [r for r in results if not r.passed_strict]
    for r in failed[:20]:  # Limit to 20 for readability
        m = r.metrics
        detail = r.details[:35] + "..." if len(r.details) > 35 else r.details
        lines.append(
            f"| {r.test_id[:20]} | {r.category[:4]} | {m.cor} | {m.inc} | {m.par} | {m.mis} | {m.spu} | {detail} |"
        )

    if len(failed) > 20:
        lines.append(f"| ... | ... | ... | ... | ... | ... | ... | ({len(failed) - 20} más) |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Análisis",
        "",
        "### Fortalezas de GLiNER",
        "",
        "- Zero-shot: No requiere entrenamiento para nuevos tipos de entidad",
        "- Multilingüe: Soporte nativo para español",
        "- Labels flexibles: Especificados en runtime",
        "",
        "### Debilidades observadas",
        "",
        "- Formatos españoles específicos (DNI, NIE, IBAN con espacios)",
        "- Fechas textuales en español (XV de marzo de MMXXIV)",
        "- Identificadores legales españoles (ECLI, referencias catastrales)",
        "- Contexto negativo (NO tener DNI)",
        "",
        "### Recomendación",
        "",
    ])

    if total_metrics.f1_strict > legal_ner_f1:
        lines.append(
            f"GLiNER supera a legal_ner_v2 ({delta_sign}{delta_f1:.3f} F1). "
            "Considerar como componente del pipeline híbrido o como baseline más exigente."
        )
    else:
        lines.append(
            f"legal_ner_v2 supera a GLiNER zero-shot ({-delta_f1:.3f} F1). "
            "El fine-tuning específico para dominio legal español aporta valor. "
            "Continuar con LoRA fine-tuning de Legal-XLM-RoBERTa."
        )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Configuración",
        "",
        "```python",
        "# Labels usados (mapping a tipos ContextSafe)",
        f"GLINER_LABELS = {ALL_GLINER_LABELS}",
        "",
        "# Threshold",
        "threshold = 0.3  # Balanced (production recommended)",
        "```",
        "",
        "---",
        "",
        f"**Generado por:** `scripts/evaluate/evaluate_gliner_baseline.py`",
        f"**Fecha:** {datetime.now().strftime('%Y-%m-%d')}",
    ])

    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run GLiNER baseline evaluation."""
    print("=" * 70)
    print("GLINER-PII BASELINE EVALUATION")
    print("Model: knowledgator/gliner-pii-base-v1.0")
    print("=" * 70)

    # Load model
    predictor = GLiNERPredictor()

    # Run tests
    print(f"\nRunning {len(ADVERSARIAL_TESTS)} adversarial tests...")
    print()

    start_eval = time.time()
    results = []
    all_predictions = []

    for i, test in enumerate(ADVERSARIAL_TESTS):
        predictions = predictor.predict(test["text"])
        all_predictions.append(predictions)
        result = evaluate_test(test, predictions)
        results.append(result)

        status = "✅" if result.passed_strict else "❌"
        m = result.metrics
        print(
            f"  [{i+1:02d}/{len(ADVERSARIAL_TESTS)}] {status} {test['id']:<25} "
            f"COR:{m.cor} INC:{m.inc} PAR:{m.par} MIS:{m.mis} SPU:{m.spu}"
        )

    eval_time = time.time() - start_eval

    # Summary
    total_metrics = aggregate_metrics(results)
    passed_strict = sum(1 for r in results if r.passed_strict)
    total = len(results)

    print()
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print()
    print(f"  Pass Rate (strict): {passed_strict}/{total} ({100*passed_strict/total:.1f}%)")
    print()
    print(f"  F1 (strict):  {total_metrics.f1_strict:.3f}")
    print(f"  F1 (partial): {total_metrics.f1_partial:.3f}")
    print()
    print(f"  COR: {total_metrics.cor}  INC: {total_metrics.inc}  PAR: {total_metrics.par}")
    print(f"  MIS: {total_metrics.mis}  SPU: {total_metrics.spu}")
    print()
    print(f"  Comparison with legal_ner_v2 (F1 0.788):")
    delta = total_metrics.f1_strict - 0.788
    print(f"  Delta: {'+' if delta >= 0 else ''}{delta:.3f}")
    print()
    print(f"Evaluation time: {eval_time:.1f}s")
    print("=" * 70)

    # Generate report
    report = generate_report(results, total_metrics, eval_time)
    base_dir = Path(__file__).parent.parent.parent
    report_dir = base_dir / "docs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    report_path = report_dir / f"{timestamp}_gliner_baseline_evaluation.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")

    return 0


if __name__ == "__main__":
    exit(main())
