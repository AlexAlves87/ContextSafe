# Adversarial Evaluation - legal_ner_v2

**Date:** 2026-01-23
**Model:** legal_ner_v2
**Tests:** 35
**Total Time:** 1.4s

---

## Executive Summary

### Entity-Level Metrics (seqeval-style)

| Metric | Value |
|---------|-------|
| Precision | 0.845 |
| Recall | 0.731 |
| **F1-Score** | **0.784** |
| True Positives | 49 |
| False Positives | 9 |
| False Negatives | 18 |
| Mean Overlap Score | 0.935 |

### Noise Resistance (NoiseBench-style)

| Metric | Value | Reference |
|---------|-------|------------|
| F1 (clean text) | 0.800 | - |
| F1 (noisy) | 0.720 | - |
| Degradation | 0.080 | ≤0.10 expected |
| Status | ✅ OK | HAL Science ref |

### Tests by Result

| Metric | Value |
|---------|-------|
| Total Tests | 35 |
| Passed | 19 (54.3%) |
| Failed | 16 (45.7%) |

### By Category (with F1)

| Category | Pass Rate | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### By Difficulty

| Difficulty | Passed | Total | Rate |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

---

## Error Analysis

### Failed Tests

| Test ID | Category | Missed | FP | Detail |
|---------|-----------|--------|----|---------|
| dni_with_spaces | edge_case | 1 | 0 | Missed: ['12 345 678 Z'] |
| phone_international | edge_case | 1 | 0 | Missed: ['0034612345678'] |
| date_roman_numerals | edge_case | 1 | 0 | Missed: ['XV de marzo del año MMXXIV'] |
| example_dni | adversarial | 0 | 1 | FP: ['12345678X'] |
| fictional_person | adversarial | 0 | 1 | FP: ['Don Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_corruption | 1 | 0 | Missed: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_corruption | 1 | 0 | Missed: ['12345678X'] |
| ocr_extra_spaces | ocr_corruption | 2 | 0 | Missed: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| zero_width_space | unicode_evasion | 0 | 1 | FP: ['de'] |
| fullwidth_numbers | unicode_evasion | 2 | 0 | Missed: ['１２３４５６７８Z', 'María'] |
| notarial_header | real_world | 1 | 0 | Missed: ['quince de marzo de dos mil veinticuatro'... |
| judicial_sentence_header | real_world | 1 | 2 | Missed: ['diez de enero de dos mil veinticuatro'];... |
| contract_parties | real_world | 2 | 0 | Missed: ['28013', 'Madrid'] |
| bank_account_clause | real_world | 1 | 0 | Missed: ['A-98765432'] |
| professional_ids | real_world | 3 | 1 | Missed: ['12345', 'MIGUEL TORRES', '67890']; FP: [... |
| social_security | real_world | 1 | 1 | Missed: ['281234567890']; FP: ['28'] |

---

## Detailed Results

### ADVERSARIAL

#### date_in_reference [✅ PASS]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 0 | **Detected:** 0
**Correct:** 0 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### example_dni [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 0 | **Detected:** 1
**Correct:** 0 | **Missed:** 0 | **FP:** 1
**Details:** FP: ['12345678X']

#### fictional_person [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 0 | **Detected:** 1
**Correct:** 0 | **Missed:** 0 | **FP:** 1
**Details:** FP: ['Don Quijote de la Mancha']

#### location_as_person [✅ PASS]

**Difficulty:** hard | **Overlap:** 1.00
**Expected:** 1 | **Detected:** 1
**Correct:** 1 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### mixed_languages [✅ PASS]

**Difficulty:** hard | **Overlap:** 0.94
**Expected:** 3 | **Detected:** 3
**Correct:** 3 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### negation_dni [✅ PASS]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 0 | **Detected:** 0
**Correct:** 0 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### numbers_not_dni [✅ PASS]

**Difficulty:** medium | **Overlap:** 0.00
**Expected:** 0 | **Detected:** 0
**Correct:** 0 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### organization_as_person [✅ PASS]

**Difficulty:** medium | **Overlap:** 1.00
**Expected:** 1 | **Detected:** 1
**Correct:** 1 | **Missed:** 0 | **FP:** 0
**Details:** OK

### EDGE_CASE

#### address_floor_door [✅ PASS]

**Difficulty:** medium | **Overlap:** 0.83
**Expected:** 3 | **Detected:** 3
**Correct:** 3 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### date_ordinal [✅ PASS]

**Difficulty:** medium | **Overlap:** 1.00
**Expected:** 1 | **Detected:** 2
**Correct:** 1 | **Missed:** 0 | **FP:** 1
**Details:** FP: ['El']

#### date_roman_numerals [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 1 | **Detected:** 0
**Correct:** 0 | **Missed:** 1 | **FP:** 0
**Details:** Missed: ['XV de marzo del año MMXXIV']

#### dni_with_spaces [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 1 | **Detected:** 0
**Correct:** 0 | **Missed:** 1 | **FP:** 0
**Details:** Missed: ['12 345 678 Z']

#### dni_without_letter [✅ PASS]

**Difficulty:** medium | **Overlap:** 1.00
**Expected:** 1 | **Detected:** 1
**Correct:** 1 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### iban_with_spaces [✅ PASS]

**Difficulty:** easy | **Overlap:** 0.91
**Expected:** 1 | **Detected:** 1
**Correct:** 1 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### phone_international [❌ FAIL]

**Difficulty:** medium | **Overlap:** 1.00
**Expected:** 2 | **Detected:** 1
**Correct:** 1 | **Missed:** 1 | **FP:** 0
**Details:** Missed: ['0034612345678']

#### single_letter_name [✅ PASS]

**Difficulty:** medium | **Overlap:** 1.00
**Expected:** 1 | **Detected:** 1
**Correct:** 1 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### very_long_name [✅ PASS]

**Difficulty:** hard | **Overlap:** 1.00
**Expected:** 1 | **Detected:** 1
**Correct:** 1 | **Missed:** 0 | **FP:** 0
**Details:** OK

### OCR_CORRUPTION

#### ocr_accent_loss [✅ PASS]

**Difficulty:** easy | **Overlap:** 1.00
**Expected:** 2 | **Detected:** 2
**Correct:** 2 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### ocr_extra_spaces [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 2 | **Detected:** 0
**Correct:** 0 | **Missed:** 2 | **FP:** 0
**Details:** Missed: ['1 2 3 4 5 6 7 8 Z', 'M a r í a']

#### ocr_letter_substitution [✅ PASS]

**Difficulty:** medium | **Overlap:** 1.00
**Expected:** 2 | **Detected:** 2
**Correct:** 2 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### ocr_missing_spaces [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.88
**Expected:** 2 | **Detected:** 1
**Correct:** 1 | **Missed:** 1 | **FP:** 0
**Details:** Missed: ['12345678X']

#### ocr_zero_o_confusion [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 1 | **Detected:** 0
**Correct:** 0 | **Missed:** 1 | **FP:** 0
**Details:** Missed: ['ES91 21O0 0418 45O2 OOO5 1332']

### REAL_WORLD

#### bank_account_clause [❌ FAIL]

**Difficulty:** medium | **Overlap:** 0.88
**Expected:** 3 | **Detected:** 2
**Correct:** 2 | **Missed:** 1 | **FP:** 0
**Details:** Missed: ['A-98765432']

#### cadastral_reference [✅ PASS]

**Difficulty:** medium | **Overlap:** 1.00
**Expected:** 2 | **Detected:** 2
**Correct:** 2 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### contract_parties [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.88
**Expected:** 8 | **Detected:** 6
**Correct:** 6 | **Missed:** 2 | **FP:** 0
**Details:** Missed: ['28013', 'Madrid']

#### ecli_citation [✅ PASS]

**Difficulty:** easy | **Overlap:** 0.90
**Expected:** 2 | **Detected:** 3
**Correct:** 2 | **Missed:** 0 | **FP:** 1
**Details:** FP: ['Tribunal Supremo']

#### judicial_sentence_header [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.92
**Expected:** 4 | **Detected:** 5
**Correct:** 3 | **Missed:** 1 | **FP:** 2
**Details:** Missed: ['diez de enero de dos mil veinticuatro']; FP: ['Nº 123/2024', 'Sala Primera del Tribunal Supremo']

#### notarial_header [❌ FAIL]

**Difficulty:** medium | **Overlap:** 1.00
**Expected:** 4 | **Detected:** 3
**Correct:** 3 | **Missed:** 1 | **FP:** 0
**Details:** Missed: ['quince de marzo de dos mil veinticuatro']

#### professional_ids [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.65
**Expected:** 4 | **Detected:** 2
**Correct:** 1 | **Missed:** 3 | **FP:** 1
**Details:** Missed: ['12345', 'MIGUEL TORRES', '67890']; FP: ['Colegio de Procuradores de Madrid']

#### social_security [❌ FAIL]

**Difficulty:** easy | **Overlap:** 0.00
**Expected:** 1 | **Detected:** 1
**Correct:** 0 | **Missed:** 1 | **FP:** 1
**Details:** Missed: ['281234567890']; FP: ['28']

#### testament_comparecencia [✅ PASS]

**Difficulty:** hard | **Overlap:** 0.99
**Expected:** 5 | **Detected:** 5
**Correct:** 5 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### vehicle_clause [✅ PASS]

**Difficulty:** medium | **Overlap:** 0.72
**Expected:** 2 | **Detected:** 2
**Correct:** 2 | **Missed:** 0 | **FP:** 0
**Details:** OK

### UNICODE_EVASION

#### cyrillic_o [✅ PASS]

**Difficulty:** hard | **Overlap:** 0.94
**Expected:** 2 | **Detected:** 2
**Correct:** 2 | **Missed:** 0 | **FP:** 0
**Details:** OK

#### fullwidth_numbers [❌ FAIL]

**Difficulty:** hard | **Overlap:** 0.00
**Expected:** 2 | **Detected:** 0
**Correct:** 0 | **Missed:** 2 | **FP:** 0
**Details:** Missed: ['１２３４５６７８Z', 'María']

#### zero_width_space [❌ FAIL]

**Difficulty:** hard | **Overlap:** 1.00
**Expected:** 2 | **Detected:** 3
**Correct:** 2 | **Missed:** 0 | **FP:** 1
**Details:** FP: ['de']

---

## References

- **seqeval**: Entity-level evaluation metrics for NER
- **NoiseBench (ICLR 2024)**: Real vs simulated noise evaluation
- **HAL Science**: OCR impact assessment (~10pt F1 degradation expected)

**Date:** 2026-01-23
