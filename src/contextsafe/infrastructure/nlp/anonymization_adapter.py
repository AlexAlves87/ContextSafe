"""
Anonymization service adapter.

Implements anonymization using consistent alias generation with
project-scoped glossaries.

Traceability:
- Contract: CNT-T3-ANONYMIZATION-ADAPTER-001
- Port: AnonymizationService
- IMPLEMENTATION_PLAN.md Phase 5
- ERROR 2: Date normalization for chronological coherence
- Bug Fix: Corrección #5 - Inconsistencia de entidades (PLAN_CORRECCION_AUDITORIA.md)
"""

from __future__ import annotations

import copy
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Optional

from contextsafe.application.ports import (
    AnonymizationResult,
    AnonymizationService,
    EntityReplacement,
    NerDetection,
)
from contextsafe.domain.anonymization.services.normalization import (
    normalize_pii_value,
    values_match,
    find_matching_value,
)

if TYPE_CHECKING:
    from contextsafe.infrastructure.nlp.strategies.base import AnonymizationStrategy


# ============================================================================
# DATE PARSING AND NORMALIZATION (ERROR 2)
# ============================================================================

# Spanish month names to numbers
SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def parse_spanish_date(date_str: str) -> Optional[datetime]:
    """
    Parse Spanish date strings into datetime objects.

    Supports formats:
    - "15 de marzo de 2024"
    - "15/03/2024"
    - "2024-03-15"
    - "15-03-2024"

    Returns None if parsing fails.
    """
    date_str = date_str.strip().lower()

    # Format: "15 de marzo de 2024"
    match = re.match(
        r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})",
        date_str,
        re.IGNORECASE
    )
    if match:
        day, month_name, year = match.groups()
        month = SPANISH_MONTHS.get(month_name.lower())
        if month:
            try:
                return datetime(int(year), month, int(day))
            except ValueError:
                pass

    # Format: "15/03/2024" or "15-03-2024"
    match = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
    if match:
        day, month, year = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            pass

    # Format: "2024-03-15" or "2024/03/15" (ISO format)
    match = re.match(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", date_str)
    if match:
        year, month, day = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            pass

    return None


def get_chronological_alias(index: int) -> str:
    """
    Generate a chronological alias using letters A-Z, then AA-ZZ, etc.

    This preserves temporal order in anonymized documents:
    - Fecha_A < Fecha_B < Fecha_C in chronological order

    Args:
        index: 0-based chronological order

    Returns:
        Alias suffix (A, B, ..., Z, AA, AB, ...)
    """
    result = ""
    index += 1  # 1-based for calculation
    while index > 0:
        index -= 1
        result = chr(ord('A') + (index % 26)) + result
        index //= 26
    return result


# Alias prefixes by category (must match PiiCategoryEnum values)
# Source: controlled_vocabulary.yaml#vocabulary.pii_categories
ALIAS_PREFIXES = {
    # Person & Organization
    "PERSON_NAME": "Persona",
    "ORGANIZATION": "Org",
    # Location
    "ADDRESS": "Dir",
    "LOCATION": "Lugar",
    "POSTAL_CODE": "CP",        # Spanish postal codes
    # Identity Documents
    "DNI_NIE": "ID",            # Covers DNI, NIE, NIF, CIF
    "PASSPORT": "Pasaporte",
    # Contact
    "PHONE": "Tel",
    "EMAIL": "Email",
    # Financial
    "BANK_ACCOUNT": "Cuenta",
    "IBAN": "IBAN",             # Spanish IBAN codes
    "CREDIT_CARD": "Tarjeta",
    # Dates
    "DATE": "Fecha",
    # Health & Vehicle
    "MEDICAL_RECORD": "Historia",
    "LICENSE_PLATE": "Matricula",
    "SOCIAL_SECURITY": "NSS",
    # Professional & Legal (new for FUGA 1/2)
    "PROFESSIONAL_ID": "IdProf",
    "CASE_NUMBER": "Proc",      # Procedure numbers
    # Digital & Platform (new for FUGA 3)
    "PLATFORM": "Plataforma",
    "IP_ADDRESS": "IP",
}


class InMemoryAnonymizationAdapter(AnonymizationService):
    """
    Anonymization service using in-memory glossary.

    Features:
    - Consistent alias generation per project
    - Sequential numbering by category
    - Support for controlled vocabulary prefixes
    """

    def __init__(self) -> None:
        """Initialize the anonymization adapter."""
        # Glossary structure: {project_id: {category: {original: alias}}}
        self._glossaries: dict[str, dict[str, dict[str, str]]] = {}
        # Counters structure: {project_id: {category: next_number}}
        self._counters: dict[str, dict[str, int]] = {}

    @staticmethod
    def _is_wsl() -> bool:
        """Detect if running in WSL (Windows Subsystem for Linux)."""
        try:
            with open("/proc/version", "r") as f:
                return "microsoft" in f.read().lower()
        except Exception:
            return False

    @staticmethod
    def _get_windows_host_ip() -> str:
        """Get the Windows host IP from WSL."""
        import subprocess
        try:
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Parse: "default via 172.27.48.1 dev eth0"
            for part in result.stdout.split():
                if part.startswith("172.") or part.startswith("192.") or part.startswith("10."):
                    return part
        except Exception:
            pass
        return "localhost"

    def _get_ollama_url(self) -> str:
        """
        Get the Ollama URL, auto-detecting WSL environment.

        In WSL, connects to Windows host IP since Ollama runs on Windows.
        In native Linux/Windows, uses localhost.
        """
        if self._is_wsl():
            host_ip = self._get_windows_host_ip()
            return f"http://{host_ip}:11434"
        return "http://localhost:11434"

    # Categories that should be merged when adjacent (Corrección #1)
    # If an ADDRESS and POSTAL_CODE are adjacent, keep only the longer one
    MERGE_ADJACENT_CATEGORIES = {
        ("ADDRESS", "POSTAL_CODE"),
        ("ADDRESS", "LOCATION"),
        ("POSTAL_CODE", "ADDRESS"),
        ("LOCATION", "ADDRESS"),
    }

    # Maximum gap (in characters) to consider entities as "adjacent"
    MAX_ADJACENT_GAP = 10

    def _remove_overlapping_detections(
        self, detections: list[NerDetection]
    ) -> list[NerDetection]:
        """
        Remove overlapping AND adjacent detections.

        CRITICAL: Nested/adjacent detections cause text corruption during replacement!
        If detection A contains or is adjacent to detection B, we must choose ONE.

        Strategy (Corrección #1):
        1. Sort ALL detections by span length (longest first)
        2. For each detection, check if it overlaps with any already selected
        3. For related categories (ADDRESS/POSTAL_CODE), also check adjacency
        4. If overlap OR adjacent: skip (keep the longer/first one)
        5. If no overlap: add to result

        This ensures:
        - "c/ Calle nº 45, 08635 Ciudad" keeps EITHER the full address OR the CP
        - Adjacent ADDRESS + POSTAL_CODE don't cause concatenation
        - No nested detections that would corrupt text during replacement
        """
        if not detections:
            return []

        # Sort by span length (longest first), then by confidence
        sorted_dets = sorted(
            detections,
            key=lambda d: (
                -(d.span.end - d.span.start),  # Longer spans first
                -d.confidence.value,            # Higher confidence first
            ),
        )

        result: list[NerDetection] = []
        for detection in sorted_dets:
            # Check if this detection overlaps or is adjacent to ANY already selected
            should_skip = False
            for selected in result:
                # Check strict overlap
                if self._spans_overlap(detection.span, selected.span):
                    should_skip = True
                    break

                # Check adjacency for related categories (Corrección #1)
                if self._should_merge_adjacent(detection, selected):
                    should_skip = True
                    break

            if not should_skip:
                result.append(detection)

        return result

    def _spans_overlap(self, span1, span2) -> bool:
        """Check if two spans overlap."""
        return not (span1.end <= span2.start or span1.start >= span2.end)

    def _should_merge_adjacent(self, det1: NerDetection, det2: NerDetection) -> bool:
        """
        Check if two detections are adjacent and should be merged.

        Returns True if:
        1. Categories are in MERGE_ADJACENT_CATEGORIES
        2. Spans are adjacent (gap <= MAX_ADJACENT_GAP characters)

        This prevents concatenation when ADDRESS and POSTAL_CODE are detected
        separately but should be treated as a single entity.
        """
        cat1 = det1.category.value
        cat2 = det2.category.value

        # Check if categories should be merged when adjacent
        cats = (cat1, cat2)
        if cats not in self.MERGE_ADJACENT_CATEGORIES:
            return False

        # Calculate gap between spans
        # Gap is positive if spans don't overlap, negative if they do
        if det1.span.end <= det2.span.start:
            gap = det2.span.start - det1.span.end
        elif det2.span.end <= det1.span.start:
            gap = det1.span.start - det2.span.end
        else:
            # Overlapping - handled by _spans_overlap
            return False

        return gap <= self.MAX_ADJACENT_GAP

    def _get_strategy(self, level: str, compute_mode: "ComputeMode | None" = None) -> "AnonymizationStrategy":
        """
        Get the appropriate strategy for the anonymization level.

        Args:
            level: BASIC, INTERMEDIATE, or ADVANCED
            compute_mode: Optional compute mode (GPU/CPU). Defaults to CPU.

        Returns:
            The strategy instance for that level
        """
        from contextsafe.infrastructure.nlp.strategies import (
            MaskingStrategy,
            PseudonymStrategy,
            SyntheticStrategy,
        )
        from contextsafe.application.compute_mode import ComputeMode

        if compute_mode is None:
            compute_mode = ComputeMode.CPU

        level_upper = level.upper()

        if level_upper == "BASIC":
            return MaskingStrategy()
        elif level_upper == "ADVANCED":
            import os

            # Get compute mode to determine GPU usage for Ollama
            use_gpu = compute_mode == ComputeMode.GPU

            # Ollama URL: configurable via environment variable
            # For WSL2 connecting to Windows Ollama, auto-detect Windows host IP
            ollama_url = os.environ.get("OLLAMA_HOST", "")
            if not ollama_url:
                # Auto-detect: if running in WSL, use Windows host IP
                ollama_url = self._get_ollama_url()
            if not ollama_url.startswith("http"):
                ollama_url = f"http://{ollama_url}"

            # Model: configurable via environment variable
            ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2:1.5b")

            # SyntheticStrategy uses Ollama for realistic synthetic data
            # Pass self (adapter) for fallback alias generation when Ollama fails
            return SyntheticStrategy(
                ollama_url=ollama_url,
                model=ollama_model,
                use_gpu=use_gpu,
                adapter=self,
            )
        else:  # INTERMEDIATE (default)
            return PseudonymStrategy(adapter=self)

    async def anonymize_text(
        self,
        text: str,
        detections: list[NerDetection],
        project_id: str,
        level: str = "INTERMEDIATE",
        progress_callback: Optional[Callable] = None,
        compute_mode: "ComputeMode | None" = None,
    ) -> AnonymizationResult:
        """
        Anonymize text by replacing detected entities.

        Uses the Strategy pattern to handle different anonymization levels:
        - BASIC: Asterisks (MaskingStrategy)
        - INTERMEDIATE: Pseudonyms (PseudonymStrategy)
        - ADVANCED: Synthetic names via LLM (SyntheticStrategy)

        Processes detections in reverse order (by position) to maintain
        correct offsets during replacement.

        Args:
            progress_callback: Optional async callback(current, total, entity_info)
                              for progress updates during processing.
        """
        if not text:
            return AnonymizationResult(
                original_text=text,
                anonymized_text=text,
                replacements=[],
            )

        if not detections:
            return AnonymizationResult(
                original_text=text,
                anonymized_text=text,
                replacements=[],
            )

        # Get strategy for this level
        strategy = self._get_strategy(level, compute_mode=compute_mode)

        # Remove overlapping detections - keep highest confidence for each span
        filtered_detections = self._remove_overlapping_detections(detections)

        # Sort detections by start position (descending) for reverse replacement
        sorted_detections = sorted(
            filtered_detections,
            key=lambda d: d.span.start,
            reverse=True,
        )

        anonymized = text
        replacements: list[EntityReplacement] = []
        total_detections = len(sorted_detections)

        for i, detection in enumerate(sorted_detections):
            # Use strategy to generate replacement
            # For Level 3 (ADVANCED), this includes LLM calls to Ollama
            result = await strategy.generate_replacement(detection, project_id)

            # Report progress AFTER processing - reflects COMPLETED work
            # This ensures progress bar shows actual completion, not queued work
            if progress_callback:
                entity_info = f"{detection.category.value}: {result.replacement[:25]}..."
                await progress_callback(i + 1, total_detections, entity_info)

            # Replace in text
            start = detection.span.start
            end = detection.span.end
            anonymized = anonymized[:start] + result.replacement + anonymized[end:]

            # Record replacement
            replacements.append(
                EntityReplacement(
                    category=result.category,
                    original_value=result.original,
                    alias=result.replacement,
                    start_offset=start,
                    end_offset=end,
                    confidence=detection.confidence.value,
                )
            )

        # Final progress update
        if progress_callback:
            await progress_callback(total_detections, total_detections, "Completado")

        # Reverse to get chronological order
        replacements.reverse()

        return AnonymizationResult(
            original_text=text,
            anonymized_text=anonymized,
            replacements=replacements,
        )

    async def get_or_create_alias(
        self,
        category: str,
        original_value: str,
        project_id: str,
        level: str = "INTERMEDIATE",
    ) -> str:
        """
        Get existing alias or create a new one.

        Uses format: {prefix}_{number} (e.g., Persona_001, DNI_001)

        Special handling:
        - PERSON_NAME/ORGANIZATION: Fuzzy matching for partial names
        - DATE:
          - INTERMEDIATE: Numeric aliases (Fecha_001, Fecha_002)
          - ADVANCED: Date shifting to preserve temporal intervals

        Args:
            level: Anonymization level (INTERMEDIATE or ADVANCED)
        """
        # Initialize project glossary if needed
        if project_id not in self._glossaries:
            self._glossaries[project_id] = {}
            self._counters[project_id] = {}

        project_glossary = self._glossaries[project_id]
        project_counters = self._counters[project_id]

        # Initialize category if needed
        if category not in project_glossary:
            project_glossary[category] = {}
            project_counters[category] = 1

        # ================================================================
        # UNIFIED NORMALIZATION (Corrección #5)
        # Uses centralized normalization for ALL categories to ensure
        # consistency. The same entity always gets the same alias.
        # ================================================================

        # Check if already mapped using centralized normalization
        existing_alias = find_matching_value(original_value, project_glossary[category], category)
        if existing_alias:
            return existing_alias

        # Special handling for DATE: also compare parsed values
        if category == "DATE":
            parsed_new = parse_spanish_date(original_value)
            if parsed_new:
                for orig, alias in project_glossary[category].items():
                    parsed_orig = parse_spanish_date(orig)
                    if parsed_orig and parsed_orig == parsed_new:
                        return alias

        # ================================================================
        # DATE CATEGORY: Level-dependent handling
        # - INTERMEDIATE: Numeric aliases (Fecha_001, Fecha_002) like other categories
        # - ADVANCED: Date shifting to preserve temporal intervals
        # ================================================================
        if category == "DATE" and level.upper() == "ADVANCED":
            return await self._get_or_create_date_alias(
                original_value, project_id, project_glossary, project_counters
            )
        # For INTERMEDIATE level, DATE falls through to numeric alias below

        # Create new alias for non-date categories
        prefix = ALIAS_PREFIXES.get(category, category[:3].upper())
        number = project_counters[category]
        alias = f"{prefix}_{number:03d}"

        # Store mapping
        project_glossary[category][original_value] = alias
        project_counters[category] = number + 1

        return alias

    async def _get_or_create_date_alias(
        self,
        date_str: str,
        project_id: str,
        project_glossary: dict,
        project_counters: dict,
    ) -> str:
        """
        Create date aliases using DATE SHIFTING (Corrección #3).

        Date shifting applies a UNIFORM delta to all dates in a project,
        preserving the temporal intervals between them.

        Example: If delta = +730 days (2 years):
            "13 de enero de 2026" → "13 de enero de 2028"
            "12 de octubre de 2025" → "12 de octubre de 2027"
            Interval between dates is PRESERVED.

        IMPORTANT: Same parsed date = same alias, regardless of string format.
        "5 de diciembre de 2025" and "05/12/2025" get the SAME shifted date.

        Traceability:
        - Corrección #3: Fechas aleatorias sin date shifting
        - PLAN_CORRECCION_AUDITORIA.md
        """
        from contextsafe.domain.anonymization.services.date_shifter import get_date_shifter

        # Initialize date tracking if needed
        if "_date_parsed" not in project_glossary:
            project_glossary["_date_parsed"] = {}  # {date_str: datetime}
        if "DATE" not in project_glossary:
            project_glossary["DATE"] = {}

        date_parsed = project_glossary["_date_parsed"]

        # Check if this exact string already has an alias
        if date_str in project_glossary["DATE"]:
            return project_glossary["DATE"][date_str]

        # Try to parse the date
        parsed = parse_spanish_date(date_str)

        if parsed is None:
            # Unparseable date: use numeric alias as fallback
            prefix = ALIAS_PREFIXES.get("DATE", "Fecha")
            number = project_counters.get("DATE", 1)
            alias = f"{prefix}_{number:03d}"
            project_glossary["DATE"][date_str] = alias
            project_counters["DATE"] = number + 1
            return alias

        # Check if this PARSED date already exists (handles different formats)
        # "5 de diciembre de 2025" should match "05/12/2025"
        for existing_str, existing_dt in date_parsed.items():
            if existing_dt == parsed:
                # Same date already exists - return its alias
                return project_glossary["DATE"][existing_str]

        # ================================================================
        # DATE SHIFTING (Corrección #3)
        # Apply uniform delta to preserve temporal intervals
        # ================================================================
        shifter = get_date_shifter()
        shifted_date_str = shifter.format_shifted_date(date_str, project_id)

        # Store mapping: original → shifted date string
        date_parsed[date_str] = parsed
        project_glossary["DATE"][date_str] = shifted_date_str

        return shifted_date_str

    async def get_glossary(
        self,
        project_id: str,
    ) -> dict[str, dict[str, str]]:
        """Get the full alias glossary for a project (deep copy)."""
        return copy.deepcopy(self._glossaries.get(project_id, {}))

    def clear_project_glossary(self, project_id: str) -> None:
        """Clear glossary for a project (for testing)."""
        self._glossaries.pop(project_id, None)
        self._counters.pop(project_id, None)


# Global instance for simple use
_anonymizer: InMemoryAnonymizationAdapter | None = None


def get_anonymization_service() -> InMemoryAnonymizationAdapter:
    """Get or create the global anonymization service."""
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = InMemoryAnonymizationAdapter()
    return _anonymizer
