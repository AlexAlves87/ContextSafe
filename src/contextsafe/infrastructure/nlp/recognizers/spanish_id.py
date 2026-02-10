"""
Spanish identification document recognizers.

Recognizes:
- DNI (Documento Nacional de Identidad): 8 digits + letter
- NIE (Número de Identidad de Extranjero): X/Y/Z + 7 digits + letter
- CIF (Código de Identificación Fiscal): letter + 8 alphanumeric
- NSS (Número de Seguridad Social): 12 digits

Traceability:
- IMPLEMENTATION_PLAN.md Phase 5
- controlled_vocabulary.yaml#pii_categories.DNI
"""

from __future__ import annotations

import re
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class SpanishDNIRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish DNI (Documento Nacional de Identidad).

    Format: 8 digits + 1 control letter (e.g., 12345678Z)
    The letter is calculated from the number modulo 23.
    """

    # DNI control letters
    DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

    PATTERNS = [
        Pattern(
            "DNI_WITH_SEPARATOR",
            r"\b(\d{2}[.\-\s]?\d{3}[.\-\s]?\d{3}[.\-\s]?[A-Za-z])\b",
            0.7,
        ),
        Pattern(
            "DNI_COMPACT",
            r"\b(\d{8}[A-Za-z])\b",
            0.85,
        ),
        # Format: 8 digits + hyphen/space + letter (e.g., 47833273-N, 12345678 Z)
        Pattern(
            "DNI_WITH_FINAL_SEPARATOR",
            r"\b(\d{8}[\-\s][A-Za-z])\b",
            0.85,
        ),
        # Format: with DNI/NIF prefix (e.g., "DNI 47833273-N", "NIF: 12345678Z")
        Pattern(
            "DNI_WITH_PREFIX",
            r"(?:DNI|NIF|D\.N\.I\.?|N\.I\.F\.?)[:\s]+(\d{8}[\-\s]?[A-Za-z])",
            0.95,
        ),
    ]

    CONTEXT = [
        "dni", "documento", "identidad", "nacional", "nif",
        "identificación", "identificacion", "número", "numero",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_DNI",
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
        """Validate DNI checksum."""
        # Remove all separators (dots, hyphens, spaces, colons)
        clean = re.sub(r"[.\-\s:]", "", pattern_text).upper()

        # Also remove DNI/NIF prefix if present
        clean = re.sub(r"^(DNI|NIF|D\.?N\.?I\.?|N\.?I\.?F\.?)", "", clean, flags=re.IGNORECASE)
        clean = clean.strip()

        if len(clean) != 9:
            return False

        try:
            number = int(clean[:-1])
            letter = clean[-1]
            expected_letter = self.DNI_LETTERS[number % 23]
            return letter == expected_letter
        except (ValueError, IndexError):
            return False


class SpanishNIERecognizer(PatternRecognizer):
    """
    Recognizer for Spanish NIE (Número de Identidad de Extranjero).

    Format: X/Y/Z + 7 digits + 1 control letter (e.g., X1234567A)
    """

    NIE_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
    NIE_PREFIX_MAP = {"X": 0, "Y": 1, "Z": 2}

    PATTERNS = [
        Pattern(
            "NIE_WITH_SEPARATOR",
            r"\b([XYZxyz][.\-\s]?\d{7}[.\-\s]?[A-Za-z])\b",
            0.7,
        ),
        Pattern(
            "NIE_COMPACT",
            r"\b([XYZxyz]\d{7}[A-Za-z])\b",
            0.85,
        ),
    ]

    CONTEXT = [
        "nie", "extranjero", "residencia", "identificación",
        "identificacion", "número", "numero", "tarjeta",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_NIE",
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
        """Validate NIE checksum."""
        clean = re.sub(r"[.\-\s]", "", pattern_text).upper()
        if len(clean) != 9:
            return False

        try:
            prefix = clean[0]
            if prefix not in self.NIE_PREFIX_MAP:
                return False

            # Replace prefix with its numeric value for calculation
            number = int(str(self.NIE_PREFIX_MAP[prefix]) + clean[1:-1])
            letter = clean[-1]
            expected_letter = self.NIE_LETTERS[number % 23]
            return letter == expected_letter
        except (ValueError, IndexError):
            return False


class SpanishCIFRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish CIF (Código de Identificación Fiscal).

    Format: 1 letter + 7 digits + 1 control character (letter or digit)
    First letter indicates entity type (A, B, C, D, E, F, G, H, J, N, P, Q, R, S, U, V, W)
    """

    PATTERNS = [
        Pattern(
            "CIF_WITH_SEPARATOR",
            r"\b([A-HJ-NP-SUVW][.\-\s]?\d{2}[.\-\s]?\d{3}[.\-\s]?\d{3})\b",
            0.6,
        ),
        Pattern(
            "CIF_COMPACT",
            r"\b([A-HJ-NP-SUVW]\d{7}[A-J0-9])\b",
            0.75,
        ),
    ]

    CONTEXT = [
        "cif", "fiscal", "empresa", "sociedad", "compañía",
        "compania", "mercantil", "nif", "identificación fiscal",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_CIF",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


class SpanishNSSRecognizer(PatternRecognizer):
    """
    Recognizer for Spanish NSS (Número de Seguridad Social).

    Format: 12 digits (AA/NNNNNNNN/NN) where:
    - AA: Province code (01-52)
    - NNNNNNNN: Sequential number
    - NN: Control digits
    """

    PATTERNS = [
        Pattern(
            "NSS_WITH_SEPARATOR",
            r"\b(\d{2}[/\-\s]\d{8}[/\-\s]\d{2})\b",
            0.75,
        ),
        Pattern(
            "NSS_COMPACT",
            r"\b(\d{12})\b",
            0.4,  # Lower score due to potential false positives
        ),
    ]

    CONTEXT = [
        "seguridad social", "nss", "afiliación", "afiliacion",
        "número de afiliación", "numero de afiliacion", "ss",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "es",
        supported_entity: str = "ES_NSS",
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
        """Validate NSS format."""
        clean = re.sub(r"[/\-\s]", "", pattern_text)
        if len(clean) != 12:
            return False

        try:
            province = int(clean[:2])
            # Valid province codes: 01-52
            return 1 <= province <= 52
        except ValueError:
            return False
