#!/usr/bin/env python3
"""
Evaluate LoRA-trained Legal-XLM-RoBERTa against adversarial test set.

Compares the new LoRA model (lora_ner_v1) against:
- legal_ner_v2 (F1 0.788)
- GLiNER zero-shot (F1 0.325)

Uses same 35 adversarial test cases and SemEval 2013 metrics for fair comparison.

Usage:
    cd ml
    source .venv/bin/activate
    python scripts/evaluate/evaluate_lora_ner_adversarial.py

Author: AlexAlves87
Date: 2026-02-04
"""

import json
import re
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer


# =============================================================================
# ADVERSARIAL TEST CASES (same 35 as other evaluations)
# =============================================================================

ADVERSARIAL_TESTS = [
    # === EDGE CASE (9 tests) ===
    {
        "id": "single_letter_name",
        "category": "edge_case",
        "difficulty": "medium",
        "text": "El demandante J. García presentó recurso.",
        "expected": [{"text": "J. García", "type": "PERSON"}],
    },
    {
        "id": "very_long_name",
        "category": "edge_case",
        "difficulty": "hard",
        "text": "Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.",
        "expected": [{"text": "José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón", "type": "PERSON"}],
    },
    {
        "id": "dni_without_letter",
        "category": "edge_case",
        "difficulty": "medium",
        "text": "DNI número 12345678 (pendiente de verificación).",
        "expected": [{"text": "12345678", "type": "DNI_NIE"}],
    },
    {
        "id": "dni_with_spaces",
        "category": "edge_case",
        "difficulty": "hard",
        "text": "Su documento de identidad es 12 345 678 Z.",
        "expected": [{"text": "12 345 678 Z", "type": "DNI_NIE"}],
    },
    {
        "id": "iban_with_spaces",
        "category": "edge_case",
        "difficulty": "easy",
        "text": "Transferir a ES91 2100 0418 4502 0005 1332.",
        "expected": [{"text": "ES91 2100 0418 4502 0005 1332", "type": "IBAN"}],
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
    },
    {
        "id": "date_roman_numerals",
        "category": "edge_case",
        "difficulty": "hard",
        "text": "Otorgado el día XV de marzo del año MMXXIV.",
        "expected": [{"text": "XV de marzo del año MMXXIV", "type": "DATE"}],
    },
    {
        "id": "date_ordinal",
        "category": "edge_case",
        "difficulty": "medium",
        "text": "El primero de enero de dos mil veinticuatro.",
        "expected": [{"text": "primero de enero de dos mil veinticuatro", "type": "DATE"}],
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
    },
    # === ADVERSARIAL (8 tests) ===
    {
        "id": "negation_dni",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "El interesado manifiesta NO tener DNI ni NIE.",
        "expected": [],
    },
    {
        "id": "example_dni",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "El formato del DNI es 12345678X (ejemplo ilustrativo).",
        "expected": [],
    },
    {
        "id": "fictional_person",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "Como dijo Don Quijote de la Mancha en su célebre obra.",
        "expected": [],
    },
    {
        "id": "organization_as_person",
        "category": "adversarial",
        "difficulty": "medium",
        "text": "García y Asociados, S.L. interpone demanda.",
        "expected": [{"text": "García y Asociados, S.L.", "type": "ORGANIZATION"}],
    },
    {
        "id": "location_as_person",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "El municipio de San Fernando del Valle de Catamarca.",
        "expected": [{"text": "San Fernando del Valle de Catamarca", "type": "LOCATION"}],
    },
    {
        "id": "date_in_reference",
        "category": "adversarial",
        "difficulty": "hard",
        "text": "Según la Ley 15/2022, de 12 de julio, reguladora...",
        "expected": [],
    },
    {
        "id": "numbers_not_dni",
        "category": "adversarial",
        "difficulty": "medium",
        "text": "El expediente 12345678 consta de 9 folios.",
        "expected": [],
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
    },
    {
        "id": "ocr_zero_o_confusion",
        "category": "ocr_corruption",
        "difficulty": "hard",
        "text": "IBAN ES91 21O0 0418 45O2 OOO5 1332.",
        "expected": [{"text": "ES91 21O0 0418 45O2 OOO5 1332", "type": "IBAN"}],
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
    },
    {
        "id": "social_security",
        "category": "real_world",
        "difficulty": "easy",
        "text": "Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.",
        "expected": [{"text": "281234567890", "type": "NSS"}],
    },
]


# =============================================================================
# NORMALIZATION
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
    cor: int = 0
    inc: int = 0
    par: int = 0
    mis: int = 0
    spu: int = 0

    @property
    def possible(self) -> int:
        return self.cor + self.inc + self.par + self.mis

    @property
    def actual(self) -> int:
        return self.cor + self.inc + self.par + self.spu

    @property
    def precision_strict(self) -> float:
        return self.cor / self.actual if self.actual > 0 else 0.0

    @property
    def recall_strict(self) -> float:
        return self.cor / self.possible if self.possible > 0 else 0.0

    @property
    def f1_strict(self) -> float:
        p, r = self.precision_strict, self.recall_strict
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


@dataclass
class TestResult:
    """Result of a single test."""
    test_id: str
    category: str
    difficulty: str
    passed_strict: bool
    metrics: SemEvalMetrics
    details: str


# =============================================================================
# MATCHING
# =============================================================================

def strict_entity_match(expected: dict, detected: dict) -> bool:
    exp_text = normalize_for_comparison(expected["text"])
    det_text = normalize_for_comparison(detected["text"])
    return exp_text == det_text and expected["type"] == detected["type"]


def exact_boundary_match(expected: dict, detected: dict) -> bool:
    exp_text = normalize_for_comparison(expected["text"])
    det_text = normalize_for_comparison(detected["text"])
    return exp_text == det_text


def partial_boundary_match(expected: dict, detected: dict) -> bool:
    exp_text = normalize_for_comparison(expected["text"])
    det_text = normalize_for_comparison(detected["text"])
    return exp_text in det_text or det_text in exp_text


# =============================================================================
# LORA NER PREDICTOR
# =============================================================================

class LoRANERPredictor:
    """Predictor using LoRA-trained model."""

    def __init__(self, model_path: str | Path):
        """Load model and tokenizer."""
        self.model_path = Path(model_path)
        print(f"Loading LoRA model from {model_path}...")
        start = time.time()

        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model = AutoModelForTokenClassification.from_pretrained(str(model_path))

        # Load label mappings
        mappings_path = self.model_path / "label_mappings.json"
        with open(mappings_path) as f:
            mappings = json.load(f)
        self.id2label = {int(k): v for k, v in mappings["id2label"].items()}

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()

        elapsed = time.time() - start
        print(f"  Model loaded in {elapsed:.1f}s on {self.device}")

    def predict(self, text: str, min_confidence: float = 0.5) -> list[dict]:
        """Predict entities in text."""
        if not text or not text.strip():
            return []

        # Tokenize
        encoding = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            return_offsets_mapping=True,
        )

        offset_mapping = encoding.pop("offset_mapping")[0].tolist()
        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits

        probabilities = torch.softmax(logits, dim=-1)
        predictions = torch.argmax(logits, dim=-1)[0].cpu().tolist()
        confidences = probabilities[0].max(dim=-1).values.cpu().tolist()

        # Extract entities
        entities = []
        current_entity = None

        for i, (pred, conf, (start, end)) in enumerate(
            zip(predictions, confidences, offset_mapping)
        ):
            if start == 0 and end == 0:
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                continue

            label = self.id2label[pred]

            if label.startswith("B-"):
                if current_entity:
                    entities.append(current_entity)
                entity_type = label[2:]
                current_entity = {
                    "type": entity_type,
                    "start": start,
                    "end": end,
                    "confidences": [conf],
                }

            elif label.startswith("I-") and current_entity:
                entity_type = label[2:]
                if entity_type == current_entity["type"]:
                    current_entity["end"] = end
                    current_entity["confidences"].append(conf)
                else:
                    entities.append(current_entity)
                    current_entity = None

            else:
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None

        if current_entity:
            entities.append(current_entity)

        # Convert to output format
        result = []
        for ent in entities:
            avg_conf = sum(ent["confidences"]) / len(ent["confidences"])
            if avg_conf >= min_confidence:
                result.append({
                    "text": text[ent["start"]:ent["end"]],
                    "type": ent["type"],
                    "start": ent["start"],
                    "end": ent["end"],
                    "confidence": avg_conf,
                })

        return result


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

    passed_strict = (metrics.cor == len(expected)) and (metrics.spu == 0)

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
        metrics=metrics,
        details="; ".join(details_parts) if details_parts else "OK",
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
# REPORT
# =============================================================================

def generate_report(
    results: list[TestResult],
    total_metrics: SemEvalMetrics,
    elapsed_time: float,
) -> str:
    """Generate markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(results)
    passed_strict = sum(1 for r in results if r.passed_strict)

    # Baselines
    legal_ner_v2_f1 = 0.788
    gliner_f1 = 0.325

    delta_v2 = total_metrics.f1_strict - legal_ner_v2_f1
    delta_gliner = total_metrics.f1_strict - gliner_f1

    # By category
    categories = defaultdict(lambda: {"total": 0, "passed": 0, "cor": 0, "mis": 0, "spu": 0})
    for r in results:
        cat = categories[r.category]
        cat["total"] += 1
        cat["passed"] += 1 if r.passed_strict else 0
        cat["cor"] += r.metrics.cor
        cat["mis"] += r.metrics.mis
        cat["spu"] += r.metrics.spu

    lines = [
        "# LoRA Legal-XLM-RoBERTa NER - Evaluación Adversarial",
        "",
        f"**Fecha:** {timestamp}",
        f"**Modelo:** lora_ner_v1 (Legal-XLM-RoBERTa-base + LoRA r=128)",
        f"**Tests:** {total}",
        f"**Tiempo:** {elapsed_time:.1f}s",
        "",
        "---",
        "",
        "## 1. Comparación con Baselines",
        "",
        "| Modelo | F1 Strict | Precision | Recall | Pass Rate | Delta |",
        "|--------|-----------|-----------|--------|-----------|-------|",
        f"| **LoRA NER v1** | **{total_metrics.f1_strict:.3f}** | {total_metrics.precision_strict:.3f} | {total_metrics.recall_strict:.3f} | {100*passed_strict/total:.1f}% | - |",
        f"| legal_ner_v2 | 0.788 | - | - | 60.0% | {delta_v2:+.3f} |",
        f"| GLiNER zero-shot | 0.325 | - | - | 11.4% | {delta_gliner:+.3f} |",
        "",
        "## 2. Conteos SemEval",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| COR | {total_metrics.cor} |",
        f"| INC | {total_metrics.inc} |",
        f"| PAR | {total_metrics.par} |",
        f"| MIS | {total_metrics.mis} |",
        f"| SPU | {total_metrics.spu} |",
        "",
        "## 3. Resultados por Categoría",
        "",
        "| Categoría | Pass Rate | COR | MIS | SPU |",
        "|-----------|-----------|-----|-----|-----|",
    ]

    for cat in ["edge_case", "adversarial", "ocr_corruption", "unicode_evasion", "real_world"]:
        if cat in categories:
            c = categories[cat]
            rate = 100 * c["passed"] / c["total"] if c["total"] > 0 else 0
            lines.append(f"| {cat} | {rate:.0f}% | {c['cor']} | {c['mis']} | {c['spu']} |")

    lines.extend([
        "",
        "## 4. Tests Fallados",
        "",
        "| Test | Cat | COR | INC | PAR | MIS | SPU | Detalle |",
        "|------|-----|-----|-----|-----|-----|-----|---------|",
    ])

    failed = [r for r in results if not r.passed_strict]
    for r in failed:
        m = r.metrics
        detail = r.details[:35] + "..." if len(r.details) > 35 else r.details
        lines.append(
            f"| {r.test_id[:18]} | {r.category[:4]} | {m.cor} | {m.inc} | {m.par} | {m.mis} | {m.spu} | {detail} |"
        )

    if not failed:
        lines.append("| - | - | - | - | - | - | - | Todos pasaron |")

    lines.extend([
        "",
        "---",
        "",
        f"**Generado por:** `scripts/evaluate/evaluate_lora_ner_adversarial.py`",
    ])

    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run LoRA NER adversarial evaluation."""
    print("=" * 70)
    print("LORA NER ADVERSARIAL EVALUATION")
    print("=" * 70)

    # Path to merged model
    base_dir = Path(__file__).resolve().parent.parent.parent
    model_path = base_dir / "models" / "lora_ner_v1" / "merged"

    # Load model
    predictor = LoRANERPredictor(model_path)

    # Run tests
    print(f"\nRunning {len(ADVERSARIAL_TESTS)} adversarial tests...")
    print()

    start_eval = time.time()
    results = []

    for i, test in enumerate(ADVERSARIAL_TESTS):
        predictions = predictor.predict(test["text"], min_confidence=0.3)
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
    print(f"  Precision:    {total_metrics.precision_strict:.3f}")
    print(f"  Recall:       {total_metrics.recall_strict:.3f}")
    print()
    print(f"  COR: {total_metrics.cor}  INC: {total_metrics.inc}  PAR: {total_metrics.par}")
    print(f"  MIS: {total_metrics.mis}  SPU: {total_metrics.spu}")
    print()
    print("  Comparison:")
    print(f"    vs legal_ner_v2 (0.788):  {total_metrics.f1_strict - 0.788:+.3f}")
    print(f"    vs GLiNER (0.325):        {total_metrics.f1_strict - 0.325:+.3f}")
    print()
    print(f"Evaluation time: {eval_time:.1f}s")
    print("=" * 70)

    # Generate report
    report = generate_report(results, total_metrics, eval_time)
    report_dir = base_dir / "docs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    report_path = report_dir / f"{timestamp}_lora_ner_adversarial_evaluation.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")

    return 0


if __name__ == "__main__":
    exit(main())
