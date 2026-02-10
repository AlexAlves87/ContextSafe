"""
Spanish PII recognizers for Presidio.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml PII categories
"""

from contextsafe.infrastructure.nlp.recognizers.spanish_id import (
    SpanishDNIRecognizer,
    SpanishNIERecognizer,
    SpanishCIFRecognizer,
    SpanishNSSRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_phone import (
    SpanishPhoneRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_iban import (
    SpanishIBANRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_names import (
    SpanishNameRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_orgs import (
    SpanishOrgRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_location import (
    SpanishPostalCodeRecognizer,
    SpanishAddressRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_dates import (
    SpanishDateRecognizer,
)

__all__ = [
    "SpanishDNIRecognizer",
    "SpanishNIERecognizer",
    "SpanishCIFRecognizer",
    "SpanishNSSRecognizer",
    "SpanishPhoneRecognizer",
    "SpanishIBANRecognizer",
    "SpanishNameRecognizer",
    "SpanishOrgRecognizer",
    "SpanishPostalCodeRecognizer",
    "SpanishAddressRecognizer",
    "SpanishDateRecognizer",
]
