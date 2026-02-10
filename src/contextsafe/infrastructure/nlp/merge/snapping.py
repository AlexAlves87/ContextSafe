"""
Token snapping for RoBERTa span alignment.

RoBERTa uses BPE tokenization which can cut words incorrectly.
This module aligns RoBERTa detections to proper word boundaries
using spaCy's tokenization as ground truth.

Example:
    RoBERTa detects: "an Carlos" (missed "Ju")
    spaCy tokens: ["Juan", "Carlos"]
    After snapping: "Juan Carlos"

Traceability:
- Design: docs/plans/2026-02-02-intelligent-merge-spacy-design.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import TextSpan

if TYPE_CHECKING:
    pass  # spaCy types would go here


# Sources that need snapping (BPE tokenization issues)
SOURCES_NEEDING_SNAPPING = {"roberta"}


def _spans_overlap(
    span_start: int,
    span_end: int,
    token_start: int,
    token_end: int,
) -> bool:
    """Check if two spans overlap."""
    return not (span_end <= token_start or span_start >= token_end)


def snap_to_tokens(
    detection: NerDetection,
    spacy_doc: Any,
) -> NerDetection:
    """
    Align detection span to complete spaCy tokens.

    Only applies to sources that use BPE tokenization (roberta).
    Expands the span to cover complete tokens that overlap with
    the original detection.

    Args:
        detection: The NER detection to snap
        spacy_doc: spaCy Doc object with tokenization

    Returns:
        Detection with span aligned to token boundaries
    """
    # Only snap sources with BPE tokenization issues
    if detection.source not in SOURCES_NEEDING_SNAPPING:
        return detection

    det_start = detection.span.start
    det_end = detection.span.end

    # Find all tokens that overlap with the detection span
    overlapping_tokens = []
    for token in spacy_doc:
        token_start = token.idx
        token_end = token.idx + len(token.text)

        if _spans_overlap(det_start, det_end, token_start, token_end):
            overlapping_tokens.append(token)

    if not overlapping_tokens:
        # No overlapping tokens found - keep original
        return detection

    # Calculate expanded span covering all overlapping tokens
    new_start = min(t.idx for t in overlapping_tokens)
    new_end = max(t.idx + len(t.text) for t in overlapping_tokens)

    # Check if span actually changed
    if new_start == det_start and new_end == det_end:
        return detection

    # Get the new value from the document
    new_value = spacy_doc.text[new_start:new_end]

    # Create new span
    span_result = TextSpan.create(new_start, new_end, new_value)
    if span_result.is_err():
        # If span creation fails, keep original
        return detection

    return detection.with_span(span_result.unwrap(), new_value)


def snap_all_detections(
    detections: list[NerDetection],
    spacy_doc: Any,
) -> list[NerDetection]:
    """
    Apply token snapping to all detections that need it.

    Args:
        detections: List of detections from various sources
        spacy_doc: spaCy Doc object with tokenization

    Returns:
        List of detections with spans aligned to token boundaries
    """
    return [snap_to_tokens(det, spacy_doc) for det in detections]
