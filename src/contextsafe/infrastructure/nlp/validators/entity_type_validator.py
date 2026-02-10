"""
Entity Type Validator using Embedding Similarity.

Validates and corrects NER entity type assignments by comparing entity embeddings
against pre-computed type centroids. Fixes misclassifications like:
- "Alejandro Alvarez" classified as ORGANIZATION instead of PERSON_NAME
- "10/10/2025" classified as ORGANIZATION instead of DATE
- Common words ("Finalmente", "Quien") incorrectly classified as entities

Architecture:
    NER Output → Extract entity+context → Embed → Compare centroids → Validate/Correct

References:
    - NER Retriever: arXiv 2509.04011 (2025)
    - CEPTNER: Knowledge-Based Systems (2024)
    - Multilingual E5: arXiv 2402.05672 (2024)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class ValidationAction(str, Enum):
    """Action taken by the validator."""

    KEEP = "KEEP"  # Keep original NER type
    RECLASSIFY = "RECLASSIFY"  # Change to different type
    FLAG_HITL = "FLAG_HITL"  # Flag for human review
    REJECT = "REJECT"  # Not a valid entity (false positive)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of entity type validation."""

    original_type: str
    validated_type: str
    action: ValidationAction
    confidence: float
    similarity_scores: dict[str, float]
    reason: str


# Categories that can be validated with embeddings
VALIDATABLE_CATEGORIES = frozenset({
    "PERSON_NAME",
    "ORGANIZATION",
    "LOCATION",
    "ADDRESS",
    "DATE",
})

# Categories to skip (structured data validated by regex)
SKIP_VALIDATION_CATEGORIES = frozenset({
    "DNI_NIE",
    "PASSPORT",
    "PHONE",
    "EMAIL",
    "IBAN",
    "BANK_ACCOUNT",
    "CREDIT_CARD",
    "POSTAL_CODE",
    "LICENSE_PLATE",
    "SOCIAL_SECURITY",
    "MEDICAL_RECORD",
    "IP_ADDRESS",
    "CASE_NUMBER",
    "PROFESSIONAL_ID",
    "ID_SUPPORT",
    "NIG",
    "ECLI",
    "CSV",
    "HEALTH_ID",
    "CADASTRAL_REF",
    "EMPLOYER_ID",
    "PLATFORM",
})

# Spanish stopwords that should NEVER be entities
SPANISH_STOPWORDS = frozenset({
    # Pronouns
    "quien", "quién", "quienes", "quiénes", "cual", "cuál", "cuales", "cuáles",
    "que", "qué", "donde", "dónde", "cuando", "cuándo", "como", "cómo",
    # Common words incorrectly capitalized
    "finalmente", "terminaba", "mientras", "aunque", "porque", "entonces",
    "además", "también", "todavía", "siempre", "nunca", "apenas",
    "estado", "manera", "forma", "parte", "hecho", "caso", "tiempo",
    # Verbs commonly capitalized at sentence start
    "siendo", "habiendo", "teniendo", "estando", "haciendo",
    "dice", "dijo", "señala", "indica", "establece", "dispone",
    # Legal terms that aren't PII
    "sentencia", "recurso", "demanda", "escrito", "auto", "providencia",
})


class EntityTypeValidator:
    """
    Validates NER entity types using embedding similarity to type centroids.

    Uses multilingual-e5-large model to generate embeddings and compares
    against pre-computed centroids for each entity type.

    Args:
        model_name: HuggingFace model for embeddings.
        centroids_path: Path to JSON file with pre-computed centroids.
        reclassify_threshold: Minimum similarity to consider reclassification.
        margin_threshold: Minimum margin over original type to reclassify.
        hitl_margin: When margin is below this, flag for human review.
        context_window: Number of characters around entity to include.
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        centroids_path: Path | None = None,
        reclassify_threshold: float = 0.75,
        margin_threshold: float = 0.10,
        hitl_margin: float = 0.05,
        context_window: int = 50,
    ) -> None:
        self.model_name = model_name
        self.reclassify_threshold = reclassify_threshold
        self.margin_threshold = margin_threshold
        self.hitl_margin = hitl_margin
        self.context_window = context_window

        self._model = None
        self._centroids: dict[str, NDArray[np.float32]] = {}
        self._initialized = False

        # Default centroids path
        if centroids_path is None:
            self._centroids_path = (
                Path(__file__).parent.parent.parent.parent.parent.parent
                / "ml"
                / "models"
                / "type_centroids.json"
            )
        else:
            self._centroids_path = centroids_path

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of model and centroids."""
        if self._initialized:
            return True

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            start = time.time()
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded in {time.time() - start:.2f}s")

            # Load centroids if file exists
            if self._centroids_path.exists():
                self._load_centroids()
            else:
                logger.warning(
                    f"Centroids file not found: {self._centroids_path}. "
                    "Validator will only filter stopwords."
                )

            self._initialized = True
            return True

        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to initialize EntityTypeValidator: {e}")
            return False

    def _load_centroids(self) -> None:
        """Load pre-computed centroids from JSON file."""
        logger.info(f"Loading centroids from: {self._centroids_path}")
        with open(self._centroids_path) as f:
            data = json.load(f)

        for category, centroid_list in data.items():
            self._centroids[category] = np.array(centroid_list, dtype=np.float32)

        logger.info(f"Loaded centroids for {len(self._centroids)} categories")

    def _embed(self, text: str) -> NDArray[np.float32]:
        """Generate embedding for text with E5 query prefix."""
        # E5 models require "query:" prefix for semantic search
        input_text = f"query: {text}"
        embedding = self._model.encode(
            [input_text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return embedding.astype(np.float32)

    def _extract_context(
        self,
        text: str,
        start: int,
        end: int,
    ) -> str:
        """Extract entity with surrounding context."""
        context_start = max(0, start - self.context_window)
        context_end = min(len(text), end + self.context_window)
        return text[context_start:context_end]

    def _compute_similarities(
        self,
        embedding: NDArray[np.float32],
    ) -> dict[str, float]:
        """Compute cosine similarity to all centroids."""
        similarities = {}
        for category, centroid in self._centroids.items():
            # Embeddings are normalized, so dot product = cosine similarity
            similarity = float(np.dot(embedding, centroid))
            similarities[category] = similarity
        return similarities

    def validate(
        self,
        entity_text: str,
        entity_type: str,
        full_text: str,
        start: int,
        end: int,
    ) -> ValidationResult:
        """
        Validate an entity's type assignment.

        Args:
            entity_text: The detected entity text.
            entity_type: The NER-assigned category.
            full_text: The full document text for context.
            start: Start offset of entity.
            end: End offset of entity.

        Returns:
            ValidationResult with action and corrected type if applicable.
        """
        # Step 1: Check stopwords (fast, no model needed)
        if entity_text.lower().strip() in SPANISH_STOPWORDS:
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.REJECT,
                confidence=1.0,
                similarity_scores={},
                reason=f"'{entity_text}' is a Spanish stopword/common word",
            )

        # Step 2: Skip structured data categories (validated by regex)
        if entity_type in SKIP_VALIDATION_CATEGORIES:
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.KEEP,
                confidence=1.0,
                similarity_scores={},
                reason=f"Category '{entity_type}' validated by regex patterns",
            )

        # Step 3: Check if we can validate this category
        if entity_type not in VALIDATABLE_CATEGORIES:
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.KEEP,
                confidence=0.5,
                similarity_scores={},
                reason=f"Category '{entity_type}' not in validatable set",
            )

        # Step 4: Initialize model (lazy)
        if not self._ensure_initialized():
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.KEEP,
                confidence=0.5,
                similarity_scores={},
                reason="Validator not initialized (model not available)",
            )

        # Step 5: Check if we have centroids
        if not self._centroids:
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.KEEP,
                confidence=0.5,
                similarity_scores={},
                reason="No centroids loaded",
            )

        # Step 6: Embed ONLY the entity text (not context)
        # Entity-only embeddings maximize inter-category separation.
        # Full-sentence embeddings produce >0.93 similarity because
        # legal context dominates the embedding space.
        embedding = self._embed(entity_text)

        # Step 7: Compute similarities
        similarities = self._compute_similarities(embedding)

        if not similarities:
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.KEEP,
                confidence=0.5,
                similarity_scores={},
                reason="No centroids available for comparison",
            )

        # Step 8: Find best matching type
        best_type = max(similarities, key=similarities.get)
        best_score = similarities[best_type]
        original_score = similarities.get(entity_type, 0.0)
        margin = best_score - original_score

        # Step 8.5: If best match is NOT_ENTITY, check if it's a clear rejection
        # Require NOT_ENTITY to beat the best PII type by a clear margin
        # to avoid rejecting ambiguous short names like "Pura"
        not_entity_score = similarities.get("NOT_ENTITY", 0.0)
        pii_only = {k: v for k, v in similarities.items() if k != "NOT_ENTITY"}
        best_pii_for_reject = max(pii_only.values()) if pii_only else 0.0
        not_entity_margin = not_entity_score - best_pii_for_reject

        if (
            best_type == "NOT_ENTITY"
            and not_entity_score > self.reclassify_threshold
            and not_entity_margin >= self.margin_threshold
        ):
            return ValidationResult(
                original_type=entity_type,
                validated_type="NOT_ENTITY",
                action=ValidationAction.REJECT,
                confidence=not_entity_score,
                similarity_scores=similarities,
                reason=(
                    f"'{entity_text}' matches NOT_ENTITY centroid "
                    f"(score: {not_entity_score:.3f}, margin over PII: {not_entity_margin:.3f})"
                ),
            )

        if (
            best_type == "NOT_ENTITY"
            and not_entity_margin > 0
            and not_entity_margin < self.margin_threshold
        ):
            # Close call - flag for human review instead of rejecting
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.FLAG_HITL,
                confidence=best_pii_for_reject,
                similarity_scores=similarities,
                reason=(
                    f"'{entity_text}' close to NOT_ENTITY ({not_entity_score:.3f}) "
                    f"but also to PII ({best_pii_for_reject:.3f}), margin: {not_entity_margin:.3f}"
                ),
            )

        # Exclude NOT_ENTITY from reclassification targets
        pii_similarities = {
            k: v for k, v in similarities.items() if k != "NOT_ENTITY"
        }
        if pii_similarities:
            best_pii_type = max(pii_similarities, key=pii_similarities.get)
            best_pii_score = pii_similarities[best_pii_type]
            original_score = pii_similarities.get(entity_type, 0.0)
            margin = best_pii_score - original_score
        else:
            best_pii_type = entity_type
            best_pii_score = 0.0
            margin = 0.0

        # Step 9: Decision logic
        if best_pii_type == entity_type:
            # NER was correct
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.KEEP,
                confidence=best_pii_score,
                similarity_scores=similarities,
                reason=f"NER type confirmed (similarity: {best_pii_score:.3f})",
            )

        if best_pii_score >= self.reclassify_threshold and margin >= self.margin_threshold:
            # Clear reclassification to a different PII type
            return ValidationResult(
                original_type=entity_type,
                validated_type=best_pii_type,
                action=ValidationAction.RECLASSIFY,
                confidence=best_pii_score,
                similarity_scores=similarities,
                reason=(
                    f"Reclassified from {entity_type} to {best_pii_type} "
                    f"(score: {best_pii_score:.3f}, margin: {margin:.3f})"
                ),
            )

        if margin > 0 and margin < self.hitl_margin:
            # Uncertain - flag for human review
            return ValidationResult(
                original_type=entity_type,
                validated_type=entity_type,
                action=ValidationAction.FLAG_HITL,
                confidence=original_score,
                similarity_scores=similarities,
                reason=(
                    f"Uncertain: {entity_type} ({original_score:.3f}) vs "
                    f"{best_pii_type} ({best_pii_score:.3f}), margin: {margin:.3f}"
                ),
            )

        # Keep original
        return ValidationResult(
            original_type=entity_type,
            validated_type=entity_type,
            action=ValidationAction.KEEP,
            confidence=original_score,
            similarity_scores=similarities,
            reason=(
                f"Kept {entity_type} (best: {best_pii_type} with score {best_pii_score:.3f}, "
                f"below threshold or margin)"
            ),
        )

    def validate_batch(
        self,
        detections: list[tuple[str, str, int, int]],
        full_text: str,
    ) -> list[ValidationResult]:
        """
        Validate multiple detections efficiently.

        Args:
            detections: List of (entity_text, entity_type, start, end) tuples.
            full_text: The full document text.

        Returns:
            List of ValidationResult for each detection.
        """
        results = []
        for entity_text, entity_type, start, end in detections:
            result = self.validate(entity_text, entity_type, full_text, start, end)
            results.append(result)
        return results
