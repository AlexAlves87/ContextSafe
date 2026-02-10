# Element 1: Text Normalizer - Standalone Test

**Date:** 2026-02-03
**Status:** ✅ COMPLETED

---

## 1. Summary

| Metric | Value |
|--------|-------|
| Tests executed | 15 |
| Tests passed | 15 |
| Pass rate | 100% |
| Time | 0.002s |

## 2. Component

**File:** `scripts/preprocess/text_normalizer.py`

**Main Class:** `TextNormalizer`

**Functionality:**
- NFKC normalization (fullwidth → ASCII)
- Zero-width character removal (U+200B-U+200F, U+2060-U+206F, U+FEFF)
- Cyrillic → Latin homoglyph mapping (17 characters)
- NBSP → space + collapse multiple spaces
- Soft hyphen removal

**Preserves (critical for NER):**
- Case (RoBERTa is case-sensitive)
- Spanish accents (María, García, etc.)
- Legitimate punctuation

## 3. Validated Tests

| Test | Category | Description |
|------|----------|-------------|
| fullwidth_dni | Unicode | `１２３４５６７８Z` → `12345678Z` |
| fullwidth_mixed | Unicode | Fullwidth letters and numbers |
| zero_width_in_dni | Evasion | Zero-width inside DNI |
| zero_width_in_name | Evasion | Zero-width in names |
| cyrillic_o_in_dni | Homoglyph | Cyrillic О → Latin O |
| cyrillic_mixed | Homoglyph | Mixed Cyrillic/Latin text |
| nbsp_in_address | Spaces | NBSP → normal space |
| multiple_spaces | Spaces | Multiple spaces collapse |
| soft_hyphen_in_word | OCR | Soft hyphens removed |
| combined_evasion | Combined | Multiple combined techniques |
| preserve_accents | Preserve | Spanish accents intact |
| preserve_case | Preserve | Case not modified |
| preserve_punctuation | Preserve | Legal punctuation preserved |
| empty_string | Edge | Empty string |
| only_spaces | Edge | Spaces only |

## 4. Diagnostic Example

**Input:** `DNI: １２​３４​５６​７８Х del Sr. María`

**Output:** `DNI: 12345678X del Sr. María`

**Changes applied:**
1. Removed 3 zero-width characters
2. Applied NFKC normalization
3. Replaced 1 Cyrillic homoglyphs

## 5. Next Step

Integrate `TextNormalizer` into the NER pipeline (`CompositeNerAdapter`) and evaluate impact on adversarial tests.

---

