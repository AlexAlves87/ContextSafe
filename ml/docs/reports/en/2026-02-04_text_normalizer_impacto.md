# Impact Evaluation: Text Normalizer

**Date:** 2026-02-04
**Author:** AlexAlves87
**Component:** `TextNormalizer` (Unicode/OCR normalization)
**Standard:** SemEval 2013 Task 9 (strict mode)

---

## 1. Executive Summary

Evaluation of the impact of integrating `TextNormalizer` into the NER pipeline to improve robustness against Unicode characters and OCR artifacts.

### Results

| Metric | Baseline | +Normalizer | Delta | Change |
|--------|----------|-------------|-------|--------|
| **Pass Rate (strict)** | 28.6% | **34.3%** | **+5.7pp** | +20% relative |
| **F1 (strict)** | 0.464 | **0.492** | **+0.028** | +6% relative |
| F1 (partial) | 0.632 | 0.659 | +0.027 | +4.3% relative |
| COR | 29 | 31 | +2 | More exact detections |
| MIS | 17 | 15 | -2 | Fewer missed entities |
| SPU | 8 | 7 | -1 | Fewer false positives |

### Conclusion

> **The TextNormalizer significantly improves the NER model robustness.**
> Pass rate +5.7pp, F1 +0.028. Two Unicode evasion tests now pass.

---

## 2. Methodology

### 2.1 Experimental Design

| Aspect | Specification |
|--------|---------------|
| Independent Variable | TextNormalizer (ON/OFF) |
| Dependent Variable | SemEval 2013 Metrics |
| Model | legal_ner_v2 (RoBERTalex) |
| Dataset | 35 adversarial tests |
| Standard | SemEval 2013 Task 9 (strict) |

### 2.2 Evaluated Component

**File:** `scripts/inference/ner_predictor.py` → function `normalize_text_for_ner()`

**Applied Operations:**
1. Zero-width character removal (U+200B-U+200F, U+2060-U+206F, U+FEFF)
2. NFKC normalization (fullwidth → ASCII)
3. Homoglyph mapping (Cyrillic → Latin)
4. Space normalization (NBSP → space, collapse multiple)
5. Soft hyphen removal

### 2.3 Reproducibility

```bash
# Environment
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Execution
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

---

## 3. Results

### 3.1 Detailed Comparison by SemEval Metric

| Metric | Baseline | +Normalizer | Delta |
|--------|----------|-------------|-------|
| COR (Correct) | 29 | 31 | **+2** |
| INC (Incorrect) | 0 | 0 | 0 |
| PAR (Partial) | 21 | 21 | 0 |
| MIS (Missing) | 17 | 15 | **-2** |
| SPU (Spurious) | 8 | 7 | **-1** |
| POS (Possible) | 67 | 67 | 0 |
| ACT (Actual) | 58 | 59 | +1 |

### 3.2 Improved Tests

| Test | Baseline | +Normalizer | Improvement |
|------|----------|-------------|-------------|
| `cyrillic_o` | ❌ COR:1 PAR:1 | ✅ COR:2 | **Homoglyph mapping works** |
| `zero_width_space` | ❌ COR:2 SPU:1 | ✅ COR:2 SPU:0 | **Zero-width removal works** |
| `fullwidth_numbers` | ❌ MIS:2 | ❌ COR:1 MIS:1 | Partial improvement (+1 COR) |

### 3.3 Tests Without Significant Change

| Test | Status | Reason |
|------|--------|--------|
| `ocr_extra_spaces` | ❌ MIS:2 | Requires space normalization within entities |
| `ocr_zero_o_confusion` | ❌ MIS:1 | Requires contextual OCR O↔0 correction |
| `dni_with_spaces` | ❌ MIS:1 | Internal spaces in DNI are not collapsed |

### 3.4 Results by Category

| Category | Baseline Strict | +Normalizer Strict | Delta |
|----------|-----------------|--------------------|-------|
| adversarial | 75% | 75% | 0 |
| edge_case | 22% | 22% | 0 |
| ocr_corruption | 40% | 40% | 0 |
| real_world | 10% | 10% | 0 |
| **unicode_evasion** | 0% | **67%** | **+67pp** |

**Key Finding:** Impact is concentrated in `unicode_evasion` (+67pp), which was the main goal.

---

## 4. Error Analysis

### 4.1 Test `fullwidth_numbers` (Partial Improvement)

**Input:** `"DNI １２３４５６７８Z de María."`

**Expected:**
- `"１２３４５６７８Z"` → DNI_NIE
- `"María"` → PERSON

**Detected (with normalizer):**
- `"12345678Z"` → DNI_NIE ✅ (normalized match)
- `"María"` → MIS ❌

**Analysis:** The DNI is correctly detected after NFKC. The name "María" is missed because the model fails to detect it (model issue, not normalizer).

### 4.2 Persistently Failing Tests

| Test | Issue | Required Solution |
|------|-------|-------------------|
| `dni_with_spaces` | "12 345 678 Z" not recognized | Regex for DNI with spaces |
| `date_roman_numerals` | Dates with Roman numerals | Data augmentation |
| `ocr_zero_o_confusion` | IBAN with mixed O/0 | OCR post-correction |

---

## 5. Conclusions and Future Work

### 5.1 Conclusions

1. **TextNormalizer meets its goal** for Unicode evasion:
   - `cyrillic_o`: ❌ → ✅
   - `zero_width_space`: ❌ → ✅
   - `unicode_evasion` category: 0% → 67%

2. **Moderate but positive global impact:**
   - F1 strict: +0.028 (+6%)
   - Pass rate: +5.7pp (+20% relative)

3. **Does not solve OCR problems** (expected):
   - `ocr_extra_spaces`, `ocr_zero_o_confusion` require additional techniques

### 5.2 Future Work

| Priority | Improvement | Estimated Impact |
|----------|-------------|------------------|
| HIGH | Regex for DNI/IBAN with spaces | +2-3 COR |
| HIGH | Checksum validation (reduce SPU) | -2-3 SPU |
| MEDIUM | Data augmentation for textual dates | +3-4 COR |
| LOW | OCR post-correction (O↔0) | +1-2 COR |

### 5.3 Updated Goal

| Metric | Before | Now | Level 4 Goal | Gap |
|--------|--------|-----|--------------|-----|
| F1 (strict) | 0.464 | **0.492** | ≥0.70 | -0.208 |
| Pass rate | 28.6% | **34.3%** | ≥70% | -35.7pp |

---

## 6. References

1. **Base research:** `docs/reports/2026-01-27_investigacion_text_normalization.md`
2. **Standalone component:** `scripts/preprocess/text_normalizer.py`
3. **Production integration:** `src/contextsafe/infrastructure/nlp/text_normalizer.py`
4. **UAX #15 Unicode Normalization Forms:** https://unicode.org/reports/tr15/

---

**Evaluation time:** 1.3s
**Date:** 2026-02-04
