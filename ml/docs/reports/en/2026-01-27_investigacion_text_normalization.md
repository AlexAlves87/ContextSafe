# Research: Text Normalization for NER in Legal Documents

**Date:** 2026-01-27
**Author:** AlexAlves87
**Type:** Academic Literature Review
**Status:** Completed

---

## 1. Executive Summary

This research analyzes best practices for text normalization in NER pipelines, with emphasis on:
1. Unicode normalization (fullwidth, zero-width, homoglyphs)
2. Correction of OCR artifacts
3. Integration with transformer models

### Key Findings

| Finding | Source | Impact |
|---------|--------|--------|
| NFKC normalizes fullwidth → ASCII automatically | UAX #15 Unicode Standard | High |
| Zero-width characters (U+200B-U+200F) must be explicitly removed | Unicode Consortium | High |
| OCR-sensitive neurons exist in transformers and can be modulated | arXiv:2409.16934 (ICADL 2024) | Medium |
| Preprocessing must match model pretraining | Best practices 2024 | Critical |
| NFKC destroys information in complex scripts (Arabic, Hebrew) | UAX #15 | Low (does not apply to Spanish) |

---

## 2. Methodology

### 2.1 Sources Consulted

| Source | Type | Year | Relevance |
|--------|------|------|-----------|
| UAX #15 Unicode Standard | Specification | 2024 | Unicode Standard |
| arXiv:2409.16934 | Paper (ICADL 2024) | 2024 | OCR-sensitive neurons |
| TACL Neural OCR Post-Hoc | Academic paper | 2021 | Neural OCR correction |
| Brenndoerfer NLP Guide | Technical tutorial | 2024 | Industrial best practices |
| Promptfoo Security | Technical article | 2024 | Unicode evasion in AI |

### 2.2 Search Criteria

- "text normalization NER preprocessing Unicode OCR"
- "Unicode normalization NLP NER fullwidth characters zero-width space"
- "OCR post-correction NER robustness neural network ACL EMNLP"

---

## 3. Results

### 3.1 Unicode Normalization Forms

The Unicode standard (UAX #15) defines 4 normalization forms:

| Form | Name | Description | Use in NER |
|------|------|-------------|------------|
| **NFC** | Canonical Composition | Composes characters (é = e + ´) | Standard |
| **NFD** | Canonical Decomposition | Decomposes characters | Search |
| **NFKC** | Compatibility Composition | NFC + compatibility | **Recommended for NER** |
| **NFKD** | Compatibility Decomposition | NFD + compatibility | Analysis |

**Source:** [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/)

#### 3.1.1 NFKC for Entity Normalization

NFKC is the recommended form for NER because:

```
Fullwidth:  １２３４５６７８ → 12345678
Superscript: ² → 2
Fractions:   ½ → 1/2
Roman:       Ⅳ → IV
Ligatures:   ﬁ → fi
```

**Warning:** NFKC destroys information in complex scripts (Arabic, Hebrew, Devanagari) where control characters are semantically relevant. For legal Spanish, this is not a problem.

### 3.2 Problematic Invisible Characters

**Source:** [The Invisible Threat: Zero-Width Unicode Characters](https://www.promptfoo.dev/blog/invisible-unicode-threats/)

| Codepoint | Name | Problem | Action |
|-----------|------|---------|--------|
| U+200B | Zero Width Space | Breaks tokenization | Remove |
| U+200C | Zero Width Non-Joiner | Separates joined characters | Remove |
| U+200D | Zero Width Joiner | Joins separated characters | Remove |
| U+200E | Left-to-Right Mark | Confuses text direction | Remove |
| U+200F | Right-to-Left Mark | Confuses text direction | Remove |
| U+FEFF | BOM / Zero Width No-Break | Encoding artifact | Remove |
| U+00A0 | Non-Breaking Space | Not detected by isspace() | → normal space |
| U+00AD | Soft Hyphen | Invisible hyphen | Remove |

**Impact on NER:**
- DNI `123​456​78Z` (with U+200B) does not match regex `\d{8}[A-Z]`
- Tokenizer splits word into multiple tokens
- Model does not recognize the entity

### 3.3 Homoglyphs and Evasion

**Source:** [Invisible Unicode Tricks Bypass AI Detection](https://justdone.com/blog/ai/invisible-unicode-tricks)

| Latin | Cyrillic | Visual | Code |
|-------|----------|--------|------|
| A | А | Identical | U+0041 vs U+0410 |
| B | В | Identical | U+0042 vs U+0412 |
| E | Е | Identical | U+0045 vs U+0415 |
| O | О | Identical | U+004F vs U+041E |
| X | Х | Identical | U+0058 vs U+0425 |

**Impact on NER:**
- DNI `12345678Х` (Cyrillic) does not match regex with `[A-Z]`
- Model may not recognize as valid DNI

**Solution:** Normalize common Latin homoglyphs before NER.

### 3.4 OCR-Sensitive Neurons in Transformers

**Source:** [Investigating OCR-Sensitive Neurons](https://arxiv.org/abs/2409.16934) (ICADL 2024)

#### Paper Findings

1. **Transformers have OCR-sensitive neurons:**
   - Identified through activation pattern analysis
   - Respond differently to clean vs corrupted text

2. **Critical layers identified:**
   - Llama 2: Layers 0-2, 11-13, 23-28
   - Mistral: Layers 29-31

3. **Proposed solution:**
   - Neutralize OCR-sensitive neurons
   - Improves NER performance on historical documents

#### Application to ContextSafe

For our fine-tuned RoBERTa model:
- Text normalization BEFORE inference is more practical
- Neutralizing neurons requires modifying model architecture
- **Recommendation:** Preprocessing, not model modification

### 3.5 Common OCR Errors and Normalization

**Source:** [OCR Data Entry: Preprocessing Text for NLP](https://labelyourdata.com/articles/ocr-data-entry)

| OCR Error | Pattern | Normalization |
|-----------|---------|---------------|
| l ↔ I ↔ 1 | `DNl`, `DN1` | → `DNI` |
| O ↔ 0 | `2l0O` | Contextual (numbers) |
| rn ↔ m | `nom` → `nom` | Dictionary |
| S ↔ 5 | `E5123` | Contextual |
| B ↔ 8 | `B-123` vs `8-123` | Contextual |

**Recommended Strategy:**
1. **Simple preprocess:** l/I/1 → normalize based on context
2. **Post-validation:** Checksums (DNI, IBAN) reject invalid ones
3. **Do not attempt to correct everything:** Better to reject than invent

### 3.6 Mismatch Preprocessing-Pretraining

**Source:** [Text Preprocessing Guide](https://mbrenndoerfer.com/writing/text-preprocessing-nlp-tokenization-normalization)

> "If you train a model with aggressively preprocessed text but deploy it on minimally preprocessed input, performance will crater."

**Critical for our model:**
- RoBERTa-BNE was pretrained with case-sensitive text
- Do NOT apply lowercase
- DO apply Unicode normalization (NFKC)
- DO remove zero-width characters

---

## 4. Proposed Normalization Pipeline

### 4.1 Order of Operations

```
OCR/Raw Text
    ↓
[1] Remove BOM (U+FEFF)
    ↓
[2] Remove zero-width (U+200B-U+200F, U+2060-U+206F)
    ↓
[3] NFKC normalization (fullwidth → ASCII)
    ↓
[4] Normalize spaces (U+00A0 → space, collapse multiples)
    ↓
[5] Homoglyph mapping (common Cyrillic → Latin)
    ↓
[6] Contextual OCR (DNl → DNI only if context indicates)
    ↓
Normalized Text → NER
```

### 4.2 Python Implementation

```python
import unicodedata
import re

# Characters to remove
ZERO_WIDTH = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

# Cyrillic → Latin homoglyphs
HOMOGLYPHS = {
    '\u0410': 'A',  # А → A
    '\u0412': 'B',  # В → B
    '\u0415': 'E',  # Е → E
    '\u041e': 'O',  # О → O
    '\u0421': 'C',  # С → C
    '\u0425': 'X',  # Х → X
    '\u0430': 'a',  # а → a
    '\u0435': 'e',  # е → e
    '\u043e': 'o',  # о → o
    '\u0441': 'c',  # с → c
    '\u0445': 'x',  # х → x
}

def normalize_text(text: str) -> str:
    """
    Normalize text for NER processing.

    Applies: NFKC, zero-width removal, homoglyph mapping, space normalization.
    Does NOT apply: lowercase (RoBERTa is case-sensitive).
    """
    # 1. Remove BOM and zero-width
    text = ZERO_WIDTH.sub('', text)

    # 2. NFKC normalization (fullwidth → ASCII)
    text = unicodedata.normalize('NFKC', text)

    # 3. Homoglyph mapping
    for cyrillic, latin in HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)

    # 4. Normalize spaces (NBSP → space, collapse multiples)
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)

    # 5. Remove soft hyphens
    text = text.replace('\u00ad', '')

    return text.strip()
```

### 4.3 Validation Tests

| Input | Expected Output | Test |
|-------|-----------------|------|
| `１２３４５６７８Z` | `12345678Z` | Fullwidth |
| `123​456​78Z` | `12345678Z` | Zero-width |
| `12345678Х` | `12345678X` | Cyrillic X |
| `D N I` | `D N I` | Spaces (without collapsing words) |
| `María` | `María` | Accents preserved |

---

## 5. Gap Analysis

### 5.1 Comparison: Current Practice vs Best Practices

| Aspect | Best Practice | Current Implementation | Gap |
|--------|---------------|------------------------|-----|
| NFKC normalization | Apply before NER | Not implemented | **CRITICAL** |
| Zero-width removal | Remove U+200B-F | Not implemented | **CRITICAL** |
| Homoglyph mapping | Cyrillic → Latin | Not implemented | HIGH |
| Space normalization | NBSP → space | Not implemented | MEDIUM |
| Contextual OCR | DNl → DNI | Not implemented | MEDIUM |
| Case preservation | NO lowercase | Correct | ✓ OK |

### 5.2 Estimated Impact

| Correction | Effort | Impact on Tests |
|------------|--------|-----------------|
| NFKC + zero-width | Low (10 lines) | `fullwidth_numbers`: PASS |
| Homoglyph mapping | Low (table) | `cyrillic_o`: PASS (already passes, but more robust) |
| Space normalization | Low | Reduces FPs in tokenization |
| **Total** | **~50 lines Python** | **+5-10% pass rate adversarial** |

---

## 6. Conclusions

### 6.1 Key Findings

1. **NFKC is sufficient** to normalize fullwidth → ASCII without additional code
2. **Zero-width characters** must be explicitly removed (simple regex)
3. **Homoglyphs** require mapping table (Cyrillic → Latin)
4. **Do NOT apply lowercase** - RoBERTa is case-sensitive
5. **Contextual OCR** is complex - better to validate with checksums afterwards

### 6.2 Recommendation for ContextSafe

**Implement `scripts/preprocess/text_normalizer.py`** with:
1. `normalize_text()` function as described above
2. Integrate into inference pipeline BEFORE tokenizer
3. Also apply during training dataset generation

**Priority:** HIGH - Will resolve `fullwidth_numbers` tests and improve general robustness.

---

## 7. References

### Academic Papers

1. **Investigating OCR-Sensitive Neurons to Improve Entity Recognition in Historical Documents**
   - arXiv:2409.16934, ICADL 2024
   - URL: https://arxiv.org/abs/2409.16934

2. **Neural OCR Post-Hoc Correction of Historical Corpora**
   - TACL, MIT Press
   - URL: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00379

### Standards and Specifications

3. **UAX #15: Unicode Normalization Forms**
   - Unicode Consortium
   - URL: https://unicode.org/reports/tr15/

### Technical Resources

4. **Text Normalization: Unicode Forms, Case Folding & Whitespace Handling for NLP**
   - Michael Brenndoerfer, 2024
   - URL: https://mbrenndoerfer.com/writing/text-normalization-unicode-nlp

5. **The Invisible Threat: How Zero-Width Unicode Characters Can Silently Backdoor Your AI-Generated Code**
   - Promptfoo, 2024
   - URL: https://www.promptfoo.dev/blog/invisible-unicode-threats/

6. **OCR Data Entry: Preprocessing Text for NLP Tasks in 2025**
   - Label Your Data
   - URL: https://labelyourdata.com/articles/ocr-data-entry

7. **Zero-width space - Wikipedia**
   - URL: https://en.wikipedia.org/wiki/Zero-width_space

---

**Date:** 2026-01-27
