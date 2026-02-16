"""
Composite NER adapter.

Combines multiple NER services for comprehensive PII detection.
Includes post-processing filters for false positive exclusion.

Traceability:
- Contract: CNT-T3-COMPOSITE-ADAPTER-001
- Port: ports.NerService
- Bug Fix: False Positive (Sentencias)
- Optimization: Parallel execution with asyncio.gather
- Optimization: Nested entity handling (Matrioshka problem)
- Enhancement: Intelligent merge with contextual anchors and weighted voting
- Design: docs/plans/2026-02-02-intelligent-merge-spacy-design.md
- Enhancement: Text normalization for Unicode/OCR robustness
- Research: ml/docs/reports/2026-02-03_1730_investigacion_text_normalization.md
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, List, Pattern

from contextsafe.application.ports import NerDetection, NerService, ProgressCallback
from contextsafe.domain.shared.types import Ok
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    PERSON_NAME,
    ORGANIZATION,
    ADDRESS,
    LOCATION,
    DNI_NIE,
    PASSPORT,
    IBAN,
    BANK_ACCOUNT,
    CREDIT_CARD,
)

# Intelligent merge components
from contextsafe.infrastructure.nlp.merge.anchors import apply_contextual_anchors
from contextsafe.infrastructure.nlp.merge.voting import (
    weighted_vote_with_tiebreaker,
    get_weighted_score,
)
from contextsafe.infrastructure.nlp.merge.snapping import snap_all_detections

# Text normalization (Unicode, OCR robustness)
from contextsafe.infrastructure.nlp.text_normalizer import TextNormalizer

# Entity type validation (embedding-based)
from contextsafe.infrastructure.nlp.validators.entity_type_validator import (
    EntityTypeValidator,
    ValidationAction,
)

logger = logging.getLogger(__name__)


# ============================================================================
# FALSE POSITIVE EXCLUSION PATTERNS
# ============================================================================
# These patterns identify text that should NOT be anonymized even if detected.
# They represent public references (court cases, laws, etc.)
# Includes variations found in real CENDOJ documents.

FALSE_POSITIVE_PATTERNS: List[Pattern] = [
    # =========================================================================
    # LEGAL DOCUMENT SECTION TITLES (NOT PII - structure headings)
    # "FUNDAMENTOS DE DERECHO", "HECHOS", "SUPLICO AL JUZGADO", etc.
    # =========================================================================
    re.compile(
        r"^(?:FUNDAMENTOS?|ANTECEDENTES?|CONCLUSI[OÓ]N|CONCLUSIONES)\s+(?:DE\s+)?(?:DERECHO|HECHO|HECHOS?)?\s*$",
        re.IGNORECASE
    ),
    re.compile(r"^HECHOS?\s*(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO)?\s*$", re.IGNORECASE),
    re.compile(r"^(?:SUPLICO|SOLICITO|PIDO)\s+(?:AL\s+)?(?:JUZGADO|TRIBUNAL)?\s*$", re.IGNORECASE),
    re.compile(r"^(?:AL\s+)?JUZGADO\s*$", re.IGNORECASE),
    re.compile(r"^(?:OTROSI|OTROSÍ)\s+DIGO\s*$", re.IGNORECASE),
    re.compile(r"^(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|DÉCIMO)\s*[.:\-]?\s*$", re.IGNORECASE),
    re.compile(r"^(?:EN\s+)?(?:NOMBRE|REPRESENTACI[OÓ]N)\s+(?:Y\s+)?(?:DE|DEL)?\s*$", re.IGNORECASE),
    re.compile(r"^FALLO\s*$", re.IGNORECASE),
    re.compile(r"^VISTOS?\s*$", re.IGNORECASE),
    re.compile(r"^RESULTANDO\s*$", re.IGNORECASE),
    re.compile(r"^CONSIDERANDO\s*$", re.IGNORECASE),

    # Court decisions with variations:
    # "Sentencia 61/2019", "SENTENCIA nº 61/2019", "Sentencia núm. 61/2019"
    re.compile(
        r"^(?:Sentencia|Auto|Providencia|Decreto)\s*(?:n[úu]m?\.?\s*)?\d+/\d{4}$",
        re.IGNORECASE
    ),
    # STS references: "STS 1234/2020", "STSJ 567/2019"
    re.compile(r"^STS[JC]?\s*\d+/\d{4}$", re.IGNORECASE),
    # SAP references: "SAP Madrid 123/2020"
    re.compile(r"^SAP\s+\w+\s+\d+/\d{4}$", re.IGNORECASE),

    # Law references with variations:
    # "Ley 39/2015", "L.O. 1/2004", "Ley Orgánica 3/2007"
    re.compile(
        r"^(?:Ley|L\.?O\.?|Ley\s+Org[áa]nica|R\.?D\.?|Real\s+Decreto|RDL|RD-Ley)\s*\d+/\d{4}$",
        re.IGNORECASE
    ),
    # LEC, LECrim, LOPJ references (standalone)
    re.compile(r"^(?:LEC(?:rim)?|LOPJ|CE|CP|CC|ET|LAU|LPH|LSC|TRLSC)\s*$", re.IGNORECASE),

    # Article references with variations:
    # "artículo 24", "art. 18.4", "arts. 14 y 15", "artículo 24.2 CE"
    re.compile(
        r"^(?:art[íi]culos?|arts?\.?)\s+\d+(?:\.\d+)?(?:\s+(?:y|a|,)\s+\d+(?:\.\d+)?)*(?:\s+(?:CE|CP|CC|LEC|LOPJ|LAU|ET))?$",
        re.IGNORECASE
    ),

    # CRITICAL: Article numbers followed by legal codes - NOT license plates!
    # "1285 CC", "24.2 CE", "371 LEC", "y 1285 CC"
    # This prevents "1285 CC" from being detected as a vehicle plate
    re.compile(
        r"^(?:y\s+)?\d+(?:\.\d+)?\s+(?:CC|CE|CP|LEC|LECrim|LOPJ|ET|LAU|LPH|LSC|TRLSC)$",
        re.IGNORECASE
    ),

    # Lists of articles: "1281.1, 1282 y 1285 CC"
    re.compile(
        r"^\d+(?:\.\d+)?(?:\s*,\s*\d+(?:\.\d+)?)*(?:\s+y\s+\d+(?:\.\d+)?)?\s+(?:CC|CE|CP|LEC|LOPJ)$",
        re.IGNORECASE
    ),

    # Case/procedure numbers: "61/2019", "Rollo 123/2020", "Recurso 456/2021"
    re.compile(r"^\d+/\d{4}$"),
    re.compile(
        r"^(?:Rollo|Recurso|Procedimiento|Autos|Ejecutoria|Diligencias)\s*(?:n[úu]m?\.?\s*)?\d+/\d{4}$",
        re.IGNORECASE
    ),

    # NOTE (Corrección #2): Court names pattern REMOVED to allow anonymization
    # of local judicial organs that could enable triangulation.
    # Previously: r"^(?:Juzgado|Audiencia|Tribunal|Sala)\s+(?:de\s+lo\s+)?(?:\w+\s*)+(?:n[úu]m?\.?\s*\d+)?$"
    # Now: Local judicial organs (Juzgado Nº X de Localidad) will be anonymized.
    # Only national-level courts (Tribunal Supremo, Audiencia Nacional) are
    # kept in PUBLIC_INSTITUTIONS for exclusion.

    # NIG (Número de Identificación General) - public case identifier
    re.compile(r"^NIG[:\s]*[\d\-]+$", re.IGNORECASE),

    # ECLI (European Case Law Identifier)
    re.compile(r"^ECLI:ES:\w+:\d{4}:\d+$", re.IGNORECASE),
]


# ============================================================================
# STOPWORDS - Words that should NEVER be detected as PII entities
# (Corrección #6: Falso positivo "Quien")
# ============================================================================
# Pronouns, articles, and common words that NER models may confuse with
# entities when they appear at the beginning of a sentence (capitalized).

SPANISH_STOPWORDS = {
    # Interrogative/relative pronouns (common problems)
    "quien", "quién", "quienes", "quiénes",
    "cual", "cuál", "cuales", "cuáles",
    "que", "qué",
    "donde", "dónde", "adonde", "adónde",
    "cuando", "cuándo",
    "como", "cómo",
    "cuanto", "cuánto", "cuanta", "cuánta",

    # Personal pronouns
    "yo", "tu", "tú", "el", "él", "ella", "ello",
    "nosotros", "nosotras", "vosotros", "vosotras",
    "ellos", "ellas", "usted", "ustedes",

    # Demonstratives
    "este", "esta", "esto", "estos", "estas",
    "ese", "esa", "eso", "esos", "esas",
    "aquel", "aquella", "aquello", "aquellos", "aquellas",

    # Articles (in case they're capitalized)
    "el", "la", "los", "las", "un", "una", "unos", "unas",

    # Common connectors
    "sin embargo", "no obstante", "por tanto", "por lo tanto",
    "asimismo", "además", "también", "tampoco",

    # Common legal words that are NOT PII
    "demandante", "demandado", "demandada", "actor", "actora",
    "recurrente", "recurrido", "recurrida", "apelante", "apelado",
    "querellante", "querellado", "querellada", "denunciante",
    "denunciado", "denunciada", "ejecutante", "ejecutado", "ejecutada",

    # Legal adverbs (often misclassified by RoBERTa as PERSON/ORG)
    "subsidiariamente", "alternativamente", "conjuntamente",
    "solidariamente", "mancomunadamente", "expresamente",
    "tácitamente", "implícitamente", "explícitamente",
    "parcialmente", "totalmente", "íntegramente",

    # Verbs and adverbs misclassified as ORG (audit findings)
    "terminaba", "finalmente", "inicialmente", "posteriormente",
    "seguidamente", "inmediatamente", "anteriormente",
}

# Short common words that should be filtered when detected alone
COMMON_SHORT_WORDS = {
    "para", "pero", "sino", "pues", "tras", "ante", "bajo", "cabe",
    "con", "contra", "desde", "hasta", "hacia", "según", "sin", "sobre",
    "durante", "mediante", "excepto", "salvo",
}


# ============================================================================
# PLATFORM NAMES BLOCKLIST (Error 3 — WhatsApp as Persona)
# Platform/app names that spaCy/RoBERTa misclassify as PERSON_NAME.
# These should ONLY be detected as PLATFORM, never as PERSON_NAME.
# ============================================================================
PLATFORM_NAMES_BLOCKLIST = {
    "whatsapp", "telegram", "signal", "messenger",
    "instagram", "facebook", "twitter", "tiktok",
    "linkedin", "snapchat", "discord", "slack",
    "teams", "skype", "zoom", "wechat", "viber",
    "wallapop", "vinted", "milanuncios", "idealista",
    "fotocasa", "infojobs", "imessage", "facetime",
}


# ============================================================================
# GENERIC TERMS WHITELIST (FP-4)
# Terms that represent generic concepts, not specific PII entities.
# These should NEVER be anonymized even if detected as ORG/PERSON.
# ============================================================================

GENERIC_TERMS_WHITELIST = {
    # Generic political/institutional terms
    "estado", "estados", "unión", "union", "nación", "nacion",
    "parlamento", "consejo", "comisión", "comision",
    "gobierno", "ministerio", "tribunal", "juzgado",
    "congreso", "senado", "cortes",
    # Generic geographic terms
    "europa", "asia", "africa", "américa", "america",
    # Acronyms for regulations/documents (not organizations)
    "ria", "rgpd", "gdpr", "lopd", "lopdgdd",
    "lec", "lecrim", "lopj", "ce", "cp", "cc", "et",
    # Common words incorrectly detected as entities
    "conducta", "proceso", "principios", "reglamento",
    "directiva", "sentencia", "auto", "decreto",
    # English equivalents (for bilingual documents)
    "states", "union", "parliament", "council", "commission",
}


# ============================================================================
# CONTEXT EXCLUSION PATTERNS (FP-2, FP-3)
# Patterns that identify context where numeric patterns should NOT be detected
# as PII (e.g., DOI numbers are not postal codes, ORCID is not credit card).
# ============================================================================

CONTEXT_EXCLUSION_PATTERNS: List[Pattern] = [
    # DOI - Digital Object Identifier
    # Format: 10.XXXXX/... - the numeric part is NOT a postal code
    re.compile(r"(?:https?://)?(?:dx\.)?doi\.org/10\.\d+/[^\s]+", re.IGNORECASE),
    re.compile(r"doi:\s*10\.\d+/[^\s]+", re.IGNORECASE),

    # ORCID - Open Researcher and Contributor ID
    # Format: 0000-0000-0000-000X - NOT a credit card number
    re.compile(r"(?:https?://)?orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[0-9X]", re.IGNORECASE),
    re.compile(r"orcid:\s*\d{4}-\d{4}-\d{4}-\d{3}[0-9X]", re.IGNORECASE),

    # ISSN/ISBN - Publication identifiers, not PII
    re.compile(r"ISSN\s*:?\s*\d{4}-\d{3}[0-9X]", re.IGNORECASE),
    re.compile(r"ISBN\s*:?\s*[\d\-]{10,17}", re.IGNORECASE),

    # URLs - Numbers in URLs are not PII
    re.compile(r"https?://[^\s]+", re.IGNORECASE),
]


# ============================================================================
# YEAR-FOOTNOTE PATTERN (FP-1)
# Detects patterns where a year is concatenated with a footnote number.
# Example: "20237" = year 2023 + footnote 7
# ============================================================================

YEAR_FOOTNOTE_PATTERN = re.compile(r"\b((?:19|20)\d{2})(\d{1,2})\b")


# ============================================================================
# STRUCTURAL OVERRIDE PATTERNS (Errors 5-7 — post-merge reclassification)
# Deterministic patterns that should ALWAYS win over statistical models.
# Applied after merge to fix misclassifications by RoBERTa/spaCy.
# ============================================================================

_MONTH_NAMES = (
    r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto"
    r"|septiembre|octubre|noviembre|diciembre)"
)

# Patterns that definitively identify a DATE
STRUCTURAL_DATE_PATTERNS: list[re.Pattern] = [
    # "28 de octubre de 2025"
    re.compile(
        rf"^\d{{1,2}}\s+de\s+{_MONTH_NAMES}\s+de\s+\d{{4}}$",
        re.IGNORECASE,
    ),
    # "17 julio 2025"
    re.compile(
        rf"^\d{{1,2}}\s+{_MONTH_NAMES}\s+\d{{4}}$",
        re.IGNORECASE,
    ),
    # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    re.compile(r"^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}$"),
]

# Patterns that definitively identify a CASE_NUMBER
STRUCTURAL_CASE_NUMBER_PATTERNS: list[re.Pattern] = [
    # "548/2025-D7" — digits/year with alphanumeric suffix
    re.compile(r"^\d{1,5}/\d{4}-[A-Z0-9]{1,4}$", re.IGNORECASE),
    # "548/2025" — bare digits/year (only when NOT already a known entity)
    re.compile(r"^\d{1,5}/\d{4}$"),
]

# Context pattern: entity right after judicial number ("Nº 6 DE", "nº 3 de")
# Used to reclassify ORG -> LOCATION for city names in judicial headers
# Two patterns for judicial location context:
# 1. "Juzgado ... Nº X de/DE" (judicial organ with number)
# 2. "Audiencia Provincial de" (no number needed)
JUDICIAL_LOCATION_CONTEXT: list[re.Pattern] = [
    re.compile(
        r"(?:juzgado|sala)\s+.*?"
        r"n[ºúu]m?\.?\s*\d+\s+(?:de|DE)\s*$",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(?:audiencia\s+provincial|tribunal\s+superior)\s+(?:de|DE)\s*$",
        re.IGNORECASE,
    ),
]


# ============================================================================
# NER GARBAGE FILTERS (ML audit R2/R3 — post-merge false positive reduction)
# Source: plan_integracion_hallazgos_ml_a_produccion.md, Cambios 1-3
# Evidence: Reporte consolidado §3.3, §4.1, §5.1
# ============================================================================

# Whitelist: 1-word ORGs that are always valid (F2)
_ORG_WHITELIST_1WORD = frozenset({
    "ETA", "TEDH", "CNI", "CESID", "NATO", "OTAN", "ONU", "UE",
    "UNESCO", "UNICEF", "EUROPOL", "INTERPOL", "FRONTEX",
    "Batasuna", "Sortu", "Bildu", "Podemos", "Ciudadanos", "Vox",
    "TSJ", "CGPJ", "BOE", "BOCG", "TSJC", "TSJPV",
})


class CompositeNerAdapter(NerService):
    """
    Composite NER service that combines multiple NER adapters.

    Features:
    - Runs multiple NER engines in PARALLEL (asyncio.gather)
    - Intelligent merge with 3 phases:
      1. Contextual anchors (Spanish legal domain)
      2. Weighted voting (Regex=5, RoBERTa=2, SpaCy=1)
      3. GDPR risk-based tiebreaker
    - Token snapping for RoBERTa alignment
    - Nested entity handling (Matrioshka problem)
    """

    def __init__(
        self,
        adapters: list[NerService],
        dedup_overlap_threshold: float = 0.8,
        tie_threshold: float = 0.3,
        spacy_adapter: Any = None,
        enable_normalization: bool = True,
        enable_type_validation: bool = True,
        type_validator: EntityTypeValidator | None = None,
    ) -> None:
        """
        Initialize the composite NER adapter.

        Args:
            adapters: List of NER adapters to combine
            dedup_overlap_threshold: Threshold for considering spans as duplicates
            tie_threshold: Score difference below which triggers risk-based tiebreaker
            spacy_adapter: Optional SpacyNerAdapter for token snapping
            enable_normalization: Enable text normalization (Unicode, OCR) before NER
            enable_type_validation: Enable entity type validation with embeddings
            type_validator: Optional pre-configured EntityTypeValidator
        """
        self._adapters = adapters
        self._dedup_threshold = dedup_overlap_threshold
        self._tie_threshold = tie_threshold
        self._spacy_adapter = spacy_adapter
        self._spacy_doc_cache: Any = None  # Cached spaCy Doc for current text
        self._normalizer = TextNormalizer() if enable_normalization else None
        self._enable_type_validation = enable_type_validation
        self._type_validator = type_validator

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
        progress_callback: ProgressCallback | None = None,
    ) -> list[NerDetection]:
        """
        Detect entities using all adapters IN PARALLEL and merge results.

        Args:
            text: The text to analyze
            categories: Optional filter for specific categories
            min_confidence: Minimum confidence threshold
            progress_callback: Optional async callback for progress updates

        Returns:
            Merged list of detected entities
        """
        if not text or not text.strip():
            return []

        # Apply text normalization (Unicode, OCR robustness)
        # This handles: fullwidth chars, zero-width chars, Cyrillic homoglyphs
        if self._normalizer:
            text = self._normalizer.normalize(text)
            if not text:  # After normalization, text might become empty
                return []

        # Track progress across adapters
        # RoBERTa gets 0-80%, Regex gets 80-90%, Merge gets 90-100%
        adapter_ranges = [
            (0, 80),   # First adapter (usually RoBERTa - slow)
            (80, 90),  # Second adapter (usually Regex - fast)
        ]

        # Create adapter-specific callbacks that map to global progress
        def create_scoped_callback(
            adapter_idx: int,
        ) -> ProgressCallback | None:
            if not progress_callback:
                return None

            # Get range for this adapter
            if adapter_idx < len(adapter_ranges):
                start_pct, end_pct = adapter_ranges[adapter_idx]
            else:
                # Additional adapters share remaining range before merge
                start_pct, end_pct = 80, 90

            async def scoped_callback(current: int, total: int, info: str) -> None:
                if total > 0:
                    # Map adapter's 0-100 to its allocated range
                    adapter_progress = current / total
                    global_progress = start_pct + (end_pct - start_pct) * adapter_progress
                    await progress_callback(int(global_progress), 100, info)

            return scoped_callback

        # Check availability and create tasks for available adapters
        async def run_adapter(idx: int, adapter: NerService) -> list[NerDetection]:
            scoped_cb = create_scoped_callback(idx)
            try:
                if await adapter.is_available():
                    return await adapter.detect_entities(
                        text, categories, min_confidence, scoped_cb
                    )
            except Exception:
                pass
            return []

        # Run ALL adapters in PARALLEL using asyncio.gather
        results = await asyncio.gather(
            *[run_adapter(i, adapter) for i, adapter in enumerate(self._adapters)],
            return_exceptions=True
        )

        # Report merge phase
        if progress_callback:
            await progress_callback(90, 100, "Fusionando detecciones...")

        # Flatten results, ignoring exceptions
        all_detections: list[NerDetection] = []
        for result in results:
            if isinstance(result, list):
                all_detections.extend(result)

        # Get spaCy Doc for token snapping (if spacy_adapter available)
        spacy_doc = None
        if self._spacy_adapter:
            try:
                spacy_doc = await self._spacy_adapter.tokenize(text)
                self._spacy_doc_cache = spacy_doc
            except Exception:
                pass  # Continue without snapping

        # Apply token snapping to fix RoBERTa BPE issues
        if spacy_doc:
            all_detections = snap_all_detections(all_detections, spacy_doc)

        # Deduplicate and merge (pass text for contextual filtering)
        if progress_callback:
            await progress_callback(95, 100, f"Filtrando {len(all_detections)} detecciones...")

        merged = self._merge_detections(all_detections, text)

        if progress_callback:
            await progress_callback(100, 100, f"Detección completa: {len(merged)} entidades")

        return merged

    def _merge_detections(
        self, detections: list[NerDetection], text: str = ""
    ) -> list[NerDetection]:
        """
        Intelligent 3-phase merge for NER detections.

        Phase 1: Apply contextual anchors (deterministic rules)
        Phase 2: Weighted voting (Regex=5, RoBERTa=2, Presidio=1.5, SpaCy=1)
        Phase 3: GDPR risk-based tiebreaker when scores are close

        Args:
            detections: All detections from all adapters
            text: Original text (for contextual filtering and anchors)

        Returns:
            Merged list with intelligent category resolution
        """
        if not detections:
            return []

        # Step 1: Filter out false positives (legal references)
        filtered_detections = self._filter_false_positives(detections)

        # Step 2: Filter out stopwords and generic terms (Corrección #6, FP-4)
        filtered_detections = self._filter_stopwords(filtered_detections)

        # Step 2.5: Filter NER garbage (ML audit R2/R3: F1, F2, F3, F5, F6)
        filtered_detections = self._filter_ner_garbage(filtered_detections)

        # Step 3: Filter contextual false positives (DOI, ORCID, URLs) (FP-2, FP-3)
        if text:
            filtered_detections = self._filter_contextual_false_positives(
                filtered_detections, text
            )

        # Step 4: Filter year+footnote false positives (FP-1)
        if text:
            filtered_detections = self._filter_year_footnote_false_positives(
                filtered_detections, text
            )

        # Step 5: Remove nested entities (Matrioshka problem)
        non_nested = self._filter_nested_entities(filtered_detections)

        # Step 5.5: Entity type validation with embeddings
        # Rejects false positives (stopwords) and reclassifies mistyped entities
        if text and self._enable_type_validation:
            non_nested = self._apply_type_validation(non_nested, text)

        # Step 6: Apply PHASE 1 - Contextual Anchors
        # This forces categories based on Spanish legal domain context
        anchored_detections = []
        for det in non_nested:
            if text:
                det_anchored, _ = apply_contextual_anchors(det, text)
                anchored_detections.append(det_anchored)
            else:
                anchored_detections.append(det)

        # Step 7: Group overlapping detections for voting
        groups = self._group_overlapping_detections(anchored_detections)

        # Step 8: Apply PHASE 2+3 - Weighted Voting with Tiebreaker
        merged: list[NerDetection] = []
        for group in groups:
            if len(group) == 1:
                # Single detection - no voting needed
                merged.append(group[0])
            else:
                # Multiple detections for same span - use weighted voting
                winner = self._resolve_by_voting(group)
                merged.append(winner)

        # Step 8.5: Structural overrides (deterministic reclassification)
        merged = self._apply_structural_overrides(merged, text)

        # Step 8.6: Coreference boost for names confirmed with title
        if text:
            merged = self._boost_coreferenced_names(merged, text)

        # Step 9: Sort by position for consistent output
        merged.sort(key=lambda d: (d.span.start, d.span.end))

        return merged

    def _group_overlapping_detections(
        self, detections: list[NerDetection]
    ) -> list[list[NerDetection]]:
        """
        Group detections that overlap significantly.

        Detections with IoU >= threshold are grouped together
        for voting resolution.

        Args:
            detections: List of detections to group

        Returns:
            List of groups, each group contains overlapping detections
        """
        if not detections:
            return []

        # Sort by start position
        sorted_dets = sorted(detections, key=lambda d: d.span.start)

        groups: list[list[NerDetection]] = []
        used: set[int] = set()

        for i, det in enumerate(sorted_dets):
            if i in used:
                continue

            # Start a new group with this detection
            group = [det]
            used.add(i)

            # Find all detections that overlap with any member of the group
            changed = True
            while changed:
                changed = False
                for j, other in enumerate(sorted_dets):
                    if j in used:
                        continue
                    # Check overlap with any group member
                    for member in group:
                        overlap = self._calculate_overlap(other, member)
                        if overlap >= self._dedup_threshold:
                            group.append(other)
                            used.add(j)
                            changed = True
                            break

            groups.append(group)

        return groups

    def _resolve_by_voting(
        self, detections: list[NerDetection]
    ) -> NerDetection:
        """
        Resolve multiple overlapping detections using weighted voting.

        Uses the 3-phase merge strategy:
        - Phase 2: Weighted voting based on detector authority
        - Phase 3: GDPR risk-based tiebreaker for close scores

        Args:
            detections: Group of overlapping detections

        Returns:
            Single winning detection
        """
        # Get voting result (includes tiebreaker logic)
        result = weighted_vote_with_tiebreaker(detections)

        # Find the best detection with the winning category
        # Prefer longer spans and higher weighted scores
        candidates = [d for d in detections if d.category == result.category]

        if not candidates:
            # Fallback: use highest weighted score overall
            return max(detections, key=get_weighted_score)

        # Among candidates with winning category, pick best span
        # Prefer: longer span > higher weighted score
        best = max(
            candidates,
            key=lambda d: (
                d.span.end - d.span.start,  # Longer span
                get_weighted_score(d),       # Higher weighted score
            ),
        )

        return best

    def _apply_structural_overrides(
        self,
        detections: list[NerDetection],
        text: str = "",
    ) -> list[NerDetection]:
        """
        Post-merge structural overrides for deterministic patterns.

        Reclassifies entities whose text matches deterministic patterns
        that should ALWAYS override statistical model predictions.

        Fixes:
        - Error 5: Dates classified as ORG (e.g., "28 de octubre de 2025")
        - Error 6: Case numbers classified as ORG (e.g., "548/2025-D7")
        - Error 7: City names in judicial headers classified as ORG

        Args:
            detections: Merged detections after voting
            text: Original text for context analysis

        Returns:
            Detections with structural overrides applied
        """
        _date = PiiCategory.from_string("DATE").unwrap()
        _case_number = PiiCategory.from_string("CASE_NUMBER").unwrap()
        _location = PiiCategory.from_string("LOCATION").unwrap()

        result: list[NerDetection] = []

        for det in detections:
            value = det.value.strip()

            # Override 1: DATE patterns
            if det.category != _date:
                for pattern in STRUCTURAL_DATE_PATTERNS:
                    if pattern.match(value):
                        det = det.with_category(_date)
                        break

            # Override 2: CASE_NUMBER patterns
            if det.category != _case_number:
                for pattern in STRUCTURAL_CASE_NUMBER_PATTERNS:
                    if pattern.match(value):
                        det = det.with_category(_case_number)
                        break

            # Override 3: LOCATION in judicial headers
            # If entity is classified as ORG and context before it matches
            # a judicial organ + number pattern, reclassify as LOCATION
            if det.category == ORGANIZATION and text:
                context_start = max(0, det.span.start - 120)
                context_before = text[context_start:det.span.start]
                if any(p.search(context_before) for p in JUDICIAL_LOCATION_CONTEXT):
                    det = det.with_category(_location)

            result.append(det)

        return result

    def _boost_coreferenced_names(
        self,
        detections: list[NerDetection],
        text: str,
    ) -> list[NerDetection]:
        """
        Boost confidence of standalone names confirmed by titled occurrences.

        If "D. Teodoro García" appears with high confidence (≥0.90),
        all standalone "Teodoro" occurrences with low confidence (<0.75)
        are boosted to 0.85.

        This prevents false negatives when NER detects a bare first name
        with low confidence, but the same name was already confirmed
        with a formal title elsewhere in the document.

        Evidence: plan_produccion_mejoras_pendientes_v2.md §4 (Cambio 2)
        Impact: 36 fragile detections (NER-only, conf <0.70) gain backup

        Args:
            detections: Merged detections after structural overrides
            text: Original document text

        Returns:
            Detections with boosted confidence for coreferenced names
        """
        _title_re = re.compile(
            r'^(?:D\.|Dña\.|D\.ª|Dª\.?|Don|Doña|Sr\.|Sra\.)\s*',
            re.IGNORECASE,
        )

        # Step 1: Collect confirmed first names from high-confidence detections
        confirmed_first_names: set[str] = set()
        for det in detections:
            if det.category != PERSON_NAME or det.confidence.value < 0.90:
                continue
            clean = _title_re.sub('', det.value).strip()
            if not clean:
                continue
            first_name = clean.split()[0]
            if len(first_name) >= 3:
                confirmed_first_names.add(first_name.upper())

        if not confirmed_first_names:
            return detections

        # Step 2: Boost low-confidence standalone names that match
        boosted: list[NerDetection] = []
        for det in detections:
            if (
                det.category == PERSON_NAME
                and det.confidence.value < 0.75
                and det.value.strip().upper() in confirmed_first_names
            ):
                boosted.append(NerDetection(
                    category=det.category,
                    value=det.value,
                    span=det.span,
                    confidence=ConfidenceScore(0.85),
                    source=det.source,
                ))
            else:
                boosted.append(det)

        return boosted

    def _filter_nested_entities(
        self, detections: list[NerDetection]
    ) -> list[NerDetection]:
        """
        Remove nested (Matrioshka) entities.

        If entity A is fully contained within entity B of the same category,
        and B has sufficient confidence, discard A.

        Example:
            - RoBERTa detects: "Pedro Martínez de la Rosa" (PER, 0.95)
            - Regex detects: "Pedro" (PER, 1.0)
            - Result: Keep only "Pedro Martínez de la Rosa"

        Args:
            detections: List of detections to filter

        Returns:
            Filtered list with nested entities removed
        """
        if len(detections) <= 1:
            return detections

        # Sort by span length (longest first) to process larger entities first
        sorted_by_length = sorted(
            detections,
            key=lambda d: -(d.span.end - d.span.start)
        )

        kept: list[NerDetection] = []

        for detection in sorted_by_length:
            is_nested = False

            for larger in kept:
                # Check if detection is fully contained within larger
                if self._is_fully_contained(detection, larger):
                    # Same category or compatible categories
                    if self._are_compatible_categories(detection.category, larger.category):
                        # Larger entity has sufficient confidence (>= 0.7)
                        if larger.confidence.value >= 0.7:
                            is_nested = True
                            break

            if not is_nested:
                kept.append(detection)

        return kept

    def _is_fully_contained(self, small: NerDetection, large: NerDetection) -> bool:
        """
        Check if 'small' entity is fully contained within 'large' entity.

        Args:
            small: Potentially contained entity
            large: Potentially containing entity

        Returns:
            True if small is fully within large
        """
        return (
            large.span.start <= small.span.start and
            small.span.end <= large.span.end and
            # Make sure they're not identical
            not (large.span.start == small.span.start and large.span.end == small.span.end)
        )

    def _are_compatible_categories(
        self, cat1: PiiCategory, cat2: PiiCategory
    ) -> bool:
        """
        Check if two categories are compatible for nested entity filtering.

        Compatible means we can safely discard one in favor of the other.

        Args:
            cat1: First category
            cat2: Second category

        Returns:
            True if categories are compatible
        """
        # Same category is always compatible
        if cat1 == cat2:
            return True

        # Define compatible category groups (using imported constants)
        compatible_groups = [
            # Person-related
            {PERSON_NAME},
            # Location-related
            {LOCATION, ADDRESS},
            # ID documents
            {DNI_NIE, PASSPORT},
            # Financial
            {IBAN, BANK_ACCOUNT, CREDIT_CARD},
        ]

        for group in compatible_groups:
            if cat1 in group and cat2 in group:
                return True

        return False

    def _filter_false_positives(
        self, detections: list[NerDetection]
    ) -> list[NerDetection]:
        """
        Filter out false positive detections.

        Removes detections that match known false positive patterns
        such as court case references (Sentencia 61/2019), law numbers, etc.

        These are public references that should NOT be anonymized.

        Args:
            detections: List of detections to filter

        Returns:
            Filtered list with false positives removed
        """
        filtered: list[NerDetection] = []

        for detection in detections:
            value = detection.value.strip()

            # Check against all false positive patterns
            is_false_positive = False
            for pattern in FALSE_POSITIVE_PATTERNS:
                if pattern.match(value):
                    is_false_positive = True
                    break

            if not is_false_positive:
                filtered.append(detection)

        return filtered

    def _filter_stopwords(
        self, detections: list[NerDetection]
    ) -> list[NerDetection]:
        """
        Filter out detections that are stopwords or generic terms.

        Removes detections that match:
        - Common Spanish pronouns, articles (SPANISH_STOPWORDS)
        - Short common words (COMMON_SHORT_WORDS)
        - Generic terms that should never be anonymized (GENERIC_TERMS_WHITELIST)

        This prevents false positives like:
        - "Quien" detected as organization
        - "Estado" detected as organization
        - "Unión" detected as organization

        Args:
            detections: List of detections to filter

        Returns:
            Filtered list with stopwords and generic terms removed

        Traceability:
            - Corrección #6: Falso positivo "Quien"
            - FP-4: Términos genéricos como ORG
            - PLAN_CORRECCION_AUDITORIA.md
        """
        filtered: list[NerDetection] = []

        for detection in detections:
            value = detection.value.strip()
            value_lower = value.lower()

            # Check exact stopword match
            if value_lower in SPANISH_STOPWORDS:
                continue

            # Check generic terms whitelist (FP-4)
            if value_lower in GENERIC_TERMS_WHITELIST:
                continue

            # Check if platform name misclassified as PERSON_NAME (Error 3)
            if detection.category == PERSON_NAME:
                if value_lower in PLATFORM_NAMES_BLOCKLIST:
                    continue

            # Check if it's a short common word (1-5 chars, single word)
            if len(value_lower) <= 5 and " " not in value_lower:
                if value_lower in COMMON_SHORT_WORDS:
                    continue

                # Additional check: single short words that are all alphabetic
                # and appear to be articles/pronouns (very conservative)
                if value_lower.isalpha() and len(value_lower) <= 3:
                    # Skip very short words unless they could be initials
                    # (all uppercase like "FBI", "CIA")
                    if not value.isupper():
                        continue

            filtered.append(detection)

        return filtered

    def _filter_ner_garbage(
        self, detections: list[NerDetection]
    ) -> list[NerDetection]:
        """
        Filter NER garbage detections from RoBERTa.

        Applies post-filters discovered during ML audit (4 rounds on 5 real
        documents, 926K chars). These catch false positives that pass through
        the model but are clearly not valid entities.

        Filters:
        F1. ≤2 alphabetic chars (PDF fragments: "E", "V", "Gu")
        F2. 1-word ORG with confidence <0.85, not in whitelist
        F3. Starts/ends with quotes or truncated preposition ("de"/"del"/"de la")
        F5. Starts with lowercase letter (PDF truncation: "hiza", "izcaya")
        F6. Starts with punctuation (garbage: ".\\nSegismundo")

        Note: F4 (gazetteer surnames) not applicable — production has no gazetteer.
        Note: F7 (generic ORG blacklist) already covered by _filter_stopwords()
              which uses .lower() matching against GENERIC_TERMS_WHITELIST.

        Evidence: plan_integracion_hallazgos_ml_a_produccion.md §5 Cambios 1-2
        """
        filtered: list[NerDetection] = []

        for det in detections:
            if det.source != "roberta":
                filtered.append(det)
                continue

            text_s = det.value.strip()
            if not text_s:
                continue

            # F1: ≤2 alphabetic chars — PDF fragment artifacts
            alpha_count = sum(1 for c in text_s if c.isalpha())
            if alpha_count <= 2:
                continue

            # F3: starts with quote or ends with truncated preposition
            if (
                text_s.startswith('"') or text_s.startswith("'")
                or text_s.endswith(" de") or text_s.endswith(" del")
                or text_s.endswith(" de la")
            ):
                continue

            # F5: starts with lowercase — PDF truncation
            if text_s[0].islower():
                continue

            # F6: starts with punctuation — NER garbage
            if not text_s[0].isalnum():
                continue

            # F2: 1-word ORG from NER, low confidence, not in whitelist
            text_normalized = " ".join(text_s.split())
            if (
                det.category == ORGANIZATION
                and " " not in text_normalized
                and text_normalized not in _ORG_WHITELIST_1WORD
                and det.confidence.value < 0.85
            ):
                continue

            filtered.append(det)

        return filtered

    def _filter_contextual_false_positives(
        self,
        detections: list[NerDetection],
        text: str,
    ) -> list[NerDetection]:
        """
        Filter detections that fall within contextual exclusion zones.

        Identifies zones in text that contain patterns like DOI, ORCID, URLs
        where numeric components should NOT be detected as PII.

        Example:
            - "doi.org/10.18239/..." - "18239" is NOT a postal code
            - "orcid.org/0000-0003-..." - NOT a credit card

        Args:
            detections: List of detections to filter
            text: Original text to analyze for exclusion zones

        Returns:
            Filtered list with contextual false positives removed

        Traceability:
            - FP-2: DOI como código postal
            - FP-3: ORCID como tarjeta
        """
        if not text:
            return detections

        # Find all exclusion zones in the text
        exclusion_zones: list[tuple[int, int]] = []
        for pattern in CONTEXT_EXCLUSION_PATTERNS:
            for match in pattern.finditer(text):
                exclusion_zones.append((match.start(), match.end()))

        if not exclusion_zones:
            return detections

        # Filter detections that fall within exclusion zones
        filtered: list[NerDetection] = []
        for detection in detections:
            det_start = detection.span.start
            det_end = detection.span.end

            # Check if detection overlaps with any exclusion zone
            is_in_exclusion_zone = False
            for zone_start, zone_end in exclusion_zones:
                # Detection is inside or overlaps with exclusion zone
                if det_start >= zone_start and det_end <= zone_end:
                    is_in_exclusion_zone = True
                    break
                # Partial overlap - also exclude
                if det_start < zone_end and det_end > zone_start:
                    is_in_exclusion_zone = True
                    break

            if not is_in_exclusion_zone:
                filtered.append(detection)

        return filtered

    def _filter_year_footnote_false_positives(
        self,
        detections: list[NerDetection],
        text: str,
    ) -> list[NerDetection]:
        """
        Filter detections of year+footnote concatenations.

        Detects patterns like "20237" where:
        - "2023" is a year (1900-2099)
        - "7" is a footnote superscript

        These should NOT be detected as postal codes (5 digits starting with 0-5).

        Args:
            detections: List of detections to filter
            text: Original text to analyze

        Returns:
            Filtered list with year+footnote false positives removed

        Traceability:
            - FP-1: Años + notas al pie como CP
        """
        if not text:
            return detections

        # Find year+footnote zones
        year_footnote_zones: set[tuple[int, int]] = set()
        for match in YEAR_FOOTNOTE_PATTERN.finditer(text):
            year_str = match.group(1)
            year = int(year_str)
            # Valid year range: 1900-2099
            if 1900 <= year <= 2099:
                year_footnote_zones.add((match.start(), match.end()))

        if not year_footnote_zones:
            return detections

        # Categories that are commonly false positives with year+footnote
        problematic_categories = {"POSTAL_CODE", "DATE", "PHONE"}

        filtered: list[NerDetection] = []
        for detection in detections:
            # Only filter specific categories prone to this issue
            if detection.category.value not in problematic_categories:
                filtered.append(detection)
                continue

            det_start = detection.span.start
            det_end = detection.span.end

            # Check if detection matches a year+footnote zone
            is_year_footnote = False
            for zone_start, zone_end in year_footnote_zones:
                # Exact match or containment
                if det_start >= zone_start and det_end <= zone_end:
                    is_year_footnote = True
                    break

            if not is_year_footnote:
                filtered.append(detection)

        return filtered

    def _apply_type_validation(
        self,
        detections: list[NerDetection],
        text: str,
    ) -> list[NerDetection]:
        """
        Apply entity type validation using embedding similarity.

        Uses EntityTypeValidator to:
        - REJECT false positives (stopwords classified as entities)
        - RECLASSIFY mistyped entities (e.g., person_name→organization)
        - FLAG uncertain cases for HITL review

        Args:
            detections: List of detections after nested filtering
            text: Original text for context extraction

        Returns:
            Validated list with corrected types and rejected false positives

        Traceability:
            - Research: ml/docs/reports/2026-02-05_embeddings_entity_type_disambiguation.md
            - Papers: NER Retriever (arXiv 2509.04011), CEPTNER (KBS 2024)
        """
        # Lazy init validator on first use
        if self._type_validator is None:
            try:
                self._type_validator = EntityTypeValidator()
            except Exception as e:
                logger.warning(f"Could not initialize EntityTypeValidator: {e}")
                self._enable_type_validation = False
                return detections

        validated: list[NerDetection] = []

        for det in detections:
            result = self._type_validator.validate(
                entity_text=det.value,
                entity_type=det.category.value,
                full_text=text,
                start=det.span.start,
                end=det.span.end,
            )

            if result.action == ValidationAction.REJECT:
                logger.debug(
                    f"Type validator REJECTED: '{det.value}' "
                    f"({det.category.value}) - {result.reason}"
                )
                continue

            if result.action == ValidationAction.RECLASSIFY:
                logger.info(
                    f"Type validator RECLASSIFIED: '{det.value}' "
                    f"{det.category.value} → {result.validated_type} "
                    f"({result.reason})"
                )
                category_result = PiiCategory.from_string(result.validated_type)
                if isinstance(category_result, Ok):
                    det = det.with_category(category_result.value)
                else:
                    logger.warning(
                        f"Invalid reclassification target: {result.validated_type}"
                    )

            elif result.action == ValidationAction.FLAG_HITL:
                logger.info(
                    f"Type validator FLAGGED for HITL: '{det.value}' "
                    f"({det.category.value}) - {result.reason}"
                )
                # Keep detection but lower confidence to push into AMBER zone
                det = NerDetection(
                    category=det.category,
                    value=det.value,
                    span=det.span,
                    confidence=ConfidenceScore(min(det.confidence.value, 0.70)),
                    source=det.source,
                )

            validated.append(det)

        return validated

    def _calculate_overlap(self, a: NerDetection, b: NerDetection) -> float:
        """
        Calculate the overlap ratio between two detections using IoU.

        Args:
            a: First detection
            b: Second detection

        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        start_a, end_a = a.span.start, a.span.end
        start_b, end_b = b.span.start, b.span.end

        # Calculate intersection
        intersection_start = max(start_a, start_b)
        intersection_end = min(end_a, end_b)
        intersection = max(0, intersection_end - intersection_start)

        # Calculate union
        union = (end_a - start_a) + (end_b - start_b) - intersection

        if union == 0:
            return 0.0

        return intersection / union

    async def is_available(self) -> bool:
        """Check if at least one adapter is available."""
        # Check all adapters in parallel
        results = await asyncio.gather(
            *[adapter.is_available() for adapter in self._adapters],
            return_exceptions=True
        )
        return any(r is True for r in results)

    async def get_model_info(self) -> dict:
        """Get information about all adapters."""
        # Get info from all adapters in parallel
        results = await asyncio.gather(
            *[adapter.get_model_info() for adapter in self._adapters],
            return_exceptions=True
        )

        adapter_infos = []
        for result in results:
            if isinstance(result, Exception):
                adapter_infos.append({"error": str(result)})
            else:
                adapter_infos.append(result)

        return {
            "type": "composite",
            "adapter_count": len(self._adapters),
            "parallel_execution": True,
            "nested_entity_handling": True,
            "adapters": adapter_infos,
        }

    def add_adapter(self, adapter: NerService) -> None:
        """Add an adapter to the composite."""
        self._adapters.append(adapter)

    def remove_adapter(self, adapter: NerService) -> None:
        """Remove an adapter from the composite."""
        if adapter in self._adapters:
            self._adapters.remove(adapter)
