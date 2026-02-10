"""
Spanish IBAN recognizer.

Recognizes Spanish IBAN numbers:
- Format: ES + 2 check digits + 20 digits (bank code, branch, control, account)
- Example: ES91 2100 0418 4502 0005 1332

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml#pii_categories.IBAN
"""

from __future__ import annotations

import re
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class SpanishIBANRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish IBAN numbers.

    Spanish IBAN: ES + 22 digits (24 characters total)
    Validates using MOD-97-10 algorithm (ISO 7064).
    """

    PATTERNS = [
        # IBAN with spaces (standard format)
        Pattern(
            "IBAN_SPACED",
            r"\b(ES\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4})\b",
            0.9,
        ),
        # IBAN compact (no spaces)
        Pattern(
            "IBAN_COMPACT",
            r"\b(ES\d{22})\b",
            0.85,
        ),
        # Old account number format (CCC - Código Cuenta Cliente)
        Pattern(
            "CCC_FORMAT",
            r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{2}[\s\-]?\d{10})\b",
            0.6,
        ),
    ]

    CONTEXT = [
        "iban", "cuenta", "bancaria", "banco", "transferencia",
        "ingreso", "domiciliación", "domiciliacion", "pago",
        "ccc", "número de cuenta", "numero de cuenta",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_IBAN",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """Validate IBAN using MOD-97-10 algorithm."""
        # Remove spaces and convert to uppercase
        iban = re.sub(r"\s", "", pattern_text).upper()

        # Spanish IBAN must be 24 characters
        if not iban.startswith("ES") or len(iban) != 24:
            # Might be CCC format, skip validation
            if len(re.sub(r"[\s\-]", "", pattern_text)) == 20:
                return True
            return False

        try:
            # Move first 4 chars to end
            rearranged = iban[4:] + iban[:4]

            # Convert letters to numbers (A=10, B=11, ..., Z=35)
            numeric = ""
            for char in rearranged:
                if char.isalpha():
                    numeric += str(ord(char) - ord("A") + 10)
                else:
                    numeric += char

            # Check if remainder is 1
            return int(numeric) % 97 == 1
        except (ValueError, IndexError):
            return False
