#!/usr/bin/env python3
"""
Text normalizer for NER preprocessing.

Normalizes text before NER inference to handle:
- OCR errors (l/I, 0/O confusion)
- Spacing issues (collapsed or extra spaces)
- Unicode variations (fullwidth, zero-width, lookalikes)
- Spanish document abbreviations (D.N.I., N.I.F., etc.)

Usage:
    from scripts.inference.text_normalizer import TextNormalizer

    normalizer = TextNormalizer()
    clean_text, char_map = normalizer.normalize(dirty_text)
    # After NER, use char_map to convert spans back to original positions
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional


@dataclass
class CharMapping:
    """Maps positions between original and normalized text."""

    original_text: str
    normalized_text: str
    # normalized_pos -> original_pos
    to_original: list[int]
    # original_pos -> normalized_pos (or -1 if deleted)
    to_normalized: list[int]

    def span_to_original(self, start: int, end: int) -> tuple[int, int]:
        """Convert span from normalized to original positions."""
        if start >= len(self.to_original) or end > len(self.to_original):
            return start, end

        orig_start = self.to_original[start]
        # For end, we need the position after the last char
        orig_end = self.to_original[end - 1] + 1 if end > 0 else 0

        return orig_start, orig_end

    def span_to_normalized(self, start: int, end: int) -> tuple[int, int]:
        """Convert span from original to normalized positions."""
        if start >= len(self.to_normalized) or end > len(self.to_normalized):
            return start, end

        # Find first non-deleted position from start
        norm_start = self.to_normalized[start]
        while norm_start == -1 and start < len(self.to_normalized) - 1:
            start += 1
            norm_start = self.to_normalized[start]

        # Find last non-deleted position before end
        norm_end = self.to_normalized[end - 1] + 1 if end > 0 else 0

        return norm_start, norm_end


class TextNormalizer:
    """
    Normalizes Spanish legal text for NER processing.

    All transformations preserve character mapping for span recovery.
    """

    # Zero-width and invisible characters
    ZERO_WIDTH_CHARS = re.compile(r'[\u200b\u200c\u200d\u2060\ufeff]')

    # Fullwidth ASCII variants (０-９, Ａ-Ｚ, ａ-ｚ)
    FULLWIDTH_DIGITS = {chr(0xFF10 + i): chr(0x30 + i) for i in range(10)}
    FULLWIDTH_UPPER = {chr(0xFF21 + i): chr(0x41 + i) for i in range(26)}
    FULLWIDTH_LOWER = {chr(0xFF41 + i): chr(0x61 + i) for i in range(26)}
    FULLWIDTH_MAP = {**FULLWIDTH_DIGITS, **FULLWIDTH_UPPER, **FULLWIDTH_LOWER}

    # Cyrillic lookalikes commonly used for evasion
    CYRILLIC_MAP = {
        'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H', 'І': 'I',
        'К': 'K', 'М': 'M', 'О': 'O', 'Р': 'P', 'Т': 'T', 'Х': 'X',
        'а': 'a', 'с': 'c', 'е': 'e', 'і': 'i', 'о': 'o', 'р': 'p',
        'х': 'x', 'у': 'y',
    }

    # Spanish document abbreviation patterns
    ABBREVIATION_PATTERNS = [
        # D.N.I., D. N. I., DNl, etc.
        (re.compile(r'D\.?\s*N\.?\s*I\.?', re.IGNORECASE), 'DNI'),
        (re.compile(r'N\.?\s*I\.?\s*F\.?', re.IGNORECASE), 'NIF'),
        (re.compile(r'C\.?\s*I\.?\s*F\.?', re.IGNORECASE), 'CIF'),
        (re.compile(r'N\.?\s*I\.?\s*E\.?', re.IGNORECASE), 'NIE'),
        (re.compile(r'N\.?\s*S\.?\s*S\.?', re.IGNORECASE), 'NSS'),
        (re.compile(r'I\.?\s*B\.?\s*A\.?\s*N\.?', re.IGNORECASE), 'IBAN'),
    ]

    # OCR confusion patterns (context-sensitive)
    OCR_PATTERNS = [
        # DNl (lowercase L) -> DNI
        (re.compile(r'\bDN[lI1]\b'), 'DNI'),
        # N1F, N1E (digit one) -> NIF, NIE
        (re.compile(r'\bN[1Il]F\b'), 'NIF'),
        (re.compile(r'\bN[1Il]E\b'), 'NIE'),
    ]

    def __init__(self,
                 normalize_unicode: bool = True,
                 normalize_abbreviations: bool = True,
                 normalize_ocr: bool = True,
                 collapse_spaces: bool = True,
                 normalize_o_zero: bool = True):
        """
        Initialize normalizer with configurable options.

        Args:
            normalize_unicode: Convert fullwidth/cyrillic to ASCII
            normalize_abbreviations: Expand D.N.I. -> DNI, etc.
            normalize_ocr: Fix common OCR errors
            collapse_spaces: Remove extra spaces in number sequences
            normalize_o_zero: Context-aware O/0 normalization
        """
        self.normalize_unicode = normalize_unicode
        self.normalize_abbreviations = normalize_abbreviations
        self.normalize_ocr = normalize_ocr
        self.collapse_spaces = collapse_spaces
        self.normalize_o_zero = normalize_o_zero

    def normalize(self, text: str) -> tuple[str, CharMapping]:
        """
        Normalize text and return mapping to original positions.

        Args:
            text: Original text

        Returns:
            Tuple of (normalized_text, CharMapping)
        """
        # Build character-by-character with position tracking
        result = []
        to_original = []  # result_pos -> original_pos
        to_normalized = [-1] * len(text)  # original_pos -> result_pos

        i = 0
        while i < len(text):
            char = text[i]
            replacement = None
            skip_count = 0

            # Check for multi-character patterns first
            if self.normalize_abbreviations:
                for pattern, repl in self.ABBREVIATION_PATTERNS:
                    match = pattern.match(text, i)
                    if match:
                        replacement = repl
                        skip_count = match.end() - match.start()
                        break

            if replacement is None and self.normalize_ocr:
                for pattern, repl in self.OCR_PATTERNS:
                    match = pattern.match(text, i)
                    if match:
                        replacement = repl
                        skip_count = match.end() - match.start()
                        break

            if replacement is not None:
                # Multi-character replacement
                for j, new_char in enumerate(replacement):
                    result.append(new_char)
                    to_original.append(i)  # Map to start of original pattern
                    if j == 0:
                        to_normalized[i] = len(result) - 1
                # Mark skipped original chars
                for k in range(1, skip_count):
                    if i + k < len(text):
                        to_normalized[i + k] = -1
                i += skip_count
                continue

            # Single character transformations
            new_char = char

            # Zero-width removal
            if self.normalize_unicode and self.ZERO_WIDTH_CHARS.match(char):
                to_normalized[i] = -1  # Deleted
                i += 1
                continue

            # Fullwidth normalization
            if self.normalize_unicode and char in self.FULLWIDTH_MAP:
                new_char = self.FULLWIDTH_MAP[char]

            # Cyrillic normalization
            if self.normalize_unicode and char in self.CYRILLIC_MAP:
                new_char = self.CYRILLIC_MAP[char]

            # O/0 normalization in numeric context
            if self.normalize_o_zero:
                new_char = self._normalize_o_zero_contextual(text, i, new_char)

            # Space collapsing in number sequences
            if self.collapse_spaces and char == ' ':
                if self._should_collapse_space(text, i):
                    to_normalized[i] = -1  # Deleted
                    i += 1
                    continue

            result.append(new_char)
            to_original.append(i)
            to_normalized[i] = len(result) - 1
            i += 1

        normalized_text = ''.join(result)

        return normalized_text, CharMapping(
            original_text=text,
            normalized_text=normalized_text,
            to_original=to_original,
            to_normalized=to_normalized,
        )

    def _normalize_o_zero_contextual(self, text: str, pos: int, char: str) -> str:
        """
        Normalize O/0 based on surrounding context.

        Rules:
        - In IBAN context (ES followed by digits): O -> 0
        - In phone/number sequence: O -> 0
        - Preserve O in words
        """
        if char not in 'Oo0':
            return char

        # Look for IBAN prefix nearby
        start = max(0, pos - 10)
        context_before = text[start:pos]

        # After ES in IBAN
        if re.search(r'ES\d*$', context_before, re.IGNORECASE):
            return '0' if char in 'Oo' else char

        # After IBAN keyword
        if re.search(r'IBAN\s*$', context_before, re.IGNORECASE):
            return '0' if char in 'Oo' else char

        # In a numeric sequence (digit before and after)
        if pos > 0 and pos < len(text) - 1:
            before = text[pos - 1]
            after = text[pos + 1]
            if before.isdigit() and after.isdigit():
                return '0' if char in 'Oo' else char

        return char

    def _should_collapse_space(self, text: str, pos: int) -> bool:
        """
        Determine if a space should be collapsed.

        Collapse spaces in DNI/phone-like patterns:
        - "12 345 678" -> "12345678"
        - But NOT in addresses: "Calle Mayor 15"
        """
        if pos == 0 or pos >= len(text) - 1:
            return False

        before = text[pos - 1]
        after = text[pos + 1]

        # Collapse between digits
        if before.isdigit() and after.isdigit():
            # Check if this looks like a document number pattern
            # Look for DNI/phone context
            start = max(0, pos - 15)
            context = text[start:pos].upper()

            # Document number contexts where we want to collapse
            if any(kw in context for kw in ['DNI', 'NIF', 'NIE', 'NSS', 'IBAN', 'TEL', 'MÓVIL', 'FAX']):
                return True

            # Count consecutive digit groups
            # If pattern is X XX XXX or similar, likely a number to collapse
            match = re.search(r'(\d+\s+)+\d*$', text[start:pos + 10])
            if match and match.group().count(' ') >= 2:
                return True

        return False

    def normalize_simple(self, text: str) -> str:
        """
        Simple normalization without position tracking.

        Use when you don't need to map spans back to original text.
        """
        normalized, _ = self.normalize(text)
        return normalized


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def normalize_for_ner(text: str) -> tuple[str, CharMapping]:
    """
    Normalize text for NER with default settings.

    Args:
        text: Raw input text (potentially from OCR)

    Returns:
        Tuple of (normalized_text, char_mapping)
    """
    normalizer = TextNormalizer()
    return normalizer.normalize(text)


def normalize_dni(text: str) -> str:
    """Normalize a DNI/NIE string specifically."""
    # Remove spaces
    text = re.sub(r'\s+', '', text)
    # Uppercase
    text = text.upper()
    # Fix common OCR errors
    text = text.replace('O', '0').replace('l', '1').replace('I', '1')
    # But the letter at the end should be a letter
    if len(text) >= 9 and text[-1].isdigit():
        # Common: 0 at end should be O, 1 should be I
        if text[-1] == '0':
            text = text[:-1] + 'O'
        elif text[-1] == '1':
            text = text[:-1] + 'I'
    return text


def normalize_iban(text: str) -> str:
    """Normalize an IBAN string specifically."""
    # Remove spaces
    text = re.sub(r'\s+', '', text)
    # Uppercase
    text = text.upper()
    # Fix O/0 (IBAN has letters at start, then digits)
    if text.startswith('ES'):
        # After country code, should be digits
        prefix = text[:2]
        rest = text[2:].replace('O', '0').replace('l', '1').replace('I', '1')
        text = prefix + rest
    return text


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "DNI 12345678Z",
        "D.N.I. 12 345 678 Z",
        "DNl 12345678Z",  # OCR error
        "IBAN ES91 21O0 0418 45O2 0005 1332",  # O instead of 0
        "DNI １２３４５６７８Z",  # Fullwidth
        "DNI 123\u200b456\u200b78Z",  # Zero-width
        "con D.N.I. número 12345678-Z",
    ]

    normalizer = TextNormalizer()

    print("=" * 60)
    print("TEXT NORMALIZER TEST")
    print("=" * 60)

    for text in test_cases:
        normalized, mapping = normalizer.normalize(text)
        print(f"\nOriginal:   '{text}'")
        print(f"Normalized: '{normalized}'")

        # Test span mapping (find first digit sequence)
        match = re.search(r'\d+', normalized)
        if match:
            norm_start, norm_end = match.start(), match.end()
            orig_start, orig_end = mapping.span_to_original(norm_start, norm_end)
            print(f"Span [{norm_start}:{norm_end}] -> original [{orig_start}:{orig_end}]")
            print(f"  Normalized: '{normalized[norm_start:norm_end]}'")
            print(f"  Original:   '{text[orig_start:orig_end]}'")
