"""
Entity type validation using embeddings.

This module provides post-NER validation to correct entity type misclassifications
using semantic similarity to type centroids.

Based on:
- NER Retriever (arXiv 2509.04011)
- CEPTNER (Knowledge-Based Systems, 2024)
"""

from .entity_type_validator import EntityTypeValidator, ValidationResult

__all__ = ["EntityTypeValidator", "ValidationResult"]
