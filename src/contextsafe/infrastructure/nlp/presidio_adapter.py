"""
Presidio NER adapter with Spanish recognizers.

Uses Microsoft Presidio for comprehensive PII detection with custom
Spanish recognizers (DNI, NIE, CIF, NSS, IBAN, phone).

Traceability:
- Contract: CNT-T3-PRESIDIO-ADAPTER-001
- Port: ports.NerService
- IMPLEMENTATION_PLAN.md Phase 5
"""

from __future__ import annotations

import re
from typing import Any

from contextsafe.application.ports import NerDetection, NerService
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)


# Blocklist of Spanish words that are often misclassified as entities
# These should NEVER be detected as PII
FALSE_POSITIVE_BLOCKLIST = {
    # Spanish ordinals (often misclassified as PERSON)
    "PRIMERO", "SEGUNDO", "TERCERO", "CUARTO", "QUINTO",
    "SEXTO", "SÉPTIMO", "OCTAVO", "NOVENO", "DÉCIMO",
    "UNDÉCIMO", "DUODÉCIMO", "DECIMOTERCERO", "DECIMOCUARTO",
    "primero", "segundo", "tercero", "cuarto", "quinto",
    "sexto", "séptimo", "octavo", "noveno", "décimo",
    # Legal terms misclassified as ADDRESS
    "DESNATURALIZACIÓN", "DESNATURALIZACION",
    "VULNERACIÓN", "VULNERACION",
    "IMPUGNACIÓN", "IMPUGNACION",
    "POSICIÓN", "POSICION",
    "RAZONABILIDAD",
    "DISPENSA",
    "ESCRITO",
    "CONCLUSIÓN", "CONCLUSION",
    "SUBSIDIARIAMENTE",
    "IMPROCEDENCIA",
    # Legal procedure types (misclassified as PERSON)
    "PROCEDIMIENTO ORDINARIO", "PROCEDIMIENTO VERBAL",
    "PROCEDIMIENTO MONITORIO", "PROCEDIMIENTO ABREVIADO",
    "JUICIO ORDINARIO", "JUICIO VERBAL",
    # Common words (often misclassified as PERSON)
    "HECHOS", "FUNDAMENTOS", "DERECHO", "SUPLICO",
    "AUTO", "SENTENCIA", "RESOLUCIÓN", "RESOLUCION",
    "Razón", "RAZÓN", "RAZON",  # "Razón por la que..."
    "Todo", "TODO", "Ello", "ELLO",
    "Votación", "VOTACIÓN", "VOTACION",  # "Votación y fallo"
    # Legal roles (not personal names) - WITH and WITHOUT "DON/DOÑA"
    "Procurador", "PROCURADOR", "El Procurador", "EL PROCURADOR",
    "Letrado", "LETRADO", "El Letrado", "EL LETRADO",
    "Magistrado", "MAGISTRADO", "Juez", "JUEZ",
    "Secretario", "SECRETARIO", "Fiscal", "FISCAL",
    "Ponente", "PONENTE",
    # Short words that are never PII
    "LA", "EL", "DE", "EN", "CON", "POR", "DEL", "AL",
    # Company names that are public (banks, etc.)
    "Liberbank", "LIBERBANK",
    "Banca March", "BANCA MARCH",
    # NOTE: Spanish city names REMOVED from blocklist (2026-01-31)
    # In judicial anonymization context, city names MUST be anonymized
    # because they enable triangulation (e.g., "Juzgado de Martorell"
    # identifies the real court). Cities are now detected as LOCATION.
}

# Patterns that indicate false positives (contains these = reject)
FALSE_POSITIVE_PATTERNS = [
    "POSICIÓN DE RAZONABILIDAD",
    "DISPENSA PUNTUAL",
    "DESNATURALIZACIÓN DEL",
    "ESCRITO DE",
    "VULNERACIÓN DEL",
    "VOTACIÓN Y FALLO",
    "RECURSO DE CASACIÓN",
    "RECURSO EXTRAORDINARIO",
]

# Regex patterns that indicate false positives
FALSE_POSITIVE_REGEX = [
    # Case/sentence numbers: 61/2019, 456/2020, 1947/2025
    re.compile(r'^\d{1,4}/\d{4}$'),
    # Dates in legal documents: DE 23 DE DICIEMBRE, DE 14 DE ENERO
    re.compile(r'^DE\s+\d{1,2}\s+DE\s+[A-ZÁÉÍÓÚÑ]+$', re.IGNORECASE),
    # Article references: art. 367, art. 1301
    re.compile(r'^art\.\s*\d+', re.IGNORECASE),
    # Law references: Ley 3/2020, R.D. 1234/2021
    re.compile(r'^(?:Ley|R\.?D\.?)\s*\d+/\d{4}', re.IGNORECASE),
    # Sentence reference with n.º: n.º 61/2019
    re.compile(r'^n\.º\s*\d+/\d{4}$', re.IGNORECASE),
]


def _is_false_positive(text: str, category: str) -> bool:
    """Check if detected text is a known false positive."""
    clean = text.strip()
    upper = clean.upper()

    # Check blocklist
    if clean in FALSE_POSITIVE_BLOCKLIST or upper in FALSE_POSITIVE_BLOCKLIST:
        return True

    # Check patterns
    for pattern in FALSE_POSITIVE_PATTERNS:
        if pattern in upper:
            return True

    # Check regex patterns (case numbers, legal references, etc.)
    for regex in FALSE_POSITIVE_REGEX:
        if regex.match(clean):
            return True

    # For PERSON_NAME: reject if it's just an ordinal possibly with punctuation
    if category == "PERSON_NAME":
        # Remove punctuation and check
        alpha_only = ''.join(c for c in clean if c.isalpha())
        if alpha_only.upper() in FALSE_POSITIVE_BLOCKLIST:
            return True

        # Reject if it looks like a case/sentence number
        if re.match(r'^\d{1,4}/\d{4}$', clean):
            return True

        # Reject single words that are common in legal text
        if ' ' not in clean and len(clean) < 10:
            common_words = {'Razón', 'Todo', 'Ello', 'Votación', 'Enero', 'Febrero',
                          'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto',
                          'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'}
            if clean in common_words or clean.upper() in {w.upper() for w in common_words}:
                return True

    # For DATE: reject public document dates (sentences, laws)
    if category == "DATE":
        # Dates of sentences are public info, not PII
        if re.search(r'SENTENCIA|AUTO|PROVIDENCIA|LEY|DECRETO', upper):
            return True

    return False


def _is_street_name_context(text: str, start: int, full_text: str) -> bool:
    """Check if the detected text is preceded by street indicators."""
    if start < 3:
        return False

    # Look at text before the detection
    prefix = full_text[max(0, start - 20):start].lower()

    street_indicators = [
        "c/", "calle ", "c. ", "avda ", "avda. ", "avenida ",
        "pza ", "pza. ", "plaza ", "paseo ", "pº ",
        "ronda ", "travesía ", "camino ", "carretera ",
        "en ", "de ",  # Common before street names
    ]

    for indicator in street_indicators:
        if prefix.rstrip().endswith(indicator.rstrip()):
            return True

    return False


def _clean_entity_text(text: str, category: str) -> str:
    """Clean entity text by removing surrounding context words."""
    clean = text.strip()

    # For organizations, remove common prefix words that got included
    if category == "ORGANIZATION":
        # First, strip any leading whitespace/newlines
        clean = clean.strip()

        # Prefixes that spaCy/Presidio often include by mistake
        # Order matters - more specific first
        prefixes_to_remove = [
            "contra\n\nla entidad ", "contra\n\nla empresa ",
            "contra\nla entidad ", "contra\nla empresa ",
            "contra la entidad ", "contra la empresa ",
            "la entidad ", "La entidad ", "LA ENTIDAD ",
            "la empresa ", "La empresa ", "LA EMPRESA ",
            "la sociedad ", "La sociedad ", "LA SOCIEDAD ",
            "la mercantil ", "La mercantil ", "LA MERCANTIL ",
            "procesal de ", "representación de ", "parte de ",
            "demandante ", "demandada ", "actora ",
            "interpuesto por ", "formulada por ", "presentado por ",
            "que ", "de ", "por ", "contra ", "a ", "y ",
            "representación ", "comparecencia de ",
        ]
        # Keep removing prefixes until no more match
        changed = True
        while changed:
            changed = False
            clean_lower = clean.lower()
            for prefix in prefixes_to_remove:
                if clean_lower.startswith(prefix.lower()):
                    clean = clean[len(prefix):].strip()
                    changed = True
                    break

        # Also remove trailing punctuation and common suffixes
        clean = clean.rstrip(" .,;:")

    # For addresses, EXTRACT actual address from legal phrasing
    if category == "ADDRESS":
        # Legal prefixes to strip (order matters - most specific first)
        legal_prefixes = [
            "domicilio a efectos de notificaciones en ",
            "domicilio a efectos de notificaciones ",
            "domicilio a efectos de ",
            "domicilio en ",
            "con domicilio en ",
            "residente en ",
        ]
        clean_lower = clean.lower()
        for prefix in legal_prefixes:
            if clean_lower.startswith(prefix):
                clean = clean[len(prefix):]
                clean_lower = clean.lower()

        # If after stripping we have no actual address content, return empty
        # An actual address should have a street indicator or number
        if clean and not any(ind in clean_lower for ind in ["c/", "calle", "avda", "avenida", "plaza", "paseo"]):
            # Check if it at least has a number (like a postal code or street number)
            if not re.search(r'\d', clean):
                return ""

    return clean


# Mapping from Presidio entity types to PII categories
# IMPORTANT: Values must match PiiCategoryEnum values exactly!
PRESIDIO_TO_PII_MAPPING = {
    # Standard Presidio entities
    "PERSON": "PERSON_NAME",
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "IBAN_CODE": "BANK_ACCOUNT",      # Maps to BANK_ACCOUNT (includes IBAN)
    "CREDIT_CARD": "CREDIT_CARD",
    "IP_ADDRESS": "ADDRESS",           # No specific category, use ADDRESS
    "DATE_TIME": "DATE",               # Generic date (not birth date)
    "LOCATION": "LOCATION",            # FIXED: Keep as LOCATION (cities, towns)
    "URL": "ADDRESS",                  # No specific category, use ADDRESS
    # Spanish custom entities - must match PiiCategoryEnum values
    "ES_DNI": "DNI_NIE",               # Fixed: was "DNI", must be "DNI_NIE"
    "ES_NIE": "DNI_NIE",               # Fixed: was "NIE", must be "DNI_NIE"
    "ES_NIF": "DNI_NIE",               # Added: Presidio's built-in NIF recognizer
    "ES_CIF": "DNI_NIE",               # Company tax ID, mapped to DNI_NIE
    "ES_NSS": "SOCIAL_SECURITY",       # Fixed: was "NSS", must be "SOCIAL_SECURITY"
    "ES_PHONE": "PHONE",
    "ES_IBAN": "BANK_ACCOUNT",         # Fixed: was "IBAN", must be "BANK_ACCOUNT"
    # NEW: Custom Spanish recognizers
    "ES_PERSON": "PERSON_NAME",        # Spanish name recognizer
    "ES_ORG": "ORGANIZATION",          # Spanish organization recognizer
    "ES_ZIP_CODE": "POSTAL_CODE",      # Spanish postal codes
    "ES_ADDRESS": "ADDRESS",           # Spanish addresses (street + number)
    "ES_LOCATION": "LOCATION",         # Spanish locations (cities, towns, municipalities)
    "ES_DATE": "DATE",                 # Spanish dates (generic)
    # spaCy entities (via NlpEngine)
    "PER": "PERSON_NAME",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",                 # FIXED: GPE (cities, countries) → LOCATION
    "LOC": "LOCATION",                 # FIXED: LOC (geographic locations) → LOCATION
    # MISC entities - spaCy often misclassifies Spanish entities as MISC
    # We still capture them for review but with lower confidence
    "MISC": "PERSON_NAME",             # spaCy MISC often contains names in legal docs
}


class PresidioNerAdapter(NerService):
    """
    NER service using Microsoft Presidio with Spanish recognizers.

    Combines:
    - Presidio's built-in recognizers (email, credit card, etc.)
    - spaCy NER for names, organizations, locations
    - Custom Spanish recognizers (DNI, NIE, CIF, NSS, IBAN, phone)
    """

    def __init__(
        self,
        model_name: str = "es_core_news_lg",
        supported_languages: list[str] | None = None,
    ) -> None:
        """
        Initialize the Presidio NER adapter.

        Args:
            model_name: spaCy model for NLP engine
            supported_languages: Languages to support (default: ["es", "en"])
        """
        self._model_name = model_name
        self._supported_languages = supported_languages or ["es", "en"]
        self._analyzer: Any = None
        self._is_loaded = False

    async def _ensure_loaded(self) -> None:
        """Ensure Presidio analyzer is loaded with Spanish recognizers."""
        if self._is_loaded:
            return

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider

            # Configure NLP engine with Spanish spaCy model
            nlp_config = {
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": "es", "model_name": self._model_name},
                    {"lang_code": "en", "model_name": "en_core_web_sm"},
                ],
            }

            # Try to create NLP engine
            try:
                provider = NlpEngineProvider(nlp_configuration=nlp_config)
                nlp_engine = provider.create_engine()
            except Exception:
                # Fallback: use default engine if English model not available
                nlp_config_es_only = {
                    "nlp_engine_name": "spacy",
                    "models": [
                        {"lang_code": "es", "model_name": self._model_name},
                    ],
                }
                provider = NlpEngineProvider(nlp_configuration=nlp_config_es_only)
                nlp_engine = provider.create_engine()
                self._supported_languages = ["es"]

            # Create analyzer with NLP engine
            self._analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                supported_languages=self._supported_languages,
            )

            # Add Spanish custom recognizers
            self._add_spanish_recognizers()

            self._is_loaded = True

        except ImportError as e:
            raise RuntimeError(
                f"Presidio not installed. Run: pip install presidio-analyzer presidio-anonymizer. Error: {e}"
            )
        except OSError as e:
            raise RuntimeError(
                f"spaCy model '{self._model_name}' not found. "
                f"Run: python -m spacy download {self._model_name}. Error: {e}"
            )

    def _add_spanish_recognizers(self) -> None:
        """Add custom Spanish recognizers to the analyzer."""
        from contextsafe.infrastructure.nlp.recognizers import (
            SpanishCIFRecognizer,
            SpanishDNIRecognizer,
            SpanishIBANRecognizer,
            SpanishNIERecognizer,
            SpanishNSSRecognizer,
            SpanishPhoneRecognizer,
            SpanishNameRecognizer,
            SpanishOrgRecognizer,
            SpanishPostalCodeRecognizer,
            SpanishAddressRecognizer,
            SpanishDateRecognizer,
        )

        spanish_recognizers = [
            # Identity documents
            SpanishDNIRecognizer(),
            SpanishNIERecognizer(),
            SpanishCIFRecognizer(),
            SpanishNSSRecognizer(),
            # Contact info
            SpanishPhoneRecognizer(),
            SpanishIBANRecognizer(),
            # NEW: Names and organizations (compensates for spaCy limitations)
            SpanishNameRecognizer(),
            SpanishOrgRecognizer(),
            # NEW: Location data
            SpanishPostalCodeRecognizer(),
            SpanishAddressRecognizer(),
            # NEW: Dates
            SpanishDateRecognizer(),
        ]

        for recognizer in spanish_recognizers:
            self._analyzer.registry.add_recognizer(recognizer)

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
    ) -> list[NerDetection]:
        """
        Detect PII entities in text using Presidio.

        Args:
            text: The text to analyze
            categories: Optional filter for specific categories
            min_confidence: Minimum confidence threshold

        Returns:
            List of detected entities
        """
        await self._ensure_loaded()

        if not text or not text.strip():
            return []

        # Analyze text
        results = self._analyzer.analyze(
            text=text,
            language="es",
            score_threshold=min_confidence,
        )

        detections: list[NerDetection] = []

        for result in results:
            # Map Presidio entity type to PII category
            pii_category_str = PRESIDIO_TO_PII_MAPPING.get(result.entity_type)
            if pii_category_str is None:
                continue

            # Extract the raw text
            raw_text = text[result.start:result.end]

            # FILTER 1: Check for false positives (ordinals, legal terms, etc.)
            if _is_false_positive(raw_text, pii_category_str):
                continue

            # FILTER 1.5: Skip person names that are actually street names
            if pii_category_str == "PERSON_NAME":
                if _is_street_name_context(raw_text, result.start, text):
                    continue

            # FILTER 2: Clean the entity text (remove surrounding context)
            cleaned_text = _clean_entity_text(raw_text, pii_category_str)

            # Skip if cleaning removed everything
            if not cleaned_text or len(cleaned_text) < 2:
                continue

            # Calculate adjusted span if text was cleaned
            start_offset = result.start
            end_offset = result.end

            # If we removed a prefix, adjust the start
            if cleaned_text != raw_text:
                prefix_len = raw_text.find(cleaned_text)
                if prefix_len > 0:
                    start_offset = result.start + prefix_len
                # Adjust end for any trailing space/punctuation removed
                end_offset = start_offset + len(cleaned_text)

            # Create PII category
            category_result = PiiCategory.from_string(pii_category_str)
            if category_result.is_err():
                continue
            category = category_result.unwrap()

            # Filter by requested categories
            if categories and category not in categories:
                continue

            # Create span with cleaned text
            span_result = TextSpan.create(start_offset, end_offset, cleaned_text)
            if span_result.is_err():
                continue

            # Create confidence
            conf_result = ConfidenceScore.create(result.score)
            if conf_result.is_err():
                continue

            detections.append(
                NerDetection(
                    category=category,
                    value=cleaned_text,
                    span=span_result.unwrap(),
                    confidence=conf_result.unwrap(),
                    source="presidio",
                )
            )

        # Deduplicate overlapping detections (keep highest confidence)
        return self._deduplicate_detections(detections)

    def _deduplicate_detections(
        self, detections: list[NerDetection]
    ) -> list[NerDetection]:
        """Remove duplicate/overlapping detections, keeping highest confidence."""
        if not detections:
            return []

        # Sort by start position, then by confidence descending
        sorted_dets = sorted(
            detections,
            key=lambda d: (d.span.start, -d.confidence.value)
        )

        result: list[NerDetection] = []
        for det in sorted_dets:
            # Check if this overlaps with any existing detection
            is_duplicate = False
            for existing in result:
                # Same span = exact duplicate
                if (det.span.start == existing.span.start and
                    det.span.end == existing.span.end):
                    is_duplicate = True
                    break
                # Overlapping spans - keep the one with higher confidence
                if (det.span.start < existing.span.end and
                    det.span.end > existing.span.start):
                    # They overlap - existing has higher confidence (we sorted)
                    is_duplicate = True
                    break

            if not is_duplicate:
                result.append(det)

        return result

    async def is_available(self) -> bool:
        """Check if Presidio analyzer is loaded."""
        try:
            await self._ensure_loaded()
            return self._is_loaded
        except Exception:
            return False

    async def get_model_info(self) -> dict:
        """Get information about the loaded analyzer."""
        info = {
            "type": "presidio",
            "spacy_model": self._model_name,
            "is_loaded": self._is_loaded,
            "supported_languages": self._supported_languages,
        }

        if self._is_loaded and self._analyzer:
            # Get list of registered recognizers
            recognizers = [
                r.name for r in self._analyzer.registry.get_recognizers(
                    language="es", all_fields=True
                )
            ]
            info["recognizers"] = recognizers
            info["recognizer_count"] = len(recognizers)

        return info
