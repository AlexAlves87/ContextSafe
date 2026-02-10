"""
Legal titles recognizer.

Detects names followed by legal professional titles.

Traceability:
- Contract: CNT-T3-LEGAL-TITLES-001
- Bug Fix: Privacy Leak (Cargos Legales)

Examples detected:
- "Agustín Pardillo Hernández, Letrado del Gabinete Técnico"
- "María García López, Secretario Judicial"
- "D. Juan Pérez Sánchez, Procurador de los Tribunales"
"""

from __future__ import annotations

import re
from typing import List, Tuple

from contextsafe.application.ports import NerDetection, NerService
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)


# Legal professional titles that trigger name detection
LEGAL_TITLES = [
    # Judicial roles
    r"(?:Letrad[oa]|Abogad[oa]|Procurador(?:a)?)\s+(?:del?|de\s+la)\s+[\w\s]+",
    r"Secretari[oa]\s+(?:Judicial|del?\s+(?:Juzgado|Tribunal))",
    r"Magistrad[oa](?:\s+(?:Juez|Ponente))?",
    r"(?:Juez|Jueza)(?:\s+(?:de\s+lo\s+[\w]+|Titular|Sustitut[oa]))?",
    r"Fiscal(?:\s+(?:Jefe|General|Adjunt[oa]))?",
    # Administrative legal roles
    r"Registrador(?:a)?(?:\s+de\s+la\s+Propiedad)?",
    r"Notari[oa](?:\s+(?:de|del)\s+[\w\s]+)?",
    r"Perit[oa](?:\s+(?:Judicial|Técnic[oa]))?",
    # Generic legal references
    r"Letrad[oa]\s+de\s+(?:la\s+)?(?:Administración|Seguridad Social)",
    r"Catedrático\s+de\s+Derecho",
]

# Pattern to capture name before title
# Matches: "D./Dña. Name Surname [Surname], Title"
# Or: "Name Surname [Surname], Title"
NAME_BEFORE_TITLE_PATTERN = re.compile(
    r"(?:D\.?ª?|Dña\.?|Don|Doña)\s*"  # Optional honorific
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})"  # Name (2-4 words)
    r"\s*,?\s*"  # Optional comma
    r"(" + "|".join(LEGAL_TITLES) + r")",  # Legal title
    re.IGNORECASE | re.UNICODE
)

# Simpler pattern for names directly followed by title
NAME_TITLE_DIRECT_PATTERN = re.compile(
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})"  # Name
    r"\s*,\s*"  # Comma separator
    r"(" + "|".join(LEGAL_TITLES) + r")",  # Legal title
    re.IGNORECASE | re.UNICODE
)


class LegalTitlesRecognizer(NerService):
    """
    Recognizer for names associated with legal professional titles.

    This recognizer specifically addresses the privacy leak issue where
    names of legal professionals were not being detected because spaCy
    didn't recognize them as person names when followed by their title.

    Strategy:
    - Look for legal titles (Letrado, Magistrado, Procurador, etc.)
    - Extract the name that precedes the title
    - Mark only the NAME as PII (not the title itself)
    """

    def __init__(self) -> None:
        """Initialize the recognizer."""
        self._patterns = [
            (NAME_BEFORE_TITLE_PATTERN, 0.92),
            (NAME_TITLE_DIRECT_PATTERN, 0.90),
        ]

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
    ) -> list[NerDetection]:
        """
        Detect names of legal professionals in text.

        Args:
            text: The text to analyze
            categories: Optional filter for specific categories
            min_confidence: Minimum confidence threshold

        Returns:
            List of detected person names
        """
        if not text or not text.strip():
            return []

        # Get PERSON_NAME category
        person_cat_result = PiiCategory.from_string("PERSON_NAME")
        if person_cat_result.is_err():
            return []

        person_category = person_cat_result.unwrap()

        # Filter by category if specified
        if categories and person_category not in categories:
            return []

        detections: list[NerDetection] = []
        seen_spans: set[Tuple[int, int]] = set()

        for pattern, base_confidence in self._patterns:
            if base_confidence < min_confidence:
                continue

            for match in pattern.finditer(text):
                # Group 1 is the name, Group 2 is the title
                name = match.group(1)
                if not name:
                    continue

                # Find the exact position of the name within the match
                name_start = match.start() + match.group(0).find(name)
                name_end = name_start + len(name)

                # Skip duplicates
                span_key = (name_start, name_end)
                if span_key in seen_spans:
                    continue
                seen_spans.add(span_key)

                # Create span with name text
                name_text = name.strip()
                span_result = TextSpan.create(name_start, name_end, name_text)
                if span_result.is_err():
                    continue

                # Create confidence
                conf_result = ConfidenceScore.create(base_confidence)
                if conf_result.is_err():
                    continue

                detections.append(
                    NerDetection(
                        category=person_category,
                        value=name_text,
                        span=span_result.unwrap(),
                        confidence=conf_result.unwrap(),
                    )
                )

        return detections

    async def is_available(self) -> bool:
        """Always available (pure regex)."""
        return True

    async def get_model_info(self) -> dict:
        """Get information about this recognizer."""
        return {
            "type": "regex",
            "name": "legal_titles_recognizer",
            "description": "Detects names of legal professionals by their titles",
            "pattern_count": len(self._patterns),
        }
