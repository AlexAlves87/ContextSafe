# Academic Baseline: Evaluation with SemEval 2013 Standards

**Date:** 2026-02-03
**Author:** AlexAlves87
**Model:** legal_ner_v2 (RoBERTalex fine-tuned)
**Standard:** SemEval 2013 Task 9

---

## 1. Executive Summary

This evaluation establishes the **real baseline** of the model using academic standards (SemEval 2013 strict mode), replacing previous results that used lenient matching.

### Comparison v1 vs v2

| Metric | v1 (lenient) | v2 (strict) | Difference |
|--------|--------------|-------------|------------|
| **Pass Rate** | 54.3% | **28.6%** | **-25.7pp** |
| **F1-Score** | 0.784 | **0.464** | **-0.320** |
| F1 (partial) | - | 0.632 | - |

### Main Conclusion

> **Previous results (F1=0.784, 54.3%) were INFLATED.**
> The real baseline with academic standards is **F1=0.464, 28.6% pass rate**.

---

## 2. Methodology

### 2.1 Experimental Design

| Aspect | Specification |
|--------|---------------|
| Evaluated Model | `legal_ner_v2` (RoBERTalex fine-tuned) |
| Framework | PyTorch 2.0+, Transformers |
| Hardware | CUDA (GPU) |
| Evaluation Standard | SemEval 2013 Task 9 |
| Main Mode | Strict (exact boundary + type) |

### 2.2 Evaluation Dataset

| Category | Tests | Purpose |
|----------|-------|---------|
| edge_case | 9 | Edge conditions (long names, variant formats) |
| adversarial | 8 | Cases designed to confuse (negations, examples) |
| ocr_corruption | 5 | Simulation of OCR errors |
| unicode_evasion | 3 | Evasion attempts with Unicode characters |
| real_world | 10 | Real legal document excerpts |
| **Total** | **35** | - |

### 2.3 Metrics Used

According to SemEval 2013 Task 9:

| Metric | Definition |
|--------|------------|
| COR | Correct: exact boundary AND type |
| INC | Incorrect: exact boundary, incorrect type |
| PAR | Partial: overlapping boundary, any type |
| MIS | Missing: gold entity not detected (FN) |
| SPU | Spurious: detection without gold match (FP) |

**Formulas:**
- Precision (strict) = COR / (COR + INC + PAR + SPU)
- Recall (strict) = COR / (COR + INC + PAR + MIS)
- F1 (strict) = 2 × P × R / (P + R)

### 2.4 Reproducibility

```bash
# Environment
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Dependencies
pip install nervaluate  # Optional, metrics implemented manually

# Execution
python scripts/evaluate/test_ner_predictor_adversarial_v2.py

# Output
# - Console: Results per test with COR/INC/PAR/MIS/SPU
# - Report: docs/reports/YYYY-MM-DD_adversarial_v2_academic_rN.md
```

### 2.5 Difference with Evaluation v1

| Aspect | v1 (lenient) | v2 (strict) |
|--------|--------------|-------------|
| Matching | Containment + 80% char overlap | Normalized exact boundary |
| Type | Required | Required |
| Metrics | TP/FP/FN | COR/INC/PAR/MIS/SPU |
| Standard | Custom | SemEval 2013 Task 9 |

---

## 3. Results

### 3.1 SemEval 2013 Counts

| Metric | Value | Description |
|--------|-------|-------------|
| **COR** | 29 | Correct (exact boundary + type) |
| **INC** | 0 | Correct boundary, incorrect type |
| **PAR** | 21 | Partial match (overlap only) |
| **MIS** | 17 | Missing (FN) |
| **SPU** | 8 | Spurious (FP) |
| **POS** | 67 | Total gold (COR+INC+PAR+MIS) |
| **ACT** | 58 | Total system (COR+INC+PAR+SPU) |

### 3.2 Interpretation

```
                    ┌─────────────────────────────────┐
                    │     GOLD: 67 entities           │
                    │                                 │
  ┌─────────────────┼─────────────────┐               │
  │                 │    COR: 29      │               │
  │   SYSTEM: 58    │  (43% of gold)  │   MIS: 17     │
  │                 │                 │   (25%)       │
  │    SPU: 8       │    PAR: 21      │               │
  │    (14%)        │   (31% overlap) │               │
  └─────────────────┴─────────────────┴───────────────┘
```

**Analysis:**
- Only **43%** of gold entities are detected with exact boundary
- **31%** are detected with partial overlap (v1 counted them as correct)
- **25%** are completely missed
- **14%** of detections are false positives

### 3.3 Formulas Applied

**Strict Mode:**
```
Precision = COR / ACT = 29 / 58 = 0.500
Recall = COR / POS = 29 / 67 = 0.433
F1 = 2 * P * R / (P + R) = 0.464
```

**Partial Mode:**
```
Precision = (COR + 0.5*PAR) / ACT = (29 + 10.5) / 58 = 0.681
Recall = (COR + 0.5*PAR) / POS = (29 + 10.5) / 67 = 0.590
F1 = 2 * P * R / (P + R) = 0.632
```

---

### 3.4 Results by Category

| Category | Strict | Lenient | COR | PAR | MIS | SPU |
|----------|--------|---------|-----|-----|-----|-----|
| adversarial | 75% | 75% | 5 | 1 | 0 | 3 |
| edge_case | 22% | 67% | 6 | 3 | 3 | 1 |
| ocr_corruption | 40% | 40% | 4 | 1 | 4 | 0 |
| real_world | 10% | 50% | 12 | 14 | 8 | 4 |
| unicode_evasion | 0% | 33% | 3 | 1 | 2 | 1 |

**Observations:**
- **real_world**: Biggest strict vs lenient discrepancy (10% vs 50%) - many PAR
- **unicode_evasion**: 0% strict - all detections are partial or incorrect
- **adversarial**: Same in both modes - non-detection tests

---

### 3.5 Results by Difficulty

| Difficulty | Strict | Lenient |
|------------|--------|---------|
| easy | 50% | 75% |
| medium | 42% | 75% |
| hard | 16% | 42% |

**Observation:** The strict vs lenient difference increases with difficulty.

---

## 4. Error Analysis

### 4.1 Partial Matches (PAR)

The 21 partial matches represent detections where the boundary is not exact:

| Type of PAR | Examples | Cause |
|-------------|----------|-------|
| Incomplete name | "José María" vs "José María de la Santísima..." | RoBERTa truncates long names |
| IBAN with spaces | "ES91 2100..." vs "ES912100..." | Space normalization |
| Partial address | "Calle Mayor 15" vs "Calle Mayor 15, 3º B" | Boundary excludes floor/door |
| Person in context | "John Smith" vs "Mr. John Smith" | Prefixes not included |

**Implication:** The model detects the entity but with imprecise boundaries.

---

### 4.2 Failed Tests (Strict)

#### 4.2.1 By SPU (False Positives)

| Test | SPU | Spurious Entities |
|------|-----|-------------------|
| example_dni | 1 | "12345678X" (example context) |
| fictional_person | 1 | "Don Quijote de la Mancha" |
| date_ordinal | 1 | "El" |
| zero_width_space | 1 | "de" |
| judicial_sentence_header | 2 | Legal references |
| professional_ids | 1 | Professional association |
| ecli_citation | 1 | Court |

#### 4.2.2 By MIS (Missing Entities)

| Test | MIS | Missing Entities |
|------|-----|------------------|
| dni_with_spaces | 1 | "12 345 678 Z" |
| phone_international | 1 | "0034612345678" |
| date_roman_numerals | 1 | "XV de marzo del año MMXXIV" |
| ocr_zero_o_confusion | 1 | IBAN with O/0 |
| ocr_extra_spaces | 2 | DNI and name with spaces |
| fullwidth_numbers | 2 | Fullwidth DNI, name |
| notarial_header | 1 | Textual date |

---

## 5. Conclusions and Future Work

### 5.1 Improvement Priorities

| Improvement | Impact on COR | Impact on PAR→COR |
|-------------|---------------|-------------------|
| Text normalization (Unicode) | +2-4 COR | +2-3 PAR→COR |
| Checksum validation | Reduce SPU | - |
| Boundary refinement | - | +10-15 PAR→COR |
| Date augmentation | +3-5 COR | - |

### 5.2 Revised Goal

| Metric | Current | Level 4 Goal |
|--------|---------|--------------|
| F1 (strict) | 0.464 | **≥ 0.70** |
| Pass rate (strict) | 28.6% | **≥ 70%** |

**Gap to close:** +0.236 F1, +41.4pp pass rate

---

### 5.3 Next Steps

1. **Re-evaluate** with TextNormalizer integrated (already prepared)
2. **Implement** boundary refinement to reduce PAR
3. **Add** checksum validation to reduce SPU
4. **Augment** data for textual dates to reduce MIS

---

### 5.4 Lessons Learned

1. **Lenient matching significantly inflates results** (F1 0.784 → 0.464)
2. **PAR is a bigger problem than MIS** (21 vs 17) - imprecise boundaries
3. **Real tests (real_world) have more PAR** - complex documents
4. **Unicode evasion passes no strict tests** - critical area

### 5.5 Value of Academic Standard

Evaluation with SemEval 2013 allows:
- Comparison with academic literature
- Granular diagnosis (COR/INC/PAR/MIS/SPU)
- Precise identification of areas for improvement
- Honest measurement of progress

---

## 6. References

1. **SemEval 2013 Task 9**: Segura-Bedmar et al. "Extraction of Drug-Drug Interactions from Biomedical Texts"
2. **nervaluate**: https://github.com/MantisAI/nervaluate
3. **David Batista Blog**: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Evaluation time:** 1.3s
**Date:** 2026-02-03
