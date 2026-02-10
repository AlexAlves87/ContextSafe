# Baseline Adversarial Analysis: legal_ner_v2

**Date:** 2026-01-23
**Author:** AlexAlves87
**Version:** 1.0.0
**Evaluated Model:** `legal_ner_v2` (RoBERTalex fine-tuned)

---

## 1. Executive Summary

This document presents the results of the adversarial evaluation of the `legal_ner_v2` model for PII detection in Spanish legal texts. The objective is to establish a robustness baseline before implementing improvements.

### Key Findings

| Metric | Value | Interpretation |
|---------|-------|----------------|
| F1-Score (entity-level) | **0.784** | Acceptable baseline |
| Precision | 0.845 | Conservative model |
| Recall | 0.731 | Priority improvement area |
| Noise degradation | 0.080 | Within expected threshold (≤0.10) |
| Test pass rate | 54.3% (19/35) | Level 4 not passed |

### Conclusion

The model **does NOT pass** Level 4 validation (adversarial). Improvements are required in:
1. Input normalization (Unicode, spaces)
2. Spanish textual date recognition
3. Specific patterns for NSS and CIF

---

## 2. Methodology

### 2.1 Experimental Design

35 adversarial test cases were designed, distributed across 5 categories:

| Category | Tests | Purpose |
|-----------|-------|-----------|
| `edge_case` | 9 | Boundary conditions (long names, variant formats) |
| `adversarial` | 8 | Cases designed to confuse (negations, examples) |
| `ocr_corruption` | 5 | OCR error simulation |
| `unicode_evasion` | 3 | Evasion attempts with similar characters |
| `real_world` | 10 | Extracts from real legal documents |

### 2.2 Difficulty Levels

| Level | Success Criteria | Tests |
|-------|-------------------|-------|
| `easy` | Detect all expected entities | 4 |
| `medium` | Detect all expected entities | 12 |
| `hard` | Detect all entities AND zero false positives | 19 |

### 2.3 Metrics Used

1. **Entity-level F1** (seqeval-style): Precision, Recall, F1 calculated at full entity level, not token.

2. **Overlap Score**: Ratio of matching characters between expected and detected entity (Jaccard over characters).

3. **Noise Degradation** (NoiseBench-style): F1 difference between "clean" categories (`edge_case`, `adversarial`, `real_world`) and "noisy" ones (`ocr_corruption`, `unicode_evasion`).

### 2.4 Execution Environment

| Component | Specification |
|------------|----------------|
| Hardware | CUDA (GPU) |
| Model | `legal_ner_v2` (RoBERTalex) |
| Framework | PyTorch 2.0+, Transformers |
| Load time | 1.6s |
| Evaluation time | 1.5s (35 tests) |

### 2.5 Reproducibility

```bash
cd ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

The script automatically generates a report in `docs/reports/`.

---

## 3. Results

### 3.1 Aggregated Metrics

| Metric | Value |
|---------|-------|
| True Positives | 49 |
| False Positives | 9 |
| False Negatives | 18 |
| **Precision** | 0.845 |
| **Recall** | 0.731 |
| **F1-Score** | 0.784 |
| Mean Overlap Score | 0.935 |

### 3.2 Results by Category

| Category | Pass Rate | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### 3.3 Results by Difficulty

| Difficulty | Passed | Total | Rate |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

### 3.4 Noise Resistance Analysis

| Metric | Value | Reference |
|---------|-------|------------|
| F1 (clean text) | 0.800 | - |
| F1 (noisy) | 0.720 | - |
| **Degradation** | 0.080 | ≤0.10 (HAL Science) |
| Status | **OK** | Within threshold |

---

## 4. Error Analysis

### 4.1 Failure Taxonomy

5 recurrent failure patterns were identified:

#### Pattern 1: Dates in Spanish Textual Format

| Test | Missed Entity |
|------|-----------------|
| `date_roman_numerals` | "XV de marzo del año MMXXIV" |
| `notarial_header` | "quince de marzo de dos mil veinticuatro" |
| `judicial_sentence_header` | "diez de enero de dos mil veinticuatro" |

**Root cause:** The model was trained mainly with numeric date formats (DD/MM/YYYY). Dates written in Spanish notarial style are not represented in the training corpus.

**Impact:** High in notarial and judicial documents where this format is standard.

#### Pattern 2: Extreme OCR Corruption

| Test | Missed Entity |
|------|-----------------|
| `ocr_extra_spaces` | "1 2 3 4 5 6 7 8 Z", "M a r í a" |
| `ocr_missing_spaces` | "12345678X" (in concatenated text) |
| `ocr_zero_o_confusion` | "ES91 21O0 0418 45O2 OOO5 1332" |

**Root cause:** RoBERTa's tokenizer does not handle text with anomalous spacing well. O/0 confusion breaks IBAN regex patterns.

**Impact:** Medium. Low-quality scanned documents.

#### Pattern 3: Unicode Evasion

| Test | Missed Entity |
|------|-----------------|
| `fullwidth_numbers` | "１２３４５６７８Z" (U+FF11-U+FF18) |

**Root cause:** No Unicode normalization prior to NER. Fullwidth digits (U+FF10-U+FF19) are not recognized as numbers.

**Impact:** Low in production, but critical for security (intentional evasion).

#### Pattern 4: Specific Spanish Identifiers

| Test | Missed Entity |
|------|-----------------|
| `social_security` | "281234567890" (NSS) |
| `bank_account_clause` | "A-98765432" (CIF) |
| `professional_ids` | "12345", "67890" (collegiate numbers) |

**Root cause:** Infrequent patterns in the training corpus. Spanish NSS has a specific format (12 digits) that was not learned.

**Impact:** High for labor and commercial documents.

#### Pattern 5: Contextual False Positives

| Test | False Entity |
|------|---------------|
| `example_dni` | "12345678X" (context: "illustrative example") |
| `fictional_person` | "Don Quijote de la Mancha" |

**Root cause:** The model detects patterns without considering semantic context (negations, examples, fiction).

**Impact:** Medium. Causes unnecessary anonymization.

### 4.2 Confusion Matrix by Entity Type

| Type | TP | FP | FN | Observation |
|------|----|----|----|----|
| PERSON | 15 | 2 | 2 | Good, fails on fiction |
| DNI_NIE | 8 | 1 | 4 | Fails on variant formats |
| LOCATION | 6 | 0 | 2 | Fails on isolated ZIP codes |
| DATE | 3 | 0 | 4 | Fails on textual format |
| IBAN | 2 | 0 | 1 | Fails with OCR |
| ORGANIZATION | 5 | 2 | 0 | Confuses with courts |
| NSS | 0 | 0 | 1 | Does not detect |
| PROFESSIONAL_ID | 0 | 0 | 2 | Does not detect |
| Others | 10 | 4 | 2 | - |

---

## 5. Conclusions

### 5.1 Current State

The `legal_ner_v2` model presents an **F1 of 0.784** in adversarial evaluation, with the following characteristics:

- **Strengths:**
  - High precision (0.845) - few false positives
  - Good noise resistance (degradation 0.080)
  - Excellent on compound names and addresses

- **Weaknesses:**
  - Insufficient recall (0.731) - misses entities
  - Does not recognize dates in Spanish textual format
  - Vulnerable to Unicode evasion (fullwidth)
  - Does not detect NSS or collegiate numbers

### 5.2 Validation Level

| Level | Status | Criteria |
|-------|--------|----------|
| Level 1: Unit Tests | ✅ | Individual functions |
| Level 2: Integration | ✅ | Complete pipeline |
| Level 3: Benchmark | ✅ | F1 > 0.75 |
| **Level 4: Adversarial** | ❌ | Pass rate < 70% |
| Level 5: Production-like | ⏸️ | Pending |

**Conclusion:** The model is **NOT ready for production** according to project criteria (Level 4 mandatory).

### 5.3 Future Work

#### HIGH Priority (estimated impact > 3pts F1)

1. **Unicode normalization in preprocessing**
   - Convert fullwidth to ASCII
   - Remove zero-width characters
   - Normalize O/0 in numeric contexts

2. **Textual date augmentation**
   - Generate variants: "primero de enero", "XV de marzo"
   - Include Roman numerals
   - Fine-tune with augmented corpus

3. **Regex patterns for NSS/CIF**
   - Add to CompositeNerAdapter
   - NSS: `\d{12}` in context "Seguridad Social"
   - CIF: `[A-Z]-?\d{8}` in company context

#### MEDIUM Priority (estimated impact 1-3pts F1)

4. **OCR space normalization**
   - Detect and collapse excessive spaces
   - Reconstruct fragmented tokens

5. **Post-process filter for "example" contexts**
   - Detect phrases: "por ejemplo", "ilustrativo", "formato"
   - Suppress entities in those contexts

#### LOW Priority (edge cases)

6. **Fictional character gazetteer**
   - Don Quijote, Sancho Panza, etc.
   - Post-process filter

7. **Dates with Roman numerals**
   - Specific regex for old notarial style

---

## 6. References

1. **seqeval** - Entity-level evaluation metrics for sequence labeling. https://github.com/chakki-works/seqeval

2. **NoiseBench (ICLR 2024)** - Benchmark for evaluating NLP models under realistic noise conditions.

3. **HAL Science** - Study on OCR impact in NER tasks. Establishes expected degradation of ~10pts F1.

4. **RoBERTalex** - Spanish legal domain RoBERTa model. Basis of the evaluated model.

5. **Project guidelines v1.0.0** - ML preparation methodology for ContextSafe.

---

## Appendices

### A. Test Configuration

```yaml
total_tests: 35
categories:
  edge_case: 9
  adversarial: 8
  ocr_corruption: 5
  unicode_evasion: 3
  real_world: 10
difficulty_distribution:
  easy: 4
  medium: 12
  hard: 19
```

### B. Reproduction Command

```bash
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

### C. Generated Files

- Automatic report: `docs/reports/2026-01-23_adversarial_ner_v2.md`
- Academic analysis: `docs/reports/2026-01-23_baseline_adversarial_analysis.md` (this document)

---

**Date:** 2026-01-23
