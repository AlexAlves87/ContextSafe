"""
NLP infrastructure for ContextSafe.

Provides NER services using spaCy, Presidio, regex patterns, and composite strategies.
"""

from contextsafe.infrastructure.nlp.anonymization_adapter import (
    InMemoryAnonymizationAdapter,
    get_anonymization_service,
)
from contextsafe.infrastructure.nlp.composite_adapter import CompositeNerAdapter
from contextsafe.infrastructure.nlp.hybrid_ner_adapter import HybridNerAdapter
from contextsafe.infrastructure.nlp.presidio_adapter import PresidioNerAdapter
from contextsafe.infrastructure.nlp.regex_adapter import RegexNerAdapter
from contextsafe.infrastructure.nlp.spacy_adapter import SpacyNerAdapter
from contextsafe.infrastructure.nlp.recognizers.legal_titles import LegalTitlesRecognizer
from contextsafe.infrastructure.nlp.roberta_ner_adapter import RobertaNerAdapter


__all__ = [
    "CompositeNerAdapter",
    "HybridNerAdapter",
    "RegexNerAdapter",
    "RobertaNerAdapter",
    "SpacyNerAdapter",
    "PresidioNerAdapter",
    "LegalTitlesRecognizer",
    "InMemoryAnonymizationAdapter",
    "get_anonymization_service",
]
