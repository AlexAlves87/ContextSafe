"""
Text normalizer for NER preprocessing.

Applies Unicode normalization optimized for Spanish legal documents.
This is the production version integrated into the NER pipeline.

Based on: ml/docs/reports/2026-02-03_1730_investigacion_text_normalization.md
Standalone tests: ml/scripts/preprocess/text_normalizer.py
"""

import re
import unicodedata


# Zero-width and invisible characters to remove
ZERO_WIDTH_PATTERN = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

# Cyrillic homoglyphs that look identical to Latin
HOMOGLYPHS = {
    # Uppercase
    '\u0410': 'A',  # Cyrillic А → Latin A
    '\u0412': 'B',  # Cyrillic В → Latin B
    '\u0415': 'E',  # Cyrillic Е → Latin E
    '\u041a': 'K',  # Cyrillic К → Latin K
    '\u041c': 'M',  # Cyrillic М → Latin M
    '\u041d': 'H',  # Cyrillic Н → Latin H
    '\u041e': 'O',  # Cyrillic О → Latin O
    '\u0420': 'P',  # Cyrillic Р → Latin P
    '\u0421': 'C',  # Cyrillic С → Latin C
    '\u0422': 'T',  # Cyrillic Т → Latin T
    '\u0425': 'X',  # Cyrillic Х → Latin X
    # Lowercase
    '\u0430': 'a',  # Cyrillic а → Latin a
    '\u0435': 'e',  # Cyrillic е → Latin e
    '\u043e': 'o',  # Cyrillic о → Latin o
    '\u0440': 'p',  # Cyrillic р → Latin p
    '\u0441': 'c',  # Cyrillic с → Latin c
    '\u0443': 'y',  # Cyrillic у → Latin y
    '\u0445': 'x',  # Cyrillic х → Latin x
}


class TextNormalizer:
    """
    Text normalizer for NER preprocessing in Spanish legal documents.

    Applies:
    - NFKC normalization (fullwidth → ASCII)
    - Zero-width character removal
    - Homoglyph mapping (Cyrillic → Latin)
    - Space normalization (NBSP → space, collapse multiples)
    - Soft hyphen removal

    Does NOT modify:
    - Case (RoBERTa is case-sensitive)
    - Accents (important for Spanish)
    - Legitimate punctuation
    """

    def normalize(self, text: str) -> str:
        """
        Normalize text for NER processing.

        Args:
            text: Input text to normalize.

        Returns:
            Normalized text ready for NER.
        """
        if not text:
            return text

        # 1. Remove BOM and zero-width characters
        text = ZERO_WIDTH_PATTERN.sub('', text)

        # 2. NFKC normalization (fullwidth → ASCII, ligatures → expanded)
        text = unicodedata.normalize('NFKC', text)

        # 3. Homoglyph mapping (Cyrillic → Latin)
        for cyrillic, latin in HOMOGLYPHS.items():
            text = text.replace(cyrillic, latin)

        # 4. Normalize spaces (NBSP → space, collapse multiples)
        text = text.replace('\u00a0', ' ')  # NBSP
        text = re.sub(r' +', ' ', text)

        # 5. Remove soft hyphens
        text = text.replace('\u00ad', '')

        return text.strip()


# Module-level instance for convenience
_normalizer = TextNormalizer()


def normalize_text(text: str) -> str:
    """
    Convenience function to normalize text.

    Args:
        text: Input text to normalize.

    Returns:
        Normalized text.
    """
    return _normalizer.normalize(text)
