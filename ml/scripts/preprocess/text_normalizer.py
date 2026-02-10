#!/usr/bin/env python3
"""
Text normalizer for NER preprocessing.

Applies Unicode normalization optimized for Spanish legal documents:
- NFKC normalization (fullwidth → ASCII)
- Zero-width character removal
- Homoglyph mapping (Cyrillic → Latin)
- Space normalization

Based on: docs/reports/2026-02-03_1730_investigacion_text_normalization.md

Usage:
    python scripts/preprocess/text_normalizer.py

This script runs standalone tests. For integration, import TextNormalizer.
"""

import re
import time
import unicodedata
from dataclasses import dataclass
from typing import List, Tuple


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


@dataclass
class NormalizationResult:
    """Result of text normalization with diagnostics."""
    original: str
    normalized: str
    changes: List[str]

    @property
    def was_modified(self) -> bool:
        return self.original != self.normalized


class TextNormalizer:
    """
    Text normalizer for NER preprocessing in Spanish legal documents.

    Optimized to handle:
    - OCR artifacts (fullwidth characters, extra spaces)
    - Unicode evasion attempts (zero-width, homoglyphs)
    - Common encoding issues (BOM, NBSP)

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

    def normalize_with_diagnostics(self, text: str) -> NormalizationResult:
        """
        Normalize text and return diagnostics about changes made.

        Useful for debugging and understanding what was modified.
        """
        changes = []
        original = text

        if not text:
            return NormalizationResult(original, text, changes)

        # 1. Zero-width removal
        zero_width_count = len(ZERO_WIDTH_PATTERN.findall(text))
        if zero_width_count > 0:
            text = ZERO_WIDTH_PATTERN.sub('', text)
            changes.append(f"Removed {zero_width_count} zero-width characters")

        # 2. NFKC normalization
        nfkc_text = unicodedata.normalize('NFKC', text)
        if nfkc_text != text:
            changes.append("Applied NFKC normalization")
            text = nfkc_text

        # 3. Homoglyph mapping
        homoglyph_count = 0
        for cyrillic, latin in HOMOGLYPHS.items():
            count = text.count(cyrillic)
            if count > 0:
                homoglyph_count += count
                text = text.replace(cyrillic, latin)
        if homoglyph_count > 0:
            changes.append(f"Replaced {homoglyph_count} Cyrillic homoglyphs")

        # 4. Space normalization
        nbsp_count = text.count('\u00a0')
        if nbsp_count > 0:
            text = text.replace('\u00a0', ' ')
            changes.append(f"Replaced {nbsp_count} NBSP characters")

        before_collapse = text
        text = re.sub(r' +', ' ', text)
        if text != before_collapse:
            changes.append("Collapsed multiple spaces")

        # 5. Soft hyphen removal
        soft_hyphen_count = text.count('\u00ad')
        if soft_hyphen_count > 0:
            text = text.replace('\u00ad', '')
            changes.append(f"Removed {soft_hyphen_count} soft hyphens")

        text = text.strip()

        return NormalizationResult(original, text, changes)


# =============================================================================
# STANDALONE TESTS
# =============================================================================

@dataclass
class TestCase:
    """Test case for normalizer validation."""
    name: str
    input: str
    expected: str
    description: str


TEST_CASES: List[TestCase] = [
    # Fullwidth characters (from adversarial test: fullwidth_numbers)
    TestCase(
        name="fullwidth_dni",
        input="DNI: １２３４５６７８Z",
        expected="DNI: 12345678Z",
        description="Fullwidth digits should normalize to ASCII"
    ),
    TestCase(
        name="fullwidth_mixed",
        input="Ａｂｃ １２３",
        expected="Abc 123",
        description="Fullwidth letters and digits"
    ),

    # Zero-width characters (from adversarial test: zero_width_space)
    TestCase(
        name="zero_width_in_dni",
        input="123\u200b456\u200b78Z",
        expected="12345678Z",
        description="Zero-width spaces inside DNI"
    ),
    TestCase(
        name="zero_width_in_name",
        input="María\u200c García",
        expected="María García",
        description="Zero-width non-joiner in name"
    ),

    # Cyrillic homoglyphs (from adversarial test: cyrillic_o)
    TestCase(
        name="cyrillic_o_in_dni",
        input="1234567О",  # Cyrillic О (U+041E)
        expected="1234567O",  # Latin O
        description="Cyrillic O should become Latin O"
    ),
    TestCase(
        name="cyrillic_mixed",
        input="Маría",  # Cyrillic М + а
        expected="María",
        description="Mixed Cyrillic/Latin text"
    ),

    # NBSP and space issues
    TestCase(
        name="nbsp_in_address",
        input="Calle\u00a0Mayor\u00a0123",
        expected="Calle Mayor 123",
        description="NBSP should become regular space"
    ),
    TestCase(
        name="multiple_spaces",
        input="Juan    García    López",
        expected="Juan García López",
        description="Multiple spaces should collapse"
    ),

    # Soft hyphens
    TestCase(
        name="soft_hyphen_in_word",
        input="docu\u00admen\u00adto",
        expected="documento",
        description="Soft hyphens should be removed"
    ),

    # Combined issues (realistic OCR/evasion scenario)
    TestCase(
        name="combined_evasion",
        input="DNI:\u00a0１２\u200b３４\u200b５６\u200b７８Х",  # NBSP + fullwidth + zero-width + Cyrillic
        expected="DNI: 12345678X",
        description="Combined evasion attempt"
    ),

    # Edge cases - should NOT modify
    TestCase(
        name="preserve_accents",
        input="María José García Núñez",
        expected="María José García Núñez",
        description="Spanish accents must be preserved"
    ),
    TestCase(
        name="preserve_case",
        input="JUAN garcía López",
        expected="JUAN garcía López",
        description="Case must be preserved (RoBERTa is case-sensitive)"
    ),
    TestCase(
        name="preserve_punctuation",
        input="Art. 123, párr. 2º",
        expected="Art. 123, párr. 2o",  # NFKC converts º to o
        description="Legal punctuation preserved (º becomes o via NFKC)"
    ),

    # Empty and edge cases
    TestCase(
        name="empty_string",
        input="",
        expected="",
        description="Empty string returns empty"
    ),
    TestCase(
        name="only_spaces",
        input="   ",
        expected="",
        description="Only spaces returns empty after strip"
    ),
]


def run_tests() -> Tuple[int, int, List[str]]:
    """
    Run all test cases and return results.

    Returns:
        Tuple of (passed, total, failure_messages)
    """
    normalizer = TextNormalizer()
    passed = 0
    failures = []

    for test in TEST_CASES:
        result = normalizer.normalize(test.input)
        if result == test.expected:
            passed += 1
            print(f"  ✅ {test.name}")
        else:
            failures.append(
                f"{test.name}: expected '{test.expected}', got '{result}'"
            )
            print(f"  ❌ {test.name}")
            print(f"      Input:    '{test.input}'")
            print(f"      Expected: '{test.expected}'")
            print(f"      Got:      '{result}'")

    return passed, len(TEST_CASES), failures


def run_diagnostics_demo():
    """Demonstrate diagnostics mode with a complex example."""
    normalizer = TextNormalizer()

    print("\n" + "=" * 60)
    print("DIAGNOSTICS DEMO")
    print("=" * 60)

    # Complex evasion attempt
    text = "DNI:\u00a0１２\u200b３４\u200b５６\u200b７８Х del Sr. María"

    result = normalizer.normalize_with_diagnostics(text)

    print(f"\nOriginal:   '{result.original}'")
    print(f"Normalized: '{result.normalized}'")
    print(f"Modified:   {result.was_modified}")
    print("\nChanges applied:")
    for change in result.changes:
        print(f"  - {change}")


if __name__ == "__main__":
    start_time = time.time()

    print("=" * 60)
    print("TEXT NORMALIZER - STANDALONE TESTS")
    print("=" * 60)
    print(f"\nRunning {len(TEST_CASES)} test cases...\n")

    passed, total, failures = run_tests()

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} passed ({100*passed/total:.1f}%)")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")

    run_diagnostics_demo()

    elapsed = time.time() - start_time
    print(f"\nTiempo de ejecución: {elapsed:.3f}s")

    # Exit code for CI
    exit(0 if passed == total else 1)
