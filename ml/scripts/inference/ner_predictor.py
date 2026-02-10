#!/usr/bin/env python3
"""
NER Predictor wrapper for legal_ner_v2 model.

Loads the fine-tuned model and provides inference on Spanish legal text.
Converts model predictions to entity spans with confidence scores.

Includes:
- Text normalization for Unicode/OCR robustness
- Regex patterns for identifiers with spaces/dashes (hybrid NER)
- Checksum validation for Spanish identifiers (DNI, NIE, IBAN, NSS, CIF)
- Boundary refinement for PAR→COR conversion (prefix/suffix stripping, extension)

Research:
- ml/docs/reports/2026-02-03_1730_investigacion_text_normalization.md
- ml/docs/reports/2026-02-03_1800_investigacion_hybrid_ner.md
- ml/docs/reports/2026-02-03_1900_regex_patterns_standalone.md (CHPDA hybrid approach)
- SemEval 2013 Task 9: Entity-level evaluation (COR/INC/PAR/MIS/SPU)

Usage:
    from scripts.inference.ner_predictor import NERPredictor

    predictor = NERPredictor("models/legal_ner_v2")
    entities = predictor.predict("Don José García con DNI 12345678Z")
"""

import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

# Import regex patterns for hybrid NER (optional, graceful degradation)
try:
    # Add parent path for sibling imports
    _script_dir = Path(__file__).resolve().parent
    if str(_script_dir.parent) not in sys.path:
        sys.path.insert(0, str(_script_dir.parent))
    from preprocess.spanish_id_patterns import find_matches, normalize_match, RegexMatch
    REGEX_AVAILABLE = True
except ImportError:
    REGEX_AVAILABLE = False
    RegexMatch = None  # type: ignore

# Import boundary refinement (optional, graceful degradation)
try:
    from preprocess.boundary_refinement import refine_entity, RefinedEntity
    REFINEMENT_AVAILABLE = True
except ImportError:
    REFINEMENT_AVAILABLE = False
    RefinedEntity = None  # type: ignore


# =============================================================================
# TEXT NORMALIZER (for Unicode/OCR robustness)
# =============================================================================

# Zero-width and invisible characters to remove
ZERO_WIDTH_PATTERN = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

# Cyrillic homoglyphs that look identical to Latin
HOMOGLYPHS = {
    '\u0410': 'A', '\u0412': 'B', '\u0415': 'E', '\u041a': 'K',
    '\u041c': 'M', '\u041d': 'H', '\u041e': 'O', '\u0420': 'P',
    '\u0421': 'C', '\u0422': 'T', '\u0425': 'X',
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
    '\u0441': 'c', '\u0443': 'y', '\u0445': 'x',
}


def normalize_text_for_ner(text: str) -> str:
    """
    Normalize text for NER processing.

    Applies:
    - Zero-width character removal
    - NFKC normalization (fullwidth → ASCII)
    - Homoglyph mapping (Cyrillic → Latin)
    - Space normalization

    Does NOT modify:
    - Case (RoBERTa is case-sensitive)
    - Accents (important for Spanish)
    """
    if not text:
        return text

    # 1. Remove zero-width characters
    text = ZERO_WIDTH_PATTERN.sub('', text)

    # 2. NFKC normalization (fullwidth → ASCII)
    text = unicodedata.normalize('NFKC', text)

    # 3. Homoglyph mapping
    for cyrillic, latin in HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)

    # 4. Normalize spaces
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)

    # 5. Remove soft hyphens
    text = text.replace('\u00ad', '')

    return text


# =============================================================================
# CHECKSUM VALIDATORS (for Spanish identifiers)
# =============================================================================

# Control letter sequence for DNI/NIE (mod 23)
DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
NIE_PREFIX_MAP = {'X': '0', 'Y': '1', 'Z': '2'}

# Entity types that support checksum validation
VALIDATABLE_TYPES = {'DNI_NIE', 'IBAN', 'NSS', 'CIF'}

# Entity type merge priorities for hybrid NER-regex pipeline.
# Higher priority number = wins in overlap resolution.
# preferred_source: "regex", "ner", or "any" (no preference).
#
# Based on: RECAP Framework (arXiv 2510.07551, 2025), Mishra et al. (Nature 2025),
# GNNer (ACL SRW 2022), Presidio merge rules.
# See: docs/reports/2026-02-04_1100_investigacion_gaps_pipeline_hibrido.md, section 3.5
MERGE_PRIORITY: dict[str, tuple[int, str]] = {
    # Regex with checksum validation = highest reliability (Mishra et al. 2025)
    "DNI_NIE": (10, "regex"),
    "IBAN": (10, "regex"),
    "NSS": (10, "regex"),
    "CIF": (10, "regex"),
    # Regex with well-defined format
    "PHONE": (8, "regex"),
    "POSTAL_CODE": (8, "regex"),
    "LICENSE_PLATE": (8, "regex"),
    "EMAIL": (7, "regex"),
    "CADASTRAL_REF": (7, "regex"),
    "ECLI": (7, "regex"),
    # Both sources valid
    "DATE": (6, "any"),
    "PROFESSIONAL_ID": (5, "any"),
    # NER excels with semantic context (RECAP, PyDeID)
    "PERSON": (4, "ner"),
    "ORGANIZATION": (4, "ner"),
    "LOCATION": (4, "ner"),
    "ADDRESS": (4, "ner"),
}
DEFAULT_PRIORITY: tuple[int, str] = (5, "any")


def validate_dni_checksum(dni: str) -> tuple[bool, float, str]:
    """Validate Spanish DNI checksum."""
    clean = dni.replace(' ', '').replace('-', '').replace('.', '').upper()
    match = re.match(r'^(\d{8})([A-Z])$', clean)
    if not match:
        return False, 0.0, "invalid_format"
    number, letter = match.groups()
    expected = DNI_LETTERS[int(number) % 23]
    if letter == expected:
        return True, 1.0, "valid"
    return False, 0.5, "invalid_checksum"


def validate_nie_checksum(nie: str) -> tuple[bool, float, str]:
    """Validate Spanish NIE checksum."""
    clean = nie.replace(' ', '').replace('-', '').replace('.', '').upper()
    match = re.match(r'^([XYZ])(\d{7})([A-Z])$', clean)
    if not match:
        return False, 0.0, "invalid_format"
    prefix, number, letter = match.groups()
    full_number = NIE_PREFIX_MAP[prefix] + number
    expected = DNI_LETTERS[int(full_number) % 23]
    if letter == expected:
        return True, 1.0, "valid"
    return False, 0.5, "invalid_checksum"


def validate_dni_or_nie_checksum(identifier: str) -> tuple[bool, float, str]:
    """Validate either DNI or NIE."""
    clean = identifier.replace(' ', '').replace('-', '').replace('.', '').upper()
    if clean and clean[0] in 'XYZ':
        return validate_nie_checksum(identifier)
    return validate_dni_checksum(identifier)


def validate_iban_checksum(iban: str) -> tuple[bool, float, str]:
    """Validate IBAN using ISO 13616 mod 97 algorithm."""
    clean = iban.replace(' ', '').replace('-', '').upper()
    if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', clean):
        return False, 0.0, "invalid_format"
    if clean.startswith('ES') and len(clean) != 24:
        return False, 0.3, "invalid_length"
    rearranged = clean[4:] + clean[:4]
    numeric = ''
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - 55)
        else:
            numeric += char
    try:
        if int(numeric) % 97 == 1:
            return True, 1.0, "valid"
        return False, 0.4, "invalid_checksum"
    except ValueError:
        return False, 0.0, "invalid_format"


def validate_nss_checksum(nss: str) -> tuple[bool, float, str]:
    """Validate Spanish NSS checksum."""
    clean = nss.replace(' ', '').replace('-', '').replace('/', '')
    if not re.match(r'^\d{12}$', clean):
        return False, 0.0, "invalid_format"
    province = clean[:2]
    number = clean[2:10]
    control = clean[10:12]
    base = int(province + number)
    expected_control = base % 97
    if int(control) == expected_control:
        return True, 1.0, "valid"
    return False, 0.5, "invalid_checksum"


def validate_cif_checksum(cif: str) -> tuple[bool, float, str]:
    """Validate Spanish CIF checksum."""
    clean = cif.replace(' ', '').replace('-', '').replace('.', '').upper()
    match = re.match(r'^([A-HJ-NP-SUVW])(\d{7})([0-9A-J])$', clean)
    if not match:
        return False, 0.0, "invalid_format"
    org_type, digits, control = match.groups()
    even_sum = sum(int(digits[i]) for i in [1, 3, 5])
    odd_sum = 0
    for i in [0, 2, 4, 6]:
        doubled = int(digits[i]) * 2
        odd_sum += doubled // 10 + doubled % 10
    total = even_sum + odd_sum
    control_digit = (10 - (total % 10)) % 10
    letter_types = {'K', 'P', 'Q', 'S'}
    digit_types = {'A', 'B', 'E', 'H'}
    control_letter = chr(ord('A') + control_digit) if control_digit < 10 else 'J'
    if org_type in letter_types:
        if control == control_letter:
            return True, 1.0, "valid"
        return False, 0.5, "invalid_checksum"
    elif org_type in digit_types:
        if control == str(control_digit):
            return True, 1.0, "valid"
        return False, 0.5, "invalid_checksum"
    else:
        if control == str(control_digit) or control == control_letter:
            return True, 1.0, "valid"
        return False, 0.5, "invalid_checksum"


def validate_entity_checksum(text: str, entity_type: str) -> tuple[bool, float, str]:
    """Validate checksum for supported entity types."""
    validators = {
        'DNI_NIE': validate_dni_or_nie_checksum,
        'IBAN': validate_iban_checksum,
        'NSS': validate_nss_checksum,
        'CIF': validate_cif_checksum,
    }
    validator = validators.get(entity_type)
    if not validator:
        return True, 1.0, "no_validation"
    return validator(text)


@dataclass
class PredictedEntity:
    """Entity detected by NER model."""

    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    source: str = "ner"
    checksum_valid: bool | None = None
    checksum_reason: str | None = None
    original_text: str | None = None
    refinement_applied: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "text": self.text,
            "type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "source": self.source,
        }
        if self.checksum_valid is not None:
            result["checksum_valid"] = self.checksum_valid
            result["checksum_reason"] = self.checksum_reason
        if self.original_text is not None:
            result["original_text"] = self.original_text
            result["refinement_applied"] = self.refinement_applied
        return result


# =============================================================================
# OVERLAP RESOLUTION (priority-based merge for hybrid NER-regex pipeline)
# =============================================================================


def _pick_winner(
    existing: "PredictedEntity",
    candidate: "PredictedEntity",
) -> str:
    """
    Decide which entity wins in an overlap conflict.

    Returns "existing" or "candidate".

    Resolution order:
    1. Different types → higher priority wins
    2. Same priority, different types → entity from preferred source wins
    3. Same priority, same source preference → longer span wins (more complete)
    4. Same type → preferred source wins
    5. Tiebreaker → higher confidence wins
    """
    e_prio, e_pref = MERGE_PRIORITY.get(existing.entity_type, DEFAULT_PRIORITY)
    c_prio, c_pref = MERGE_PRIORITY.get(candidate.entity_type, DEFAULT_PRIORITY)

    if existing.entity_type != candidate.entity_type:
        if e_prio != c_prio:
            return "existing" if e_prio > c_prio else "candidate"
        # Same priority, different types: prefer entity from its preferred source
        e_from_pref = e_pref == existing.source or e_pref == "any"
        c_from_pref = c_pref == candidate.source or c_pref == "any"
        if e_from_pref and not c_from_pref:
            return "existing"
        if c_from_pref and not e_from_pref:
            return "candidate"
        # Both have same preference: prefer longer span (more complete entity)
        e_len = existing.end - existing.start
        c_len = candidate.end - candidate.start
        if e_len != c_len:
            return "existing" if e_len > c_len else "candidate"
    else:
        # Same type: prefer preferred source
        pref = e_pref
        if pref != "any":
            if pref == existing.source and pref != candidate.source:
                return "existing"
            if pref == candidate.source and pref != existing.source:
                return "candidate"

    return "existing" if existing.confidence >= candidate.confidence else "candidate"


def _resolve_entity_overlaps(
    candidates: list["PredictedEntity"],
) -> list["PredictedEntity"]:
    """
    Resolve overlapping entities using priority-based greedy merge.

    Algorithm: process candidates in priority order (high → low). For each
    candidate, check against already-selected entities:

    1. No overlap → add to selected
    2. Full containment, different types, BOTH high priority → keep both (nested)
    3. Any other overlap → _pick_winner() decides

    Based on: RECAP Framework (arXiv 2510.07551), GNNer (ACL SRW 2022),
    Presidio __remove_duplicates.
    See: docs/reports/2026-02-04_1100_investigacion_gaps_pipeline_hibrido.md, section 3.5
    """
    if not candidates:
        return []

    # Sort by priority (high→low), confidence (high→low), start position
    def sort_key(e: "PredictedEntity") -> tuple[int, float, int]:
        prio, _ = MERGE_PRIORITY.get(e.entity_type, DEFAULT_PRIORITY)
        return (-prio, -e.confidence, e.start)

    sorted_candidates = sorted(candidates, key=sort_key)
    selected: list["PredictedEntity"] = []

    # Threshold for keeping nested entities: both must have priority >= 6
    # This keeps ADDRESS+POSTAL_CODE nested, but drops PERSON inside ORG
    NESTED_PRIORITY_THRESHOLD = 6

    for candidate in sorted_candidates:
        dominated = False
        to_remove: list["PredictedEntity"] = []

        for existing in selected:
            # No overlap → skip
            if candidate.end <= existing.start or candidate.start >= existing.end:
                continue

            # Overlap exists — check if full containment with different types
            e_contains_c = existing.start <= candidate.start and existing.end >= candidate.end
            c_contains_e = candidate.start <= existing.start and candidate.end >= existing.end

            if (e_contains_c or c_contains_e) and candidate.entity_type != existing.entity_type:
                # Check if BOTH entities are high-priority (PII-critical)
                e_prio, _ = MERGE_PRIORITY.get(existing.entity_type, DEFAULT_PRIORITY)
                c_prio, _ = MERGE_PRIORITY.get(candidate.entity_type, DEFAULT_PRIORITY)

                # Same high priority (e.g., NSS vs DNI_NIE): prefer longer span
                if e_prio == c_prio and e_prio >= NESTED_PRIORITY_THRESHOLD:
                    e_len = existing.end - existing.start
                    c_len = candidate.end - candidate.start
                    if e_len > c_len:
                        dominated = True
                        break
                    elif c_len > e_len:
                        to_remove.append(existing)
                        continue
                    # Same length: fall through to normal resolution
                elif e_prio >= NESTED_PRIORITY_THRESHOLD and c_prio >= NESTED_PRIORITY_THRESHOLD:
                    # Different high priorities: keep both as nested entities (GNNer)
                    continue

                # Otherwise, drop the lower-priority one
                if c_prio < e_prio:
                    dominated = True
                    break
                elif c_prio > e_prio:
                    to_remove.append(existing)
                    continue
                # Same priority: use normal resolution

            # Non-nested overlap or same-type containment → resolve
            winner = _pick_winner(existing, candidate)
            if winner == "existing":
                dominated = True
                break
            else:
                to_remove.append(existing)

        if not dominated:
            for e in to_remove:
                selected.remove(e)
            selected.append(candidate)

    selected.sort(key=lambda e: e.start)
    return selected


class NERPredictor:
    """
    NER predictor using fine-tuned RoBERTa model.

    Handles tokenization, inference, and entity extraction.
    """

    def __init__(self, model_path: str | Path, device: str | None = None):
        """
        Initialize predictor with model path.

        Args:
            model_path: Path to model directory (with config.json, model.safetensors, etc.)
            device: Device to use ('cuda', 'cpu', or None for auto-detect)
        """
        self.model_path = Path(model_path)

        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Load model and tokenizer
        self._load_model()

    def _load_model(self) -> None:
        """Load model, tokenizer, and label mappings."""
        print(f"Loading model from {self.model_path}...")
        start = time.time()

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_path),
            use_fast=True,
        )

        # Load model
        self.model = AutoModelForTokenClassification.from_pretrained(
            str(self.model_path),
        )
        self.model.to(self.device)
        self.model.eval()

        # Load label mappings
        label_path = self.model_path / "label_mappings.json"
        if label_path.exists():
            with open(label_path) as f:
                mappings = json.load(f)
                self.id2label = {int(k): v for k, v in mappings["id2label"].items()}
                self.label2id = mappings["label2id"]
        else:
            # Fallback to model config
            self.id2label = self.model.config.id2label
            self.label2id = self.model.config.label2id

        elapsed = time.time() - start
        print(f"Model loaded in {elapsed:.2f}s on {self.device}")
        print(f"Labels: {len(self.id2label)} ({len(self.label2id) // 2} entity types)")

    def predict(
        self,
        text: str,
        min_confidence: float = 0.5,
        max_length: int = 512,
    ) -> list[PredictedEntity]:
        """
        Predict entities in text.

        Args:
            text: Input text
            min_confidence: Minimum confidence threshold
            max_length: Maximum sequence length

        Returns:
            List of PredictedEntity objects
        """
        if not text or not text.strip():
            return []

        # Apply text normalization for Unicode/OCR robustness
        text = normalize_text_for_ner(text)

        if not text:
            return []

        # Tokenize with offset mapping
        encoding = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=max_length,
            truncation=True,
            return_offsets_mapping=True,
            padding=True,
        )

        # Get offset mapping before moving to device
        offset_mapping = encoding.pop("offset_mapping")[0].tolist()

        # Move to device
        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits

        # Get predictions and probabilities
        probabilities = torch.softmax(logits, dim=-1)
        predictions = torch.argmax(logits, dim=-1)[0].cpu().tolist()
        confidences = probabilities[0].max(dim=-1).values.cpu().tolist()

        # Extract entities from NER model
        entities = self._extract_entities(
            text, predictions, confidences, offset_mapping, min_confidence
        )

        # Add regex-based detections (hybrid approach)
        if REGEX_AVAILABLE:
            entities = self._merge_regex_detections(text, entities, min_confidence)

        # Apply boundary refinement (PAR→COR conversion)
        if REFINEMENT_AVAILABLE:
            entities = self._apply_boundary_refinement(text, entities)

        return entities

    def _merge_regex_detections(
        self,
        text: str,
        ner_entities: list["PredictedEntity"],
        min_confidence: float,
    ) -> list["PredictedEntity"]:
        """
        Merge regex-based detections with NER entities using priority-based strategy.

        Strategy (based on RECAP Framework, arXiv 2510.07551):
        - Phase 1: Independent detection (NER + regex already done)
        - Phase 2: Resolve overlaps by entity type priority
        - Phase 3: Consolidation with nested entity support (GNNer)

        See: docs/reports/2026-02-04_1100_investigacion_gaps_pipeline_hibrido.md, section 3.5
        """
        if not REGEX_AVAILABLE:
            return ner_entities

        # Phase 1: Collect all regex candidates with checksum validation
        regex_matches = find_matches(text)
        regex_entities: list[PredictedEntity] = []
        seen_spans: set[tuple[int, int]] = set()

        for match in regex_matches:
            if match.confidence < min_confidence:
                continue

            span_key = (match.start, match.end)
            if span_key in seen_spans:
                continue
            seen_spans.add(span_key)

            normalized_text = normalize_match(match)
            checksum_valid = None
            checksum_reason = None
            final_confidence = match.confidence

            if match.entity_type in VALIDATABLE_TYPES:
                is_valid, checksum_conf, reason = validate_entity_checksum(
                    normalized_text, match.entity_type
                )
                checksum_valid = is_valid
                checksum_reason = reason

                if is_valid:
                    final_confidence = min(match.confidence * 1.1, 0.99)
                elif checksum_conf == 0.5:
                    final_confidence = match.confidence * 0.8
                elif checksum_conf < 0.5:
                    final_confidence = match.confidence * 0.5

            regex_entities.append(
                PredictedEntity(
                    text=match.text,
                    entity_type=match.entity_type,
                    start=match.start,
                    end=match.end,
                    confidence=round(final_confidence, 4),
                    source="regex",
                    checksum_valid=checksum_valid,
                    checksum_reason=checksum_reason,
                )
            )

        # Phase 2 & 3: Resolve overlaps using priority-based merge
        all_candidates = list(ner_entities) + regex_entities
        return _resolve_entity_overlaps(all_candidates)

    def _apply_boundary_refinement(
        self,
        text: str,
        entities: list["PredictedEntity"],
    ) -> list["PredictedEntity"]:
        """
        Apply boundary refinement to convert PAR matches to COR.

        Refinements:
        - Strip honorific prefixes from PERSON (Don, Dña., D., Mr., etc.)
        - Strip date prefixes (a, el día)
        - Strip trailing punctuation from ORGANIZATION
        - Strip postal+city from ADDRESS
        - Extend truncated POSTAL_CODE to 5 digits
        - Extend DNI_NIE to include control letter
        """
        if not REFINEMENT_AVAILABLE:
            return entities

        refined_entities = []

        for ent in entities:
            refined = refine_entity(
                text=ent.text,
                entity_type=ent.entity_type,
                start=ent.start,
                end=ent.end,
                confidence=ent.confidence,
                source=ent.source,
                original_text=text,
            )

            # Create new PredictedEntity with refined values
            refined_entities.append(
                PredictedEntity(
                    text=refined.text,
                    entity_type=refined.entity_type,
                    start=refined.start,
                    end=refined.end,
                    confidence=refined.confidence,
                    source=refined.source,
                    checksum_valid=ent.checksum_valid,
                    checksum_reason=ent.checksum_reason,
                    original_text=refined.original_text,
                    refinement_applied=refined.refinement_applied,
                )
            )

        return refined_entities

    def _extract_entities(
        self,
        text: str,
        predictions: list[int],
        confidences: list[float],
        offset_mapping: list[tuple[int, int]],
        min_confidence: float,
    ) -> list[PredictedEntity]:
        """
        Extract entities from BIO predictions.

        Handles BIO scheme: B-TYPE starts entity, I-TYPE continues.
        """
        entities = []
        current_entity = None

        for i, (pred, conf, (start, end)) in enumerate(
            zip(predictions, confidences, offset_mapping)
        ):
            # Skip special tokens (offset 0,0)
            if start == 0 and end == 0:
                if current_entity:
                    # Finalize current entity
                    entities.append(current_entity)
                    current_entity = None
                continue

            label = self.id2label[pred]

            if label.startswith("B-"):
                # Start of new entity
                if current_entity:
                    entities.append(current_entity)

                entity_type = label[2:]  # Remove "B-" prefix
                current_entity = {
                    "type": entity_type,
                    "start": start,
                    "end": end,
                    "confidences": [conf],
                }

            elif label.startswith("I-") and current_entity:
                # Continue current entity
                entity_type = label[2:]
                if entity_type == current_entity["type"]:
                    # Extend entity
                    current_entity["end"] = end
                    current_entity["confidences"].append(conf)
                else:
                    # Type mismatch - finalize and skip
                    entities.append(current_entity)
                    current_entity = None

            else:
                # O label or I- without B-
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None

        # Finalize last entity
        if current_entity:
            entities.append(current_entity)

        # Convert to PredictedEntity objects with confidence filtering and checksum validation
        result = []
        for ent in entities:
            # Average confidence
            avg_conf = sum(ent["confidences"]) / len(ent["confidences"])

            if avg_conf >= min_confidence:
                entity_text = text[ent["start"] : ent["end"]]
                entity_type = ent["type"]

                # Apply checksum validation for supported types
                checksum_valid = None
                checksum_reason = None
                final_confidence = avg_conf

                if entity_type in VALIDATABLE_TYPES:
                    is_valid, checksum_conf, reason = validate_entity_checksum(
                        entity_text, entity_type
                    )
                    checksum_valid = is_valid
                    checksum_reason = reason

                    # Adjust confidence based on checksum validation
                    if is_valid:
                        # Boost confidence for valid checksum (max 0.99)
                        final_confidence = min(avg_conf * 1.1, 0.99)
                    elif checksum_conf == 0.5:
                        # Reduce confidence for invalid checksum but valid format
                        final_confidence = avg_conf * 0.8
                    elif checksum_conf < 0.5:
                        # Significantly reduce for invalid format
                        final_confidence = avg_conf * 0.5

                result.append(
                    PredictedEntity(
                        text=entity_text,
                        entity_type=entity_type,
                        start=ent["start"],
                        end=ent["end"],
                        confidence=round(final_confidence, 4),
                        checksum_valid=checksum_valid,
                        checksum_reason=checksum_reason,
                    )
                )

        return result

    def predict_batch(
        self,
        texts: list[str],
        min_confidence: float = 0.5,
        max_length: int = 512,
    ) -> list[list[PredictedEntity]]:
        """
        Predict entities for multiple texts.

        Args:
            texts: List of input texts
            min_confidence: Minimum confidence threshold
            max_length: Maximum sequence length

        Returns:
            List of entity lists, one per input text
        """
        # For now, process sequentially
        # TODO: Batch processing for efficiency
        return [self.predict(text, min_confidence, max_length) for text in texts]

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_path": str(self.model_path),
            "device": self.device,
            "num_labels": len(self.id2label),
            "entity_types": sorted(
                set(
                    label[2:] for label in self.id2label.values() if label.startswith("B-")
                )
            ),
            "vocab_size": self.tokenizer.vocab_size,
            "max_length": self.tokenizer.model_max_length,
        }


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys

    # Default model path
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MODEL_PATH = BASE_DIR / "models" / "legal_ner_v2"

    if not MODEL_PATH.exists():
        print(f"Model not found at {MODEL_PATH}")
        sys.exit(1)

    # Initialize predictor
    predictor = NERPredictor(MODEL_PATH)

    # Print model info
    print("\n" + "=" * 60)
    print("MODEL INFO")
    print("=" * 60)
    info = predictor.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Test cases (includes checksum validation and boundary refinement examples)
    test_texts = [
        "Don José García López con DNI 12345678Z.",  # Valid DNI + prefix strip
        "Dña. Ana Martínez Ruiz compareció.",  # Prefix strip
        "La empresa Construcciones Pérez S.L., domiciliada en Madrid.",  # Suffix strip
        "Transferir a IBAN ES91 2100 0418 4502 0005 1332.",  # Valid IBAN
        "En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro.",  # Date prefix
        "Compareció Doña María Antonia Fernández Ruiz, vecina de Córdoba.",
        "Mr. John Smith, residente en Calle Alcalá 50, Madrid.",  # English prefix
        "NIE X0000000T del extranjero.",  # Valid NIE
    ]

    print("\n" + "=" * 60)
    print("NER PREDICTIONS (with checksum + boundary refinement)")
    print("=" * 60)
    print(f"Refinement available: {REFINEMENT_AVAILABLE}")

    for text in test_texts:
        print(f"\n>>> {text}")
        entities = predictor.predict(text, min_confidence=0.3)

        if entities:
            for ent in entities:
                extra_info = []
                if ent.checksum_valid is not None:
                    status = "✅" if ent.checksum_valid else "❌"
                    extra_info.append(f"checksum={status}")
                if ent.refinement_applied:
                    extra_info.append(f"refined:{ent.refinement_applied}")
                    extra_info.append(f"was:'{ent.original_text}'")
                extra_str = " | ".join(extra_info) if extra_info else ""
                print(
                    f"    [{ent.entity_type}] '{ent.text}' "
                    f"({ent.start}:{ent.end}) conf={ent.confidence:.2f}"
                )
                if extra_str:
                    print(f"        {extra_str}")
        else:
            print("    (no entities detected)")

    # Timing test
    print("\n" + "=" * 60)
    print("TIMING TEST")
    print("=" * 60)

    test_text = "Don José García López, mayor de edad, con DNI 12345678Z, vecino de Madrid, domiciliado en Calle Mayor 15, 28001 Madrid."

    times = []
    for _ in range(10):
        start = time.time()
        predictor.predict(test_text)
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)
    print(f"Average inference time: {avg_time * 1000:.1f}ms")
    print(f"Text length: {len(test_text)} chars")

    # Pipeline summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print("\n1. CHECKSUM VALIDATION")
    print(f"   Validatable types: {sorted(VALIDATABLE_TYPES)}")
    print("   Algorithms: DNI/NIE mod 23, IBAN ISO 13616, NSS mod 97, CIF sum")

    print("\n2. BOUNDARY REFINEMENT")
    print(f"   Available: {REFINEMENT_AVAILABLE}")
    if REFINEMENT_AVAILABLE:
        print("   PERSON: Strip Don, Dña., D., Mr., etc.")
        print("   DATE: Strip 'a', 'el día' prefixes")
        print("   ORGANIZATION: Strip trailing commas")
        print("   ADDRESS: Strip postal+city")
        print("   POSTAL_CODE: Extend to 5 digits")
        print("   DNI_NIE: Extend to include control letter")

    print("\n3. HYBRID NER")
    print(f"   Regex patterns available: {REGEX_AVAILABLE}")
