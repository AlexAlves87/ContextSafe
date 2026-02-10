# Evaluación Adversarial - legal_ner_v2

**Fecha:** 2026-01-23
**Modelo:** legal_ner_v2
**Tests:** 35
**Tiempo total:** 1.4s

---

## Resumen Ejecutivo

### Métricas Entity-Level (seqeval-style)

| Métrica | Valor |
|---------|-------|
| Precision | 0.845 |
| Recall | 0.731 |
| **F1-Score** | **0.784** |
| True Positives | 49 |
| False Positives | 9 |
| False Negatives | 18 |
| Mean Overlap Score | 0.935 |

### Resistencia al Ruido (NoiseBench-style)

| Métrica | Valor | Referencia |
|---------|-------|------------|
| F1 (texto limpio) | 0.800 | - |
| F1 (con ruido) | 0.720 | - |
| Degradación | 0.080 | ≤0.10 esperado |
| Estado | ✅ OK | HAL Science ref |

### Tests por Resultado

| Métrica | Valor |
|---------|-------|
| Tests totales | 35 |
| Pasados | 19 (54.3%) |
| Fallados | 16 (45.7%) |

### Por Categoría (con F1)

| Categoría | Pass Rate | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### Por Dificultad

| Dificultad | Pasados | Total | Tasa |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

---

## Análisis de Errores

### Tests Fallados

| Test ID | Categoría | Missed | FP | Detalle |
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

## Resultados Detallados

### ADVERSARIAL

#### date_in_reference [✅ PASS]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 0 | **Detectado:** 0
**Correctos:** 0 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### example_dni [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 0 | **Detectado:** 1
**Correctos:** 0 | **Perdidos:** 0 | **FP:** 1
**Detalles:** FP: ['12345678X']

#### fictional_person [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 0 | **Detectado:** 1
**Correctos:** 0 | **Perdidos:** 0 | **FP:** 1
**Detalles:** FP: ['Don Quijote de la Mancha']

#### location_as_person [✅ PASS]

**Dificultad:** hard | **Overlap:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Correctos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### mixed_languages [✅ PASS]

**Dificultad:** hard | **Overlap:** 0.94
**Esperado:** 3 | **Detectado:** 3
**Correctos:** 3 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### negation_dni [✅ PASS]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 0 | **Detectado:** 0
**Correctos:** 0 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### numbers_not_dni [✅ PASS]

**Dificultad:** medium | **Overlap:** 0.00
**Esperado:** 0 | **Detectado:** 0
**Correctos:** 0 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### organization_as_person [✅ PASS]

**Dificultad:** medium | **Overlap:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Correctos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

### EDGE_CASE

#### address_floor_door [✅ PASS]

**Dificultad:** medium | **Overlap:** 0.83
**Esperado:** 3 | **Detectado:** 3
**Correctos:** 3 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### date_ordinal [✅ PASS]

**Dificultad:** medium | **Overlap:** 1.00
**Esperado:** 1 | **Detectado:** 2
**Correctos:** 1 | **Perdidos:** 0 | **FP:** 1
**Detalles:** FP: ['El']

#### date_roman_numerals [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 1 | **Detectado:** 0
**Correctos:** 0 | **Perdidos:** 1 | **FP:** 0
**Detalles:** Missed: ['XV de marzo del año MMXXIV']

#### dni_with_spaces [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 1 | **Detectado:** 0
**Correctos:** 0 | **Perdidos:** 1 | **FP:** 0
**Detalles:** Missed: ['12 345 678 Z']

#### dni_without_letter [✅ PASS]

**Dificultad:** medium | **Overlap:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Correctos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### iban_with_spaces [✅ PASS]

**Dificultad:** easy | **Overlap:** 0.91
**Esperado:** 1 | **Detectado:** 1
**Correctos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### phone_international [❌ FAIL]

**Dificultad:** medium | **Overlap:** 1.00
**Esperado:** 2 | **Detectado:** 1
**Correctos:** 1 | **Perdidos:** 1 | **FP:** 0
**Detalles:** Missed: ['0034612345678']

#### single_letter_name [✅ PASS]

**Dificultad:** medium | **Overlap:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Correctos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### very_long_name [✅ PASS]

**Dificultad:** hard | **Overlap:** 1.00
**Esperado:** 1 | **Detectado:** 1
**Correctos:** 1 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

### OCR_CORRUPTION

#### ocr_accent_loss [✅ PASS]

**Dificultad:** easy | **Overlap:** 1.00
**Esperado:** 2 | **Detectado:** 2
**Correctos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### ocr_extra_spaces [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 2 | **Detectado:** 0
**Correctos:** 0 | **Perdidos:** 2 | **FP:** 0
**Detalles:** Missed: ['1 2 3 4 5 6 7 8 Z', 'M a r í a']

#### ocr_letter_substitution [✅ PASS]

**Dificultad:** medium | **Overlap:** 1.00
**Esperado:** 2 | **Detectado:** 2
**Correctos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### ocr_missing_spaces [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.88
**Esperado:** 2 | **Detectado:** 1
**Correctos:** 1 | **Perdidos:** 1 | **FP:** 0
**Detalles:** Missed: ['12345678X']

#### ocr_zero_o_confusion [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 1 | **Detectado:** 0
**Correctos:** 0 | **Perdidos:** 1 | **FP:** 0
**Detalles:** Missed: ['ES91 21O0 0418 45O2 OOO5 1332']

### REAL_WORLD

#### bank_account_clause [❌ FAIL]

**Dificultad:** medium | **Overlap:** 0.88
**Esperado:** 3 | **Detectado:** 2
**Correctos:** 2 | **Perdidos:** 1 | **FP:** 0
**Detalles:** Missed: ['A-98765432']

#### cadastral_reference [✅ PASS]

**Dificultad:** medium | **Overlap:** 1.00
**Esperado:** 2 | **Detectado:** 2
**Correctos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### contract_parties [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.88
**Esperado:** 8 | **Detectado:** 6
**Correctos:** 6 | **Perdidos:** 2 | **FP:** 0
**Detalles:** Missed: ['28013', 'Madrid']

#### ecli_citation [✅ PASS]

**Dificultad:** easy | **Overlap:** 0.90
**Esperado:** 2 | **Detectado:** 3
**Correctos:** 2 | **Perdidos:** 0 | **FP:** 1
**Detalles:** FP: ['Tribunal Supremo']

#### judicial_sentence_header [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.92
**Esperado:** 4 | **Detectado:** 5
**Correctos:** 3 | **Perdidos:** 1 | **FP:** 2
**Detalles:** Missed: ['diez de enero de dos mil veinticuatro']; FP: ['Nº 123/2024', 'Sala Primera del Tribunal Supremo']

#### notarial_header [❌ FAIL]

**Dificultad:** medium | **Overlap:** 1.00
**Esperado:** 4 | **Detectado:** 3
**Correctos:** 3 | **Perdidos:** 1 | **FP:** 0
**Detalles:** Missed: ['quince de marzo de dos mil veinticuatro']

#### professional_ids [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.65
**Esperado:** 4 | **Detectado:** 2
**Correctos:** 1 | **Perdidos:** 3 | **FP:** 1
**Detalles:** Missed: ['12345', 'MIGUEL TORRES', '67890']; FP: ['Colegio de Procuradores de Madrid']

#### social_security [❌ FAIL]

**Dificultad:** easy | **Overlap:** 0.00
**Esperado:** 1 | **Detectado:** 1
**Correctos:** 0 | **Perdidos:** 1 | **FP:** 1
**Detalles:** Missed: ['281234567890']; FP: ['28']

#### testament_comparecencia [✅ PASS]

**Dificultad:** hard | **Overlap:** 0.99
**Esperado:** 5 | **Detectado:** 5
**Correctos:** 5 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### vehicle_clause [✅ PASS]

**Dificultad:** medium | **Overlap:** 0.72
**Esperado:** 2 | **Detectado:** 2
**Correctos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

### UNICODE_EVASION

#### cyrillic_o [✅ PASS]

**Dificultad:** hard | **Overlap:** 0.94
**Esperado:** 2 | **Detectado:** 2
**Correctos:** 2 | **Perdidos:** 0 | **FP:** 0
**Detalles:** OK

#### fullwidth_numbers [❌ FAIL]

**Dificultad:** hard | **Overlap:** 0.00
**Esperado:** 2 | **Detectado:** 0
**Correctos:** 0 | **Perdidos:** 2 | **FP:** 0
**Detalles:** Missed: ['１２３４５６７８Z', 'María']

#### zero_width_space [❌ FAIL]

**Dificultad:** hard | **Overlap:** 1.00
**Esperado:** 2 | **Detectado:** 3
**Correctos:** 2 | **Perdidos:** 0 | **FP:** 1
**Detalles:** FP: ['de']

---

## Referencias

- **seqeval**: Entity-level evaluation metrics for NER
- **NoiseBench (ICLR 2024)**: Real vs simulated noise evaluation
- **HAL Science**: OCR impact assessment (~10pt F1 degradation expected)

**Generado por:** `scripts/evaluate/test_ner_predictor_adversarial.py`
**Fecha:** 2026-01-23