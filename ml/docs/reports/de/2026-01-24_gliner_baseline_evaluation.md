# GLiNER-PII Baseline Evaluation

**Datum:** 2026-01-24
**Modell:** knowledgator/gliner-pii-base-v1.0
**Threshold:** 0.3 (ausgewogen)
**Tests:** 35
**Zeit:** 3.8s

---

## 1. Zusammenfassung

### Vergleich mit legal_ner_v2

| Modell | Strict F1 | Präzision | Recall | Pass Rate |
|--------|-----------|-----------|--------|-----------|
| **GLiNER-PII-base** | **0.325** | 0.287 | 0.373 | 11.4% |
| legal_ner_v2 | 0.788 | - | - | 60.0% |
| **Differenz** | **-0.463** | - | - | -48.6pp |

### SemEval-Zählungen

| Metrik | Wert | Beschreibung |
|--------|-------|-------------|
| COR | 25 | Korrekt (Grenze + Typ) |
| INC | 4 | Grenze OK, Typ inkorrekt |
| PAR | 24 | Teilweise Übereinstimmung |
| MIS | 14 | Verpasst (FN) |
| SPU | 34 | Scheinbar (FP) |

---

## 2. Ergebnisse nach Kategorie

| Kategorie | Strict | COR | INC | PAR | MIS | SPU |
|----------|--------|-----|-----|-----|-----|-----|
| edge_case | 22% | 5 | 0 | 3 | 4 | 5 |
| adversarial | 0% | 1 | 0 | 3 | 1 | 9 |
| ocr_corruption | 0% | 2 | 0 | 4 | 3 | 2 |
| unicode_evasion | 67% | 5 | 0 | 1 | 0 | 1 |
| real_world | 0% | 12 | 4 | 13 | 6 | 17 |

---

## 3. Fehlgeschlagene Tests (Strict)

| Test | Kat | COR | INC | PAR | MIS | SPU | Detail |
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
| ... | ... | ... | ... | ... | ... | ... | (11 mehr) |

---

## 4. Analyse

### Stärken von GLiNER

- Zero-Shot: Erfordert kein Training für neue Entitätstypen
- Mehrsprachig: Native Unterstützung für Spanisch
- Flexible Labels: Zur Laufzeit spezifiziert

### Beobachtete Schwächen

- Spezifische spanische Formate (DNI, NIE, IBAN mit Leerzeichen)
- Spanische textuelle Daten (XV de marzo de MMXXIV)
- Spanische rechtliche Identifikatoren (ECLI, Katasterreferenzen)
- Negativer Kontext (NO tener DNI)

### Empfehlung

legal_ner_v2 übertrifft Zero-Shot GLiNER (0.325 F1). Spezifisches Fine-Tuning für die spanische Rechtsdomäne bringt Mehrwert.

> **Nachfolgende Anmerkung (2026-02-04):** LoRA Fine-Tuning von Legal-XLM-RoBERTa-base wurde getestet: F1 0.016 adversarial (schweres Overfitting). Verworfen. Das Basismodell der Pipeline bleibt RoBERTa-BNE CAPITEL NER (`legal_ner_v2`).

---

## 5. Konfiguration

```python
# Verwendete Labels (Mapping zu ContextSafe-Typen)
GLINER_LABELS = ['phone_number', 'national id', 'zip code', 'company_name', 'date_of_birth', 'certificate_license_number', 'social security number', 'account_number', 'case number', 'ssn', 'address', 'location state', 'postal code', 'email', 'vehicle_identifier', 'city', 'phone number', 'date', 'vehicle id', 'dob', 'professional id', 'license number', 'property id', 'email address', 'location city', 'organization', 'name', 'company', 'national_id', 'court case id', 'iban', 'street_address', 'last name', 'location address', 'postcode', 'license_plate', 'unique_identifier', 'first name', 'country', 'cadastral reference', 'bank account']

# Threshold
threshold = 0.3  # Ausgewogen (für Produktion empfohlen)
```

---

**Generiert von:** `scripts/evaluate/evaluate_gliner_baseline.py`
**Datum:** 2026-01-24
