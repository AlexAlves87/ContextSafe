"""
Intelligent merge components for NER detection.

This module provides:
- Contextual anchors for Spanish legal domain
- Weighted voting with tiebreaker
- Token snapping for RoBERTa alignment

Traceability:
- Design: docs/plans/2026-02-02-intelligent-merge-spacy-design.md
"""

from contextsafe.infrastructure.nlp.merge.anchors import (
    apply_contextual_anchors,
    PERSON_ANCHORS,
    LOCATION_ANCHORS,
    ORG_ANCHORS,
)
from contextsafe.infrastructure.nlp.merge.voting import (
    weighted_vote_with_tiebreaker,
    VotingResult,
    DETECTOR_WEIGHTS,
    RISK_PRIORITY,
)
from contextsafe.infrastructure.nlp.merge.snapping import snap_to_tokens

__all__ = [
    # Anchors
    "apply_contextual_anchors",
    "PERSON_ANCHORS",
    "LOCATION_ANCHORS",
    "ORG_ANCHORS",
    # Voting
    "weighted_vote_with_tiebreaker",
    "VotingResult",
    "DETECTOR_WEIGHTS",
    "RISK_PRIORITY",
    # Snapping
    "snap_to_tokens",
]
