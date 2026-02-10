"""
Spanish date recognizer.

Recognizes dates in Spanish formats:
- Full dates: "17 de julio de 2025"
- Abbreviated: "17/07/2025", "17-07-2025"
- With month names: "enero", "febrero", etc.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml#pii_categories.DATE
"""

from __future__ import annotations

import re
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class SpanishDateRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish dates.

    Handles:
    - Written format: "17 de julio de 2025"
    - Numeric formats: "17/07/2025", "17-07-2025"
    - Mixed formats: "17 julio 2025"
    """

    # Spanish month names
    MONTHS = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]

    # Month pattern
    MONTH_PATTERN = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"

    PATTERNS = [
        # Pattern 1: Full written date (e.g., "17 de julio de 2025")
        Pattern(
            "DATE_WRITTEN_FULL",
            r"\b(\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4})\b",
            0.95,
        ),
        # Pattern 2: Written without "de" (e.g., "17 julio 2025")
        Pattern(
            "DATE_WRITTEN_SHORT",
            r"\b(\d{1,2}\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{4})\b",
            0.90,
        ),
        # Pattern 3: Day and month only (e.g., "17 de julio")
        Pattern(
            "DATE_DAY_MONTH",
            r"\b(\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre))\b",
            0.70,
        ),
        # Pattern 4: Numeric DD/MM/YYYY
        Pattern(
            "DATE_NUMERIC_SLASH",
            r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
            0.85,
        ),
        # Pattern 5: Numeric DD-MM-YYYY
        Pattern(
            "DATE_NUMERIC_DASH",
            r"\b(\d{1,2}-\d{1,2}-\d{4})\b",
            0.85,
        ),
        # Pattern 6: Numeric DD.MM.YYYY
        Pattern(
            "DATE_NUMERIC_DOT",
            r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b",
            0.85,
        ),
        # Pattern 7: Context "fecha de" + date
        Pattern(
            "DATE_WITH_CONTEXT",
            r"fecha\s+(?:de\s+)?(\d{1,2}[\s/\-\.]+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|\d{1,2})[\s/\-\.]+(?:de\s+)?\d{4})",
            0.95,
        ),
        # Pattern 8: Year only in specific context (e.g., "nacido en 1985")
        Pattern(
            "YEAR_BIRTH_CONTEXT",
            r"(?:nacid[oa]|nacimiento)\s+(?:en|el)?\s*(\d{4})\b",
            0.80,
        ),
    ]

    CONTEXT = [
        "fecha", "nacimiento", "nacido", "nacida", "dia", "día",
        "celebrado", "firmado", "expedido", "emitido", "otorgado",
        "vencimiento", "caducidad", "vigencia", "notificada",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_DATE",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """Validate date format."""
        clean = pattern_text.strip().lower()

        # Try to extract day and validate
        day_match = re.match(r"^(\d{1,2})", clean)
        if day_match:
            day = int(day_match.group(1))
            if day < 1 or day > 31:
                return False

        # Try to extract month (numeric)
        month_match = re.search(r"/(\d{1,2})/|^(\d{1,2})[/\-\.](\d{1,2})", clean)
        if month_match:
            month_str = month_match.group(1) or month_match.group(3)
            if month_str:
                month = int(month_str)
                if month < 1 or month > 12:
                    return False

        # Check for valid month name
        for month in self.MONTHS:
            if month in clean:
                return True

        # If it's numeric format, validate structure
        if re.match(r"^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}$", clean):
            return True

        return True
