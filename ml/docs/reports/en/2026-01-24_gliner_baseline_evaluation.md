# GLiNER-PII Baseline Evaluation

**Date:** 2026-01-24
**Model:** knowledgator/gliner-pii-base-v1.0
**Threshold:** 0.3 (balanced)
**Tests:** 35
**Time:** 3.8s

---

## 1. Executive Summary

### Comparison with legal_ner_v2

| Model | Strict F1 | Precision | Recall | Pass Rate |
|-------|-----------|-----------|--------|-----------|
| **GLiNER-PII-base** | **0.325** | 0.287 | 0.373 | 11.4% |
| legal_ner_v2 | 0.788 | - | - | 60.0% |
| **Difference** | **-0.463** | - | - | -48.6pp |

### SemEval Counts

| Metric | Value | Description |
|--------|-------|-------------|
| COR | 25 | Correct (boundary + type) |
| INC | 4 | Boundary OK, type incorrect |
| PAR | 24 | Partial match |
| MIS | 14 | Missed (FN) |
| SPU | 34 | Spurious (FP) |

---

## 2. Results by Category

| Category | Strict | COR | INC | PAR | MIS | SPU |
|----------|--------|-----|-----|-----|-----|-----|
| edge_case | 22% | 5 | 0 | 3 | 4 | 5 |
| adversarial | 0% | 1 | 0 | 3 | 1 | 9 |
| ocr_corruption | 0% | 2 | 0 | 4 | 3 | 2 |
| unicode_evasion | 67% | 5 | 0 | 1 | 0 | 1 |
| real_world | 0% | 12 | 4 | 13 | 6 | 17 |

---

## 3. Failed Tests (Strict)

| Test | Cat | COR | INC | PAR | MIS | SPU | Detail |
|------|-----|-----|-----|-----|-----|-----|--------|
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
| ... | ... | ... | ... | ... | ... | ... | (11 more) |

---

## 4. Analysis

### GLiNER Strengths

- Zero-shot: Requires no training for new entity types
- Multilingual: Native support for Spanish
- Flexible labels: Specified at runtime

### Observed Weaknesses

- Specific Spanish formats (DNI, NIE, IBAN with spaces)
- Spanish textual dates (XV de marzo de MMXXIV)
- Spanish legal identifiers (ECLI, cadastral references)
- Negative context (NO tener DNI)

### Recommendation

legal_ner_v2 outperforms zero-shot GLiNER (0.325 F1). Fine-tuning specifically for the Spanish legal domain adds value.

> **Note (2026-02-04):** LoRA fine-tuning of Legal-XLM-RoBERTa-base was tested: F1 0.016 adversarial (severe overfitting). Discarded. The pipeline's base model remains RoBERTa-BNE CAPITEL NER (`legal_ner_v2`).

---

## 5. Configuration

```python
# Labels used (mapping to ContextSafe types)
GLINER_LABELS = ['phone_number', 'national id', 'zip code', 'company_name', 'date_of_birth', 'certificate_license_number', 'social security number', 'account_number', 'case number', 'ssn', 'address', 'location state', 'postal code', 'email', 'vehicle_identifier', 'city', 'phone number', 'date', 'vehicle id', 'dob', 'professional id', 'license number', 'property id', 'email address', 'location city', 'organization', 'name', 'company', 'national_id', 'court case id', 'iban', 'street_address', 'last name', 'location address', 'postcode', 'license_plate', 'unique_identifier', 'first name', 'country', 'cadastral reference', 'bank account']

# Threshold
threshold = 0.3  # Balanced (production recommended)
```

---

**Date:** 2026-01-24
