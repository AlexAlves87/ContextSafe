"""
Anonymization strategies for different levels.

Each strategy implements a different approach to replacing PII:
- MaskingStrategy (Level 1/BASIC): Replaces with asterisks
- PseudonymStrategy (Level 2/INTERMEDIATE): Replaces with Persona_001, Org_002, etc.
- SyntheticStrategy (Level 3/ADVANCED): Replaces with plausible synthetic data via LLM
"""

from contextsafe.infrastructure.nlp.strategies.base import (
    AnonymizationStrategy,
    ReplacementResult,
)
from contextsafe.infrastructure.nlp.strategies.masking import MaskingStrategy
from contextsafe.infrastructure.nlp.strategies.pseudonym import PseudonymStrategy
from contextsafe.infrastructure.nlp.strategies.synthetic import SyntheticStrategy


__all__ = [
    "AnonymizationStrategy",
    "ReplacementResult",
    "MaskingStrategy",
    "PseudonymStrategy",
    "SyntheticStrategy",
]
