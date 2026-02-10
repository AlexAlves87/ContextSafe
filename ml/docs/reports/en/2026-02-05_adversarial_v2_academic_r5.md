# Adversarial Evaluation v2 (Academic Standards) - legal_ner_v2

**Date:** 2026-02-05
**Model:** legal_ner_v2
**Tests:** 35
**Total time:** 1.4s
**Standard:** SemEval 2013 Task 9

---

## 1. Executive Summary

### 1.1 SemEval 2013 Metrics (Strict Mode)

| Metric | Value |
|--------|-------|
| **F1 (strict)** | **0.545** |
| Precision (strict) | 0.554 |
| Recall (strict) | 0.537 |
| F1 (partial) | 0.705 |

### 1.2 SemEval Counts

| Metric | Value | Description |
|--------|-------|-------------|
| COR | 36 | Correct (exact boundary + type) |
| INC | 1 | Correct boundary, incorrect type |
| PAR | 21 | Partial match (overlap) |
| MIS | 9 | Missing (FN) |
| SPU | 7 | Spurious (FP) |
| **POS** | 67 | Total gold (COR+INC+PAR+MIS) |
| **ACT** | 65 | Total system (COR+INC+PAR+SPU) |

### 1.3 Pass Rate

| Mode | Passed | Total | Rate |
|------|--------|-------|------|
| **Strict** | 17 | 35 | **48.6%** |
| Lenient (v1) | 25 | 35 | 71.4% |

---

## 2. Metrics by Entity Type

| Type | COR | MIS | SPU | Precision | Recall | F1 |
|------|-----|-----|-----|-----------|--------|----|
| ADDRESS | 1 | 2 | 2 | 0.33 | 0.33 | 0.33 |
| CADASTRAL_REF | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| CIF | 0 | 0 | 1 | 0.00 | 0.00 | 0.00 |
| DATE | 2 | 2 | 3 | 0.40 | 0.50 | 0.44 |
| DNI_NIE | 10 | 3 | 1 | 0.91 | 0.77 | 0.83 |
| ECLI | 1 | 1 | 1 | 0.50 | 0.50 | 0.50 |
| IBAN | 1 | 2 | 1 | 0.50 | 0.33 | 0.40 |
| LICENSE_PLATE | 0 | 1 | 1 | 0.00 | 0.00 | 0.00 |
| LOCATION | 10 | 1 | 0 | 1.00 | 0.91 | 0.95 |
| NSS | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| ORGANIZATION | 1 | 2 | 5 | 0.17 | 0.33 | 0.22 |
| PERSON | 6 | 13 | 13 | 0.32 | 0.32 | 0.32 |
| PHONE | 2 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| POSTAL_CODE | 0 | 2 | 1 | 0.00 | 0.00 | 0.00 |
| PROFESSIONAL_ID | 0 | 2 | 0 | 0.00 | 0.00 | 0.00 |

---

## 3. Results by Category

| Category | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 62% | 75% | 4 | 0 | 1 | 0 | 2 | 0.67 |
| edge_case | 67% | 100% | 10 | 0 | 2 | 0 | 1 | 0.80 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0.57 |
| real_world | 20% | 60% | 13 | 1 | 17 | 4 | 4 | 0.37 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0.91 |

## 4. Results by Difficulty

| Difficulty | Strict | Lenient | Total |
|------------|--------|---------|-------|
| easy | 75% | 100% | 4 |
| medium | 58% | 92% | 12 |
| hard | 37% | 53% | 19 |

---

## 5. Failed Tests (Strict Mode)

| Test | Cat | COR | INC | PAR | MIS | SPU | Detail |
|------|-----|-----|-----|-----|-----|-----|--------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 partial matches |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| address_floor_door | edge | 2 | 0 | 1 | 0 | 0 | PAR: 1 partial matches |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Don Quijote de la Mancha'] |
| mixed_languages | adve | 2 | 0 | 1 | 0 | 0 | PAR: 1 partial matches |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 partial match... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| fullwidth_numbers | unic | 1 | 0 | 0 | 1 | 0 | MIS: ['María'] |
| notarial_header | real | 3 | 0 | 1 | 0 | 0 | PAR: 1 partial matches |
| testament_comparecencia | real | 3 | 0 | 2 | 0 | 0 | PAR: 2 partial matches |
| judicial_sentence_header | real | 1 | 0 | 3 | 0 | 1 | SPU: ['Sala Primera del Tribunal Supremo... |
| contract_parties | real | 2 | 0 | 4 | 2 | 0 | MIS: ['28013', 'Madrid']; PAR: 4 partial... |
| bank_account_clause | real | 0 | 1 | 2 | 0 | 0 | INC: 1 type mismatches; PAR: 2 partial m... |
| professional_ids | real | 0 | 0 | 2 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Abogado'... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 partia... |
| vehicle_clause | real | 0 | 0 | 2 | 0 | 0 | PAR: 2 partial matches |

---

## 6. Comparison v1 vs v2

| Metric | v1 (lenient) | v2 (strict) | Difference |
|--------|--------------|-------------|------------|
| Pass rate | 71.4% | 48.6% | +22.9pp |
| F1 | 0.705 | 0.545 | +0.159 |

**Note:** v1 used lenient matching (containment + 80% overlap). v2 uses strict (exact boundary + exact type).

---

## 7. References

- **SemEval 2013 Task 9**: Entity-level evaluation with 4 modes (strict, exact, partial, type)
- **RockNER (EMNLP 2021)**: Adversarial NER evaluation methodology
- **NoiseBench (EMNLP 2024)**: Real noise vs simulated noise benchmark
- **nervaluate**: Python library for SemEval-style NER evaluation

**Date:** 2026-02-05
