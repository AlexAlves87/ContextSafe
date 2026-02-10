# GLiNER-PII Baseline Evaluation

**Fecha:** 2026-01-24
**Modelo:** knowledgator/gliner-pii-base-v1.0
**Threshold:** 0.3 (balanced)
**Tests:** 35
**Tiempo:** 3.8s

---

## 1. Resumen Ejecutivo

### Comparación con legal_ner_v2

| Modelo | F1 Strict | Precision | Recall | Pass Rate |
|--------|-----------|-----------|--------|-----------|
| **GLiNER-PII-base** | **0.325** | 0.287 | 0.373 | 11.4% |
| legal_ner_v2 | 0.788 | - | - | 60.0% |
| **Diferencia** | **-0.463** | - | - | -48.6pp |

### Conteos SemEval

| Métrica | Valor | Descripción |
|---------|-------|-------------|
| COR | 25 | Correctos (boundary + type) |
| INC | 4 | Boundary OK, type incorrecto |
| PAR | 24 | Match parcial |
| MIS | 14 | Perdidos (FN) |
| SPU | 34 | Espurios (FP) |

---

## 2. Resultados por Categoría

| Categoría | Strict | COR | INC | PAR | MIS | SPU |
|-----------|--------|-----|-----|-----|-----|-----|
| edge_case | 22% | 5 | 0 | 3 | 4 | 5 |
| adversarial | 0% | 1 | 0 | 3 | 1 | 9 |
| ocr_corruption | 0% | 2 | 0 | 4 | 3 | 2 |
| unicode_evasion | 67% | 5 | 0 | 1 | 0 | 1 |
| real_world | 0% | 12 | 4 | 13 | 6 | 17 |

---

## 3. Tests Fallados (Strict)

| Test | Cat | COR | INC | PAR | MIS | SPU | Detalle |
|------|-----|-----|-----|-----|-----|-----|---------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 5 | SPU: ['Don', 'Trinidad', 'Fernández... |
| dni_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['12 345 678 Z'] |
| iban_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 2100 0418 4502 0005 133... |
| phone_international | edge | 1 | 0 | 0 | 1 | 0 | MIS: ['0034612345678'] |
| date_roman_numerals | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| date_ordinal | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| address_floor_door | edge | 2 | 0 | 0 | 1 | 0 | MIS: ['Calle Mayor 15, 3º B'] |
| negation_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['NIE'] |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Don'] |
| organization_as_pers | adve | 0 | 0 | 1 | 0 | 1 | SPU: ['demanda']; PAR: 1 |
| location_as_person | adve | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| date_in_reference | adve | 0 | 0 | 0 | 0 | 2 | SPU: ['15/2022', '12 de julio'] |
| numbers_not_dni | adve | 0 | 0 | 0 | 0 | 2 | SPU: ['12345678', '9'] |
| mixed_languages | adve | 1 | 0 | 1 | 1 | 1 | MIS: ['UK123456789']; SPU: ['Smith'... |
| ocr_letter_substitut | ocr_ | 1 | 0 | 1 | 0 | 2 | SPU: ['DNl', 'García']; PAR: 1 |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 1 | 0 | 0 | PAR: 1 |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í... |
| ocr_accent_loss | ocr_ | 1 | 0 | 1 | 0 | 0 | PAR: 1 |
| ... | ... | ... | ... | ... | ... | ... | (11 más) |

---

## 4. Análisis

### Fortalezas de GLiNER

- Zero-shot: No requiere entrenamiento para nuevos tipos de entidad
- Multilingüe: Soporte nativo para español
- Labels flexibles: Especificados en runtime

### Debilidades observadas

- Formatos españoles específicos (DNI, NIE, IBAN con espacios)
- Fechas textuales en español (XV de marzo de MMXXIV)
- Identificadores legales españoles (ECLI, referencias catastrales)
- Contexto negativo (NO tener DNI)

### Recomendación

legal_ner_v2 supera a GLiNER zero-shot (0.325 F1). El fine-tuning específico para dominio legal español aporta valor.

> **Nota posterior (2026-02-04):** Se probó LoRA fine-tuning de Legal-XLM-RoBERTa-base: F1 0.016 adversarial (overfitting severo). Descartado. El modelo base del pipeline sigue siendo RoBERTa-BNE CAPITEL NER (`legal_ner_v2`).

---

## 5. Configuración

```python
# Labels usados (mapping a tipos ContextSafe)
GLINER_LABELS = ['phone_number', 'national id', 'zip code', 'company_name', 'date_of_birth', 'certificate_license_number', 'social security number', 'account_number', 'case number', 'ssn', 'address', 'location state', 'postal code', 'email', 'vehicle_identifier', 'city', 'phone number', 'date', 'vehicle id', 'dob', 'professional id', 'license number', 'property id', 'email address', 'location city', 'organization', 'name', 'company', 'national_id', 'court case id', 'iban', 'street_address', 'last name', 'location address', 'postcode', 'license_plate', 'unique_identifier', 'first name', 'country', 'cadastral reference', 'bank account']

# Threshold
threshold = 0.3  # Balanced (production recommended)
```

---

**Generado por:** `scripts/evaluate/evaluate_gliner_baseline.py`
**Fecha:** 2026-01-24