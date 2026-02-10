"""
Weighted voting with GDPR risk-based tiebreaker.

Implements Phase 2 and Phase 3 of the intelligent merge:
- Phase 2: Weighted voting based on detector authority
- Phase 3: Tiebreaker using GDPR risk priority

Traceability:
- Design: docs/plans/2026-02-02-intelligent-merge-spacy-design.md
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from contextsafe.application.ports import NerDetection
from contextsafe.domain.shared.value_objects import PiiCategory


# =============================================================================
# DETECTOR WEIGHTS
# =============================================================================
# Authority weights based on detector nature

DETECTOR_WEIGHTS: dict[str, float] = {
    # Regex: Absolute truth for fixed formats (DNI, IBAN, etc.)
    "regex": 5.0,
    # RoBERTa: Deep contextual understanding, trained on Spanish
    "roberta": 2.0,
    # Presidio: Specific recognizers with good precision
    "presidio": 1.5,
    # SpaCy: Generalist base, good tokenizer
    "spacy": 1.0,
    # Unknown source
    "unknown": 0.5,
}

# Category-specific bonuses for detectors
DETECTOR_CATEGORY_BONUS: dict[tuple[str, str], float] = {
    # Regex is infallible for these formats
    ("regex", "DNI_NIE"): 3.0,
    ("regex", "IBAN"): 3.0,
    ("regex", "PHONE"): 2.0,
    ("regex", "EMAIL"): 3.0,
    ("regex", "DATE"): 1.5,
    ("regex", "CREDIT_CARD"): 2.5,
    ("regex", "SOCIAL_SECURITY"): 2.5,
    ("regex", "LICENSE_PLATE"): 2.0,
    # RoBERTa is better for semantic entities
    ("roberta", "PERSON_NAME"): 1.0,
    ("roberta", "ORGANIZATION"): 0.5,
    ("roberta", "LOCATION"): 0.5,
    # SpaCy is robust for Spanish names (morphology)
    ("spacy", "PERSON_NAME"): 1.0,
    ("spacy", "LOCATION"): 0.3,
    # Presidio has good date recognition
    ("presidio", "DATE"): 0.5,
}


# =============================================================================
# GDPR RISK PRIORITY
# =============================================================================
# Higher = more risky to miss (should favor anonymizing)

RISK_PRIORITY: dict[str, int] = {
    "PERSON_NAME": 100,      # Highest risk - personal identity
    "DNI_NIE": 95,           # National ID
    "MEDICAL_RECORD": 90,    # Sensitive health data
    "SOCIAL_SECURITY": 88,   # Social security number
    "PHONE": 85,             # Contact info
    "EMAIL": 80,             # Contact info
    "IBAN": 75,              # Financial
    "BANK_ACCOUNT": 70,      # Financial
    "CREDIT_CARD": 70,       # Financial
    "ADDRESS": 65,           # Location
    "PASSPORT": 60,          # ID document
    "ORGANIZATION": 50,      # Less risky
    "LOCATION": 40,          # Generic location
    "DATE": 30,              # Temporal
    "LICENSE_PLATE": 25,     # Vehicle
    "POSTAL_CODE": 20,       # Partial location
    "MISC": 10,              # Miscellaneous
}

# Threshold for considering a "technical tie"
# If score difference < TIE_THRESHOLD, use risk priority
TIE_THRESHOLD: float = 0.3


# =============================================================================
# VOTING RESULT
# =============================================================================

@dataclass
class VotingResult:
    """Result of weighted voting."""

    category: PiiCategory
    total_score: float
    votes: list[tuple[str, float]]  # [(detector, score), ...]
    was_tie_broken: bool = False
    runner_up: PiiCategory | None = None
    runner_up_score: float = 0.0


# =============================================================================
# WEIGHTED VOTING
# =============================================================================

def weighted_vote_with_tiebreaker(
    detections: list[NerDetection],
) -> VotingResult:
    """
    Calculate winning category using weighted voting with tiebreaker.

    Phase 2: Calculates weighted score per category
        Score = sum(confidence * (weight + bonus))

    Phase 3: If difference between 1st and 2nd < TIE_THRESHOLD,
        uses GDPR risk priority to decide.

    Args:
        detections: Detections for the same span from different detectors

    Returns:
        VotingResult with winning category and metadata
    """
    if not detections:
        raise ValueError("No detections to vote on")

    # Accumulate scores per category
    category_scores: dict[str, float] = defaultdict(float)
    category_votes: dict[str, list[tuple[str, float]]] = defaultdict(list)

    for det in detections:
        source = det.source
        category = det.category.value
        confidence = det.confidence.value

        # Calculate weighted score
        base_weight = DETECTOR_WEIGHTS.get(source, 0.5)
        bonus = DETECTOR_CATEGORY_BONUS.get((source, category), 0.0)
        weighted_score = confidence * (base_weight + bonus)

        category_scores[category] += weighted_score
        category_votes[category].append((source, weighted_score))

    # Sort categories by score (descending)
    sorted_categories = sorted(
        category_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    if len(sorted_categories) == 1:
        # Only one category - clear winner
        winner_cat = sorted_categories[0][0]
        return VotingResult(
            category=PiiCategory.from_string(winner_cat).unwrap(),
            total_score=sorted_categories[0][1],
            votes=category_votes[winner_cat],
            was_tie_broken=False,
            runner_up=None,
            runner_up_score=0.0,
        )

    # Multiple categories - check for tie
    first_cat, first_score = sorted_categories[0]
    second_cat, second_score = sorted_categories[1]
    score_diff = first_score - second_score

    if score_diff >= TIE_THRESHOLD:
        # Clear winner
        return VotingResult(
            category=PiiCategory.from_string(first_cat).unwrap(),
            total_score=first_score,
            votes=category_votes[first_cat],
            was_tie_broken=False,
            runner_up=PiiCategory.from_string(second_cat).unwrap(),
            runner_up_score=second_score,
        )

    # === TECHNICAL TIE: Apply Phase 3 (Risk Priority) ===
    first_priority = RISK_PRIORITY.get(first_cat, 0)
    second_priority = RISK_PRIORITY.get(second_cat, 0)

    if first_priority >= second_priority:
        winner_cat = first_cat
        runner_up_cat = second_cat
        winner_score = first_score
        runner_up_score = second_score
    else:
        winner_cat = second_cat
        runner_up_cat = first_cat
        winner_score = second_score
        runner_up_score = first_score

    return VotingResult(
        category=PiiCategory.from_string(winner_cat).unwrap(),
        total_score=winner_score,
        votes=category_votes[winner_cat],
        was_tie_broken=True,
        runner_up=PiiCategory.from_string(runner_up_cat).unwrap(),
        runner_up_score=runner_up_score,
    )


def get_weighted_score(detection: NerDetection) -> float:
    """
    Calculate weighted score for a single detection.

    Useful for sorting or comparing individual detections.

    Args:
        detection: The detection to score

    Returns:
        Weighted score
    """
    source = detection.source
    category = detection.category.value
    confidence = detection.confidence.value

    base_weight = DETECTOR_WEIGHTS.get(source, 0.5)
    bonus = DETECTOR_CATEGORY_BONUS.get((source, category), 0.0)

    return confidence * (base_weight + bonus)
