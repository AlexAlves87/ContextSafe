"""
SpaCy NER adapter.

Uses spaCy for traditional NLP-based named entity recognition.

Traceability:
- Contract: CNT-T3-SPACY-ADAPTER-001
- Port: ports.NerService
"""

from __future__ import annotations

from typing import Any

from contextsafe.application.ports import NerDetection, NerService
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)


# Mapping from spaCy entity labels to PII categories
SPACY_TO_PII_MAPPING = {
    # Person names
    "PER": "PERSON_NAME",
    "PERSON": "PERSON_NAME",
    # Organizations
    "ORG": "ORGANIZATION",
    # Locations (GPE = Geo-Political Entity, LOC = Location)
    # Use LOCATION for voting system compatibility
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "FAC": "ADDRESS",  # Facilities are more specific addresses
    # Ignore miscellaneous
    "MISC": None,
}


class SpacyNerAdapter(NerService):
    """
    NER service using spaCy models.

    Provides fast, CPU-based NER for common entity types.
    """

    def __init__(
        self,
        model_name: str = "es_core_news_lg",
        confidence_default: float = 0.85,
    ) -> None:
        """
        Initialize the spaCy NER adapter.

        Args:
            model_name: Name of the spaCy model to load
            confidence_default: Default confidence score for spaCy entities
        """
        self._model_name = model_name
        self._confidence_default = confidence_default
        self._nlp: Any = None
        self._is_loaded = False

    async def _ensure_loaded(self) -> None:
        """Ensure the spaCy model is loaded."""
        if self._is_loaded:
            return

        try:
            import spacy

            self._nlp = spacy.load(self._model_name)
            self._is_loaded = True
        except ImportError:
            raise RuntimeError("spaCy not installed. Run: pip install spacy")
        except OSError:
            raise RuntimeError(
                f"spaCy model '{self._model_name}' not found. "
                f"Run: python -m spacy download {self._model_name}"
            )

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
    ) -> list[NerDetection]:
        """
        Detect entities in text using spaCy.

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

        doc = self._nlp(text)
        detections: list[NerDetection] = []

        for ent in doc.ents:
            # Map spaCy label to PII category
            pii_category_str = SPACY_TO_PII_MAPPING.get(ent.label_)
            if pii_category_str is None:
                continue

            # Create PII category
            category_result = PiiCategory.from_string(pii_category_str)
            if category_result.is_err():
                continue
            category = category_result.unwrap()

            # Filter by requested categories
            if categories and category not in categories:
                continue

            # Create span with entity text
            entity_text = ent.text
            span_result = TextSpan.create(ent.start_char, ent.end_char, entity_text)
            if span_result.is_err():
                continue

            # Create confidence (spaCy doesn't provide confidence, use default)
            conf_result = ConfidenceScore.create(self._confidence_default)
            if conf_result.is_err():
                continue

            # Skip if below threshold
            if self._confidence_default < min_confidence:
                continue

            detections.append(
                NerDetection(
                    category=category,
                    value=entity_text,
                    span=span_result.unwrap(),
                    confidence=conf_result.unwrap(),
                    source="spacy",
                )
            )

        return detections

    async def is_available(self) -> bool:
        """Check if spaCy model is loaded."""
        try:
            await self._ensure_loaded()
            return self._is_loaded
        except Exception:
            return False

    async def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        info = {
            "type": "spacy",
            "model_name": self._model_name,
            "is_loaded": self._is_loaded,
        }

        if self._is_loaded and self._nlp:
            info["pipeline"] = self._nlp.pipe_names
            info["lang"] = self._nlp.lang

        return info

    async def tokenize(self, text: str) -> Any:
        """
        Tokenize text and return spaCy Doc.

        Used by token snapping to align RoBERTa detections
        to proper word boundaries.

        Args:
            text: Text to tokenize

        Returns:
            spaCy Doc object with tokens
        """
        await self._ensure_loaded()
        return self._nlp(text)
