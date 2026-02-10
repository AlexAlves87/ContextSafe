# Valutazione Avversaria - legal_ner_v2

**Data:** 2026-01-23
**Modello:** legal_ner_v2
**Test:** 35
**Tempo Totale:** 1.4s

---

## Riepilogo Esecutivo

### Metriche Entity-Level (stile seqeval)

| Metrica | Valore |
|---------|-------|
| Precisione | 0.845 |
| Richiamo | 0.731 |
| **F1-Score** | **0.784** |
| Veri Positivi | 49 |
| Falsi Positivi | 9 |
| Falsi Negativi | 18 |
| Punteggio Sovrapposizione Medio | 0.935 |

### Resistenza al Rumore (stile NoiseBench)

| Metrica | Valore | Riferimento |
|---------|-------|------------|
| F1 (testo pulito) | 0.800 | - |
| F1 (con rumore) | 0.720 | - |
| Degradazione | 0.080 | ≤0.10 atteso |
| Stato | ✅ OK | Rif. HAL Science |

### Test per Risultato

| Metrica | Valore |
|---------|-------|
| Test Totali | 35 |
| Superati | 19 (54.3%) |
| Falliti | 16 (45.7%) |

### Per Categoria (con F1)

| Categoria | Tasso Superamento | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### Per Difficoltà

| Difficoltà | Superati | Totale | Tasso |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

---

## Analisi Errori

### Test Falliti

| ID Test | Categoria | Mancati | FP | Dettaglio |
|---------|-----------|--------|----|---------|
| dni_with_spaces | edge_case | 1 | 0 | Mancato: ['12 345 678 Z'] |
| phone_international | edge_case | 1 | 0 | Mancato: ['0034612345678'] |
| date_roman_numerals | edge_case | 1 | 0 | Mancato: ['XV de marzo del año MMXXIV'] |
| example_dni | adversarial | 0 | 1 | FP: ['12345678X'] |
| fictional_person | adversarial | 0 | 1 | FP: ['Don Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_corruption | 1 | 0 | Mancato: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_corruption | 1 | 0 | Mancato: ['12345678X'] |
| ocr_extra_spaces | ocr_corruption | 2 | 0 | Mancato: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| zero_width_space | unicode_evasion | 0 | 1 | FP: ['de'] |
| fullwidth_numbers | unicode_evasion | 2 | 0 | Mancato: ['１２３４５６７８Z', 'María'] |
| notarial_header | real_world | 1 | 0 | Mancato: ['quince de marzo de dos mil veinticuatro'... |
| judicial_sentence_header | real_world | 1 | 2 | Mancato: ['diez de enero de dos mil veinticuatro'];... |
| contract_parties | real_world | 2 | 0 | Mancato: ['28013', 'Madrid'] |
| bank_account_clause | real_world | 1 | 0 | Mancato: ['A-98765432'] |
| professional_ids | real_world | 3 | 1 | Mancato: ['12345', 'MIGUEL TORRES', '67890']; FP: [... |
| social_security | real_world | 1 | 1 | Mancato: ['281234567890']; FP: ['28'] |

---

## Risultati Dettagliati

### ADVERSARIAL

#### date_in_reference [✅ PASS]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 0 | **Rilevato:** 0
**Corretti:** 0 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### example_dni [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 0 | **Rilevato:** 1
**Corretti:** 0 | **Mancati:** 0 | **FP:** 1
**Dettagli:** FP: ['12345678X']

#### fictional_person [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 0 | **Rilevato:** 1
**Corretti:** 0 | **Mancati:** 0 | **FP:** 1
**Dettagli:** FP: ['Don Quijote de la Mancha']

#### location_as_person [✅ PASS]

**Difficoltà:** hard | **Sovrapposizione:** 1.00
**Atteso:** 1 | **Rilevato:** 1
**Corretti:** 1 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### mixed_languages [✅ PASS]

**Difficoltà:** hard | **Sovrapposizione:** 0.94
**Atteso:** 3 | **Rilevato:** 3
**Corretti:** 3 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### negation_dni [✅ PASS]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 0 | **Rilevato:** 0
**Corretti:** 0 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### numbers_not_dni [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 0.00
**Atteso:** 0 | **Rilevato:** 0
**Corretti:** 0 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### organization_as_person [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 1.00
**Atteso:** 1 | **Rilevato:** 1
**Corretti:** 1 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

### EDGE_CASE

#### address_floor_door [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 0.83
**Atteso:** 3 | **Rilevato:** 3
**Corretti:** 3 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### date_ordinal [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 1.00
**Atteso:** 1 | **Rilevato:** 2
**Corretti:** 1 | **Mancati:** 0 | **FP:** 1
**Dettagli:** FP: ['El']

#### date_roman_numerals [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 1 | **Rilevato:** 0
**Corretti:** 0 | **Mancati:** 1 | **FP:** 0
**Dettagli:** Mancato: ['XV de marzo del año MMXXIV']

#### dni_with_spaces [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 1 | **Rilevato:** 0
**Corretti:** 0 | **Mancati:** 1 | **FP:** 0
**Dettagli:** Mancato: ['12 345 678 Z']

#### dni_without_letter [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 1.00
**Atteso:** 1 | **Rilevato:** 1
**Corretti:** 1 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### iban_with_spaces [✅ PASS]

**Difficoltà:** easy | **Sovrapposizione:** 0.91
**Atteso:** 1 | **Rilevato:** 1
**Corretti:** 1 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### phone_international [❌ FAIL]

**Difficoltà:** medium | **Sovrapposizione:** 1.00
**Atteso:** 2 | **Rilevato:** 1
**Corretti:** 1 | **Mancati:** 1 | **FP:** 0
**Dettagli:** Mancato: ['0034612345678']

#### single_letter_name [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 1.00
**Atteso:** 1 | **Rilevato:** 1
**Corretti:** 1 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### very_long_name [✅ PASS]

**Difficoltà:** hard | **Sovrapposizione:** 1.00
**Atteso:** 1 | **Rilevato:** 1
**Corretti:** 1 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

### OCR_CORRUPTION

#### ocr_accent_loss [✅ PASS]

**Difficoltà:** easy | **Sovrapposizione:** 1.00
**Atteso:** 2 | **Rilevato:** 2
**Corretti:** 2 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### ocr_extra_spaces [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 2 | **Rilevato:** 0
**Corretti:** 0 | **Mancati:** 2 | **FP:** 0
**Dettagli:** Mancato: ['1 2 3 4 5 6 7 8 Z', 'M a r í a']

#### ocr_letter_substitution [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 1.00
**Atteso:** 2 | **Rilevato:** 2
**Corretti:** 2 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### ocr_missing_spaces [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.88
**Atteso:** 2 | **Rilevato:** 1
**Corretti:** 1 | **Mancati:** 1 | **FP:** 0
**Dettagli:** Mancato: ['12345678X']

#### ocr_zero_o_confusion [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 1 | **Rilevato:** 0
**Corretti:** 0 | **Mancati:** 1 | **FP:** 0
**Dettagli:** Mancato: ['ES91 21O0 0418 45O2 OOO5 1332']

### REAL_WORLD

#### bank_account_clause [❌ FAIL]

**Difficoltà:** medium | **Sovrapposizione:** 0.88
**Atteso:** 3 | **Rilevato:** 2
**Corretti:** 2 | **Mancati:** 1 | **FP:** 0
**Dettagli:** Mancato: ['A-98765432']

#### cadastral_reference [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 1.00
**Atteso:** 2 | **Rilevato:** 2
**Corretti:** 2 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### contract_parties [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.88
**Atteso:** 8 | **Rilevato:** 6
**Corretti:** 6 | **Mancati:** 2 | **FP:** 0
**Dettagli:** Mancato: ['28013', 'Madrid']

#### ecli_citation [✅ PASS]

**Difficoltà:** easy | **Sovrapposizione:** 0.90
**Atteso:** 2 | **Rilevato:** 3
**Corretti:** 2 | **Mancati:** 0 | **FP:** 1
**Dettagli:** FP: ['Tribunal Supremo']

#### judicial_sentence_header [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.92
**Atteso:** 4 | **Rilevato:** 5
**Corretti:** 3 | **Mancati:** 1 | **FP:** 2
**Dettagli:** Mancato: ['diez de enero de dos mil veinticuatro']; FP: ['Nº 123/2024', 'Sala Primera del Tribunal Supremo']

#### notarial_header [❌ FAIL]

**Difficoltà:** medium | **Sovrapposizione:** 1.00
**Atteso:** 4 | **Rilevato:** 3
**Corretti:** 3 | **Mancati:** 1 | **FP:** 0
**Dettagli:** Mancato: ['quince de marzo de dos mil veinticuatro']

#### professional_ids [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.65
**Atteso:** 4 | **Rilevato:** 2
**Corretti:** 1 | **Mancati:** 3 | **FP:** 1
**Dettagli:** Mancato: ['12345', 'MIGUEL TORRES', '67890']; FP: ['Colegio de Procuradores de Madrid']

#### social_security [❌ FAIL]

**Difficoltà:** easy | **Sovrapposizione:** 0.00
**Atteso:** 1 | **Rilevato:** 1
**Corretti:** 0 | **Mancati:** 1 | **FP:** 1
**Dettagli:** Mancato: ['281234567890']; FP: ['28']

#### testament_comparecencia [✅ PASS]

**Difficoltà:** hard | **Sovrapposizione:** 0.99
**Atteso:** 5 | **Rilevato:** 5
**Corretti:** 5 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### vehicle_clause [✅ PASS]

**Difficoltà:** medium | **Sovrapposizione:** 0.72
**Atteso:** 2 | **Rilevato:** 2
**Corretti:** 2 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

### UNICODE_EVASION

#### cyrillic_o [✅ PASS]

**Difficoltà:** hard | **Sovrapposizione:** 0.94
**Atteso:** 2 | **Rilevato:** 2
**Corretti:** 2 | **Mancati:** 0 | **FP:** 0
**Dettagli:** OK

#### fullwidth_numbers [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 0.00
**Atteso:** 2 | **Rilevato:** 0
**Corretti:** 0 | **Mancati:** 2 | **FP:** 0
**Dettagli:** Mancato: ['１２３４５６７８Z', 'María']

#### zero_width_space [❌ FAIL]

**Difficoltà:** hard | **Sovrapposizione:** 1.00
**Atteso:** 2 | **Rilevato:** 3
**Corretti:** 2 | **Mancati:** 0 | **FP:** 1
**Dettagli:** FP: ['de']

---

## Riferimenti

- **seqeval**: Metriche di valutazione a livello di entità per NER
- **NoiseBench (ICLR 2024)**: Valutazione rumore reale vs simulato
- **HAL Science**: Valutazione impatto OCR (~10pt degradazione F1 attesa)

**Generato da:** `scripts/evaluate/test_ner_predictor_adversarial.py`
**Data:** 2026-01-23
