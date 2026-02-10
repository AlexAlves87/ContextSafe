"""
Spanish location recognizers.

Recognizes:
- Spanish postal codes (5 digits, province codes 01-52)
- Spanish addresses with context

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml#pii_categories.ADDRESS
"""

from __future__ import annotations

import re
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class SpanishPostalCodeRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish postal codes.

    Format: 5 digits where first 2 are province code (01-52)
    Examples: 08635 (Barcelona), 28001 (Madrid), 41001 (Sevilla)

    Uses context to avoid false positives (other 5-digit numbers).
    """

    # Valid province codes (01-52)
    VALID_PROVINCES = set(range(1, 53))

    PATTERNS = [
        # Pattern: Standalone 5-digit postal code
        # We use a simple pattern and rely on:
        # 1. Province code validation (01-52)
        # 2. Context enhancement for confidence
        # NOTE: Increased confidence to 0.92 to ensure detection
        Pattern(
            "CP_5_DIGITS",
            r"\b(\d{5})\b",
            0.92,  # Increased to ensure capture even near addresses
        ),
    ]

    CONTEXT = [
        "código postal", "cp", "c.p.", "dirección", "direccion",
        "domicilio", "calle", "avenida", "plaza", "paseo",
        "localidad", "municipio", "población", "poblacion",
        "residencia", "vive", "residente", "notificaciones",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_ZIP_CODE",
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
        """Validate Spanish postal code."""
        # Extract just the digits
        digits = re.sub(r"\D", "", pattern_text)

        if len(digits) != 5:
            return False

        try:
            province = int(digits[:2])
            # Valid province codes: 01-52
            return province in self.VALID_PROVINCES
        except ValueError:
            return False


class SpanishAddressRecognizer(PatternRecognizer):
    """
    Recognizer for full Spanish addresses.

    Handles common street types and address formats.
    """

    PATTERNS = [
        # Pattern 1: Full address (Calle/Av/Plaza + name + number) - case insensitive
        # NOTE: Uses \s* to allow "c/Santiago" without space after prefix
        Pattern(
            "ADDRESS_FULL",
            r"(?i)\b((?:Calle|C/|c\.|Avenida|Av\.|Avda\.|Plaza|Pl\.|Paseo|P\.º|Pº|Travesía|Camino|Carretera|Ronda)\s*[^,\n]{3,50}?,?\s*(?:n[ºo°]?\s*)?\d{1,4}(?:\s*[,\-–]\s*\d{1,4})?)\b",
            0.90,
        ),
        # Pattern 2: Address with "domicilio" context
        Pattern(
            "ADDRESS_DOMICILIO",
            r"(?i)domicilio\s+(?:en|a\s+efectos\s+de\s+notificaciones\s+en)\s+([^,\n]{10,100})",
            0.95,
        ),
        # Pattern 3: Simple street pattern c/Name Number (with or without space)
        Pattern(
            "ADDRESS_SIMPLE_STREET",
            r"(?i)\b(c/\s*[A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,40}\s+\d{1,4})\b",
            0.85,
        ),
        # Pattern 4: Street + number + postal code + city (complete address)
        # "c/Santiago Ramon y Cajal 45, 08635 Sant Esteve Sesrovires"
        Pattern(
            "ADDRESS_COMPLETE",
            r"(?i)\b(c/\s*[A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,40}\s+\d{1,4},\s*\d{5}\s+[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)\b",
            0.98,
        ),
    ]

    CONTEXT = [
        "domicilio", "dirección", "direccion", "residencia",
        "calle", "avenida", "plaza", "paseo", "vive", "residente",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_ADDRESS",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
