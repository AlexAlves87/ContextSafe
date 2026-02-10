# Adversarielle Evaluierung - legal_ner_v2

**Datum:** 2026-01-23
**Modell:** legal_ner_v2
**Tests:** 35
**Gesamtzeit:** 1.4s

---

## Zusammenfassung

### Entity-Level Metriken (seqeval-Stil)

| Metrik | Wert |
|---------|-------|
| Präzision | 0.845 |
| Recall | 0.731 |
| **F1-Score** | **0.784** |
| True Positives | 49 |
| False Positives | 9 |
| False Negatives | 18 |
| Mean Overlap Score | 0.935 |

### Rauschresistenz (NoiseBench-Stil)

| Metrik | Wert | Referenz |
|---------|-------|------------|
| F1 (sauberer Text) | 0.800 | - |
| F1 (mit Rauschen) | 0.720 | - |
| Degradation | 0.080 | ≤0.10 erwartet |
| Status | ✅ OK | HAL Science Ref |

### Tests nach Ergebnis

| Metrik | Wert |
|---------|-------|
| Gesamttests | 35 |
| Bestanden | 19 (54.3%) |
| Fehlgeschlagen | 16 (45.7%) |

### Nach Kategorie (mit F1)

| Kategorie | Pass Rate | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### Nach Schwierigkeit

| Schwierigkeit | Bestanden | Gesamt | Rate |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

---

## Fehleranalyse

### Fehlgeschlagene Tests

| Test ID | Kategorie | Missed | FP | Detail |
|---------|-----------|--------|----|---------|
| dni_with_spaces | edge_case | 1 | 0 | Verpasst: ['12 345 678 Z'] |
| phone_international | edge_case | 1 | 0 | Verpasst: ['0034612345678'] |
| date_roman_numerals | edge_case | 1 | 0 | Verpasst: ['XV de marzo del año MMXXIV'] |
| example_dni | adversarial | 0 | 1 | FP: ['12345678X'] |
| fictional_person | adversarial | 0 | 1 | FP: ['Don Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_corruption | 1 | 0 | Verpasst: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_corruption | 1 | 0 | Verpasst: ['12345678X'] |
| ocr_extra_spaces | ocr_corruption | 2 | 0 | Verpasst: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| zero_width_space | unicode_evasion | 0 | 1 | FP: ['de'] |
| fullwidth_numbers | unicode_evasion | 2 | 0 | Verpasst: ['１２３４５６７８Z', 'María'] |
| notarial_header | real_world | 1 | 0 | Verpasst: ['quince de marzo de dos mil veinticuatro'... |
| judicial_sentence_header | real_world | 1 | 2 | Verpasst: ['diez de enero de dos mil veinticuatro'];... |
| contract_parties | real_world | 2 | 0 | Verpasst: ['28013', 'Madrid'] |
| bank_account_clause | real_world | 1 | 0 | Verpasst: ['A-98765432'] |
| professional_ids | real_world | 3 | 1 | Verpasst: ['12345', 'MIGUEL TORRES', '67890']; FP: [... |
| social_security | real_world | 1 | 1 | Verpasst: ['281234567890']; FP: ['28'] |

---

## Detaillierte Ergebnisse

### ADVERSARIAL

#### date_in_reference [✅ PASS]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 0 | **Erkannt:** 0
**Korrekt:** 0 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### example_dni [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 0 | **Erkannt:** 1
**Korrekt:** 0 | **Verpasst:** 0 | **FP:** 1
**Details:** FP: ['12345678X']

#### fictional_person [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 0 | **Erkannt:** 1
**Korrekt:** 0 | **Verpasst:** 0 | **FP:** 1
**Details:** FP: ['Don Quijote de la Mancha']

#### location_as_person [✅ PASS]

**Schwierigkeit:** hard | **Overlap:** 1.00
**Erwartet:** 1 | **Erkannt:** 1
**Korrekt:** 1 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### mixed_languages [✅ PASS]

**Schwierigkeit:** hard | **Overlap:** 0.94
**Erwartet:** 3 | **Erkannt:** 3
**Korrekt:** 3 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### negation_dni [✅ PASS]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 0 | **Erkannt:** 0
**Korrekt:** 0 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### numbers_not_dni [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 0.00
**Erwartet:** 0 | **Erkannt:** 0
**Korrekt:** 0 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### organization_as_person [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 1.00
**Erwartet:** 1 | **Erkannt:** 1
**Korrekt:** 1 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

### EDGE_CASE

#### address_floor_door [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 0.83
**Erwartet:** 3 | **Erkannt:** 3
**Korrekt:** 3 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### date_ordinal [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 1.00
**Erwartet:** 1 | **Erkannt:** 2
**Korrekt:** 1 | **Verpasst:** 0 | **FP:** 1
**Details:** FP: ['El']

#### date_roman_numerals [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 1 | **Erkannt:** 0
**Korrekt:** 0 | **Verpasst:** 1 | **FP:** 0
**Details:** Verpasst: ['XV de marzo del año MMXXIV']

#### dni_with_spaces [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 1 | **Erkannt:** 0
**Korrekt:** 0 | **Verpasst:** 1 | **FP:** 0
**Details:** Verpasst: ['12 345 678 Z']

#### dni_without_letter [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 1.00
**Erwartet:** 1 | **Erkannt:** 1
**Korrekt:** 1 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### iban_with_spaces [✅ PASS]

**Schwierigkeit:** easy | **Overlap:** 0.91
**Erwartet:** 1 | **Erkannt:** 1
**Korrekt:** 1 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### phone_international [❌ FAIL]

**Schwierigkeit:** medium | **Overlap:** 1.00
**Erwartet:** 2 | **Erkannt:** 1
**Korrekt:** 1 | **Verpasst:** 1 | **FP:** 0
**Details:** Verpasst: ['0034612345678']

#### single_letter_name [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 1.00
**Erwartet:** 1 | **Erkannt:** 1
**Korrekt:** 1 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### very_long_name [✅ PASS]

**Schwierigkeit:** hard | **Overlap:** 1.00
**Erwartet:** 1 | **Erkannt:** 1
**Korrekt:** 1 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

### OCR_CORRUPTION

#### ocr_accent_loss [✅ PASS]

**Schwierigkeit:** easy | **Overlap:** 1.00
**Erwartet:** 2 | **Erkannt:** 2
**Korrekt:** 2 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### ocr_extra_spaces [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 2 | **Erkannt:** 0
**Korrekt:** 0 | **Verpasst:** 2 | **FP:** 0
**Details:** Verpasst: ['1 2 3 4 5 6 7 8 Z', 'M a r í a']

#### ocr_letter_substitution [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 1.00
**Erwartet:** 2 | **Erkannt:** 2
**Korrekt:** 2 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### ocr_missing_spaces [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.88
**Erwartet:** 2 | **Erkannt:** 1
**Korrekt:** 1 | **Verpasst:** 1 | **FP:** 0
**Details:** Verpasst: ['12345678X']

#### ocr_zero_o_confusion [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 1 | **Erkannt:** 0
**Korrekt:** 0 | **Verpasst:** 1 | **FP:** 0
**Details:** Verpasst: ['ES91 21O0 0418 45O2 OOO5 1332']

### REAL_WORLD

#### bank_account_clause [❌ FAIL]

**Schwierigkeit:** medium | **Overlap:** 0.88
**Erwartet:** 3 | **Erkannt:** 2
**Korrekt:** 2 | **Verpasst:** 1 | **FP:** 0
**Details:** Verpasst: ['A-98765432']

#### cadastral_reference [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 1.00
**Erwartet:** 2 | **Erkannt:** 2
**Korrekt:** 2 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### contract_parties [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.88
**Erwartet:** 8 | **Erkannt:** 6
**Korrekt:** 6 | **Verpasst:** 2 | **FP:** 0
**Details:** Verpasst: ['28013', 'Madrid']

#### ecli_citation [✅ PASS]

**Schwierigkeit:** easy | **Overlap:** 0.90
**Erwartet:** 2 | **Erkannt:** 3
**Korrekt:** 2 | **Verpasst:** 0 | **FP:** 1
**Details:** FP: ['Tribunal Supremo']

#### judicial_sentence_header [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.92
**Erwartet:** 4 | **Erkannt:** 5
**Korrekt:** 3 | **Verpasst:** 1 | **FP:** 2
**Details:** Verpasst: ['diez de enero de dos mil veinticuatro']; FP: ['Nº 123/2024', 'Sala Primera del Tribunal Supremo']

#### notarial_header [❌ FAIL]

**Schwierigkeit:** medium | **Overlap:** 1.00
**Erwartet:** 4 | **Erkannt:** 3
**Korrekt:** 3 | **Verpasst:** 1 | **FP:** 0
**Details:** Verpasst: ['quince de marzo de dos mil veinticuatro']

#### professional_ids [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.65
**Erwartet:** 4 | **Erkannt:** 2
**Korrekt:** 1 | **Verpasst:** 3 | **FP:** 1
**Details:** Verpasst: ['12345', 'MIGUEL TORRES', '67890']; FP: ['Colegio de Procuradores de Madrid']

#### social_security [❌ FAIL]

**Schwierigkeit:** easy | **Overlap:** 0.00
**Erwartet:** 1 | **Erkannt:** 1
**Korrekt:** 0 | **Verpasst:** 1 | **FP:** 1
**Details:** Verpasst: ['281234567890']; FP: ['28']

#### testament_comparecencia [✅ PASS]

**Schwierigkeit:** hard | **Overlap:** 0.99
**Erwartet:** 5 | **Erkannt:** 5
**Korrekt:** 5 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### vehicle_clause [✅ PASS]

**Schwierigkeit:** medium | **Overlap:** 0.72
**Erwartet:** 2 | **Erkannt:** 2
**Korrekt:** 2 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

### UNICODE_EVASION

#### cyrillic_o [✅ PASS]

**Schwierigkeit:** hard | **Overlap:** 0.94
**Erwartet:** 2 | **Erkannt:** 2
**Korrekt:** 2 | **Verpasst:** 0 | **FP:** 0
**Details:** OK

#### fullwidth_numbers [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 0.00
**Erwartet:** 2 | **Erkannt:** 0
**Korrekt:** 0 | **Verpasst:** 2 | **FP:** 0
**Details:** Verpasst: ['１２３４５６７８Z', 'María']

#### zero_width_space [❌ FAIL]

**Schwierigkeit:** hard | **Overlap:** 1.00
**Erwartet:** 2 | **Erkannt:** 3
**Korrekt:** 2 | **Verpasst:** 0 | **FP:** 1
**Details:** FP: ['de']

---

## Referenzen

- **seqeval**: Entity-Level-Evaluierungsmetriken für NER
- **NoiseBench (ICLR 2024)**: Evaluierung von echtem vs. simuliertem Rauschen
- **HAL Science**: Bewertung der OCR-Auswirkungen (~10pt F1-Degradation erwartet)

**Generiert von:** `scripts/evaluate/test_ner_predictor_adversarial.py`
**Datum:** 2026-01-23
