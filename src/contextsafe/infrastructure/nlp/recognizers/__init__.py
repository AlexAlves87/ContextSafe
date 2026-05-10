"""
Spanish PII recognizers for Presidio.

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml PII categories
"""

from contextsafe.infrastructure.nlp.recognizers.spanish_dates import (
    SpanishDateRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_iban import (
    SpanishIBANRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_id import (
    SpanishCIFRecognizer,
    SpanishDNIRecognizer,
    SpanishNIERecognizer,
    SpanishNSSRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_location import (
    SpanishAddressRecognizer,
    SpanishPostalCodeRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_names import (
    SpanishNameRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_orgs import (
    SpanishOrgRecognizer,
)
from contextsafe.infrastructure.nlp.recognizers.spanish_phone import (
    SpanishPhoneRecognizer,
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
