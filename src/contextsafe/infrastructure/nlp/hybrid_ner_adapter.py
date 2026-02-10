"""
Hybrid NER adapter combining LLM and Presidio detection.

Architecture: Option B (Pre-Presidio LLM)
1. LLM (Qwen via Ollama) provides semantic detection
2. Presidio validates and enhances with regex patterns
3. Results are merged with deduplication

Traceability:
- Port: ports.NerService
- IMPLEMENTATION_PLAN.md Phase 5
"""

from __future__ import annotations

from typing import Any

from contextsafe.application.ports import NerDetection, NerService
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)


class HybridNerAdapter(NerService):
    """
    Hybrid NER combining LLM semantic detection with Presidio pattern matching.

    Flow:
    1. LLM analyzes text for semantic PII (names, organizations, context)
    2. Presidio scans for pattern-based PII (DNI, IBAN, phone, etc.)
    3. Results are merged, with overlapping spans resolved

    This provides:
    - Better semantic understanding from LLM
    - Reliable pattern detection from Presidio
    - Higher recall than either alone
    """

    def __init__(
        self,
        llm_adapter: NerService,
        presidio_adapter: NerService,
        llm_weight: float = 0.6,
        presidio_weight: float = 0.8,
    ) -> None:
        """
        Initialize hybrid adapter.

        Args:
            llm_adapter: LLM-based NER service (OllamaNerAdapter)
            presidio_adapter: Presidio-based NER service (PresidioNerAdapter)
            llm_weight: Confidence multiplier for LLM detections
            presidio_weight: Confidence multiplier for Presidio detections
        """
        self._llm = llm_adapter
        self._presidio = presidio_adapter
        self._llm_weight = llm_weight
        self._presidio_weight = presidio_weight

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
    ) -> list[NerDetection]:
        """
        Detect entities using both LLM and Presidio.

        Args:
            text: Text to analyze
            categories: Optional category filter
            min_confidence: Minimum confidence threshold

        Returns:
            Merged list of detections from both sources
        """
        if not text or not text.strip():
            return []

        # Run both detectors
        llm_available = await self._llm.is_available()

        llm_detections: list[NerDetection] = []
        if llm_available:
            try:
                llm_detections = await self._llm.detect_entities(
                    text, categories, min_confidence
                )
            except Exception as e:
                print(f"[HybridNER] LLM detection failed: {e}")

        # Always run Presidio as fallback/enhancement
        presidio_detections = await self._presidio.detect_entities(
            text, categories, min_confidence
        )

        # Merge results
        merged = self._merge_detections(
            llm_detections, presidio_detections, text
        )

        # Apply minimum confidence filter
        return [d for d in merged if d.confidence.value >= min_confidence]

    def _merge_detections(
        self,
        llm_detections: list[NerDetection],
        presidio_detections: list[NerDetection],
        text: str,
    ) -> list[NerDetection]:
        """
        Merge detections from both sources with smart deduplication.

        Strategy:
        - For overlapping spans: keep higher confidence
        - For same text, different category: keep both (user decides)
        - Boost confidence when both agree
        """
        all_detections: list[NerDetection] = []
        used_spans: dict[tuple[int, int], NerDetection] = {}

        # Process LLM detections first (semantic priority)
        for det in llm_detections:
            span_key = (det.span.start, det.span.end)
            adjusted_conf = min(det.confidence.value * self._llm_weight, 1.0)

            # Create adjusted detection
            conf_result = ConfidenceScore.create(adjusted_conf)
            if conf_result.is_ok():
                adjusted_det = NerDetection(
                    category=det.category,
                    value=det.value,
                    span=det.span,
                    confidence=conf_result.unwrap(),
                )
                used_spans[span_key] = adjusted_det

        # Process Presidio detections
        for det in presidio_detections:
            span_key = (det.span.start, det.span.end)
            adjusted_conf = min(det.confidence.value * self._presidio_weight, 1.0)

            if span_key in used_spans:
                existing = used_spans[span_key]

                # Same span, check if same category
                if existing.category == det.category:
                    # Both agree! Boost confidence
                    boosted_conf = min(
                        max(existing.confidence.value, adjusted_conf) + 0.1, 1.0
                    )
                    conf_result = ConfidenceScore.create(boosted_conf)
                    if conf_result.is_ok():
                        used_spans[span_key] = NerDetection(
                            category=det.category,
                            value=det.value,
                            span=det.span,
                            confidence=conf_result.unwrap(),
                        )
                else:
                    # Different category - keep higher confidence
                    if adjusted_conf > existing.confidence.value:
                        conf_result = ConfidenceScore.create(adjusted_conf)
                        if conf_result.is_ok():
                            used_spans[span_key] = NerDetection(
                                category=det.category,
                                value=det.value,
                                span=det.span,
                                confidence=conf_result.unwrap(),
                            )
            else:
                # Check for overlapping spans
                overlaps = False
                for (s, e), existing in list(used_spans.items()):
                    if self._spans_overlap(det.span.start, det.span.end, s, e):
                        overlaps = True
                        # Keep the one with higher confidence
                        if adjusted_conf > existing.confidence.value:
                            del used_spans[(s, e)]
                            conf_result = ConfidenceScore.create(adjusted_conf)
                            if conf_result.is_ok():
                                used_spans[span_key] = NerDetection(
                                    category=det.category,
                                    value=det.value,
                                    span=det.span,
                                    confidence=conf_result.unwrap(),
                                )
                        break

                if not overlaps:
                    conf_result = ConfidenceScore.create(adjusted_conf)
                    if conf_result.is_ok():
                        used_spans[span_key] = NerDetection(
                            category=det.category,
                            value=det.value,
                            span=det.span,
                            confidence=conf_result.unwrap(),
                        )

        # Sort by position
        all_detections = sorted(used_spans.values(), key=lambda d: d.span.start)
        return all_detections

    def _spans_overlap(self, s1: int, e1: int, s2: int, e2: int) -> bool:
        """Check if two spans overlap."""
        return not (e1 <= s2 or e2 <= s1)

    async def is_available(self) -> bool:
        """Check if at least one adapter is available."""
        llm_ok = await self._llm.is_available()
        presidio_ok = await self._presidio.is_available()
        return llm_ok or presidio_ok

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about both adapters."""
        llm_info = await self._llm.get_model_info()
        presidio_info = await self._presidio.get_model_info()

        return {
            "type": "hybrid",
            "architecture": "pre-presidio-llm",
            "llm": llm_info,
            "presidio": presidio_info,
            "weights": {
                "llm": self._llm_weight,
                "presidio": self._presidio_weight,
            },
        }
