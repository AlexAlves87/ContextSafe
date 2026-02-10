"""
Spanish phone number recognizer.

Recognizes Spanish phone numbers in various formats:
- Mobile: 6XX XXX XXX, 7XX XXX XXX
- Landline: 9XX XXX XXX, 8XX XXX XXX
- With country code: +34 XXX XXX XXX

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml#pii_categories.PHONE
"""

from __future__ import annotations

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class SpanishPhoneRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish phone numbers.

    Supports:
    - Mobile numbers (6XX, 7XX)
    - Landline numbers (9XX, 8XX)
    - International format (+34)
    """

    PATTERNS = [
        # International format with +34
        Pattern(
            "PHONE_INTERNATIONAL",
            r"\b(\+34[\s\-.]?\d{3}[\s\-.]?\d{3}[\s\-.]?\d{3})\b",
            0.9,
        ),
        # International format with 0034
        Pattern(
            "PHONE_INTERNATIONAL_00",
            r"\b(0034[\s\-.]?\d{3}[\s\-.]?\d{3}[\s\-.]?\d{3})\b",
            0.85,
        ),
        # Mobile numbers (6XX, 7XX) with separators
        Pattern(
            "PHONE_MOBILE_SPACED",
            r"\b([67]\d{2}[\s\-\.]\d{3}[\s\-\.]\d{3})\b",
            0.8,
        ),
        # Landline numbers (9XX, 8XX) with separators
        Pattern(
            "PHONE_LANDLINE_SPACED",
            r"\b([89]\d{2}[\s\-\.]\d{3}[\s\-\.]\d{3})\b",
            0.7,
        ),
        # Compact 9-digit format
        Pattern(
            "PHONE_COMPACT",
            r"\b([6789]\d{8})\b",
            0.6,
        ),
    ]

    CONTEXT = [
        "teléfono", "telefono", "móvil", "movil", "celular",
        "tel", "tfno", "telf", "contacto", "llamar", "número",
        "numero", "fijo", "particular", "whatsapp",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_PHONE",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
