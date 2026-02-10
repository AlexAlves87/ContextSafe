# Evaluación Adversarial v2 (Academic Standards) - legal_ner_v2

**Fecha:** 2026-02-05
**Modelo:** legal_ner_v2
**Tests:** 35
**Tiempo total:** 1.4s
**Estándar:** SemEval 2013 Task 9

---

## 1. Resumen Ejecutivo

### 1.1 Métricas SemEval 2013 (Strict Mode)

| Métrica | Valor |
|---------|-------|
| **F1 (strict)** | **0.545** |
| Precision (strict) | 0.554 |
| Recall (strict) | 0.537 |
| F1 (partial) | 0.705 |

### 1.2 Conteos SemEval

| Métrica | Valor | Descripción |
|---------|-------|-------------|
| COR | 36 | Correctos (boundary + type exactos) |
| INC | 1 | Boundary correcto, type incorrecto |
| PAR | 21 | Match parcial (overlap) |
| MIS | 9 | Perdidos (FN) |
| SPU | 7 | Espurios (FP) |
| **POS** | 67 | Total gold (COR+INC+PAR+MIS) |
| **ACT** | 65 | Total sistema (COR+INC+PAR+SPU) |

### 1.3 Pass Rate

| Modo | Pasados | Total | Tasa |
|------|---------|-------|------|
| **Strict** | 17 | 35 | **48.6%** |
| Lenient (v1) | 25 | 35 | 71.4% |

---

## 2. Métricas por Tipo de Entidad

| Tipo | COR | MIS | SPU | Precision | Recall | F1 |
|------|-----|-----|-----|-----------|--------|-----|
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

## 3. Resultados por Categoría

| Categoría | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 62% | 75% | 4 | 0 | 1 | 0 | 2 | 0.67 |
| edge_case | 67% | 100% | 10 | 0 | 2 | 0 | 1 | 0.80 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0.57 |
| real_world | 20% | 60% | 13 | 1 | 17 | 4 | 4 | 0.37 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0.91 |

## 4. Resultados por Dificultad

| Dificultad | Strict | Lenient | Total |
|------------|--------|---------|-------|
| easy | 75% | 100% | 4 |
| medium | 58% | 92% | 12 |
| hard | 37% | 53% | 19 |

---

## 5. Tests Fallados (Strict Mode)

| Test | Cat | COR | INC | PAR | MIS | SPU | Detalle |
|------|-----|-----|-----|-----|-----|-----|---------|
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

## 6. Comparación v1 vs v2

| Métrica | v1 (lenient) | v2 (strict) | Diferencia |
|---------|--------------|-------------|------------|
| Pass rate | 71.4% | 48.6% | +22.9pp |
| F1 | 0.705 | 0.545 | +0.159 |

**Nota:** v1 usaba matching lenient (containment + 80% overlap). v2 usa strict (exact boundary + exact type).

---

## 7. Referencias

- **SemEval 2013 Task 9**: Entity-level evaluation with 4 modes (strict, exact, partial, type)
- **RockNER (EMNLP 2021)**: Adversarial NER evaluation methodology
- **NoiseBench (EMNLP 2024)**: Real noise vs simulated noise benchmark
- **nervaluate**: Python library for SemEval-style NER evaluation

**Generado por:** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Fecha:** 2026-02-05