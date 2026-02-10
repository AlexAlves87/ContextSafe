# Valutazione Adversarial v2 (Standard Accademici) - legal_ner_v2

**Data:** 04-02-2026
**Modello:** legal_ner_v2
**Test:** 35
**Tempo totale:** 1.3s
**Standard:** SemEval 2013 Task 9

---

## 1. Riepilogo Esecutivo

### 1.1 Metriche SemEval 2013 (Modalità Strict)

| Metrica | Valore |
|---------|--------|
| **F1 (strict)** | **0.492** |
| Precisione (strict) | 0.525 |
| Richiamo (strict) | 0.463 |
| F1 (parziale) | 0.659 |

### 1.2 Conteggi SemEval

| Metrica | Valore | Descrizione |
|---------|--------|-------------|
| COR | 31 | Corretti (confine + tipo esatti) |
| INC | 0 | Confine corretto, tipo errato |
| PAR | 21 | Corrispondenza parziale (sovrapposizione) |
| MIS | 15 | Persi (FN) |
| SPU | 7 | Spuri (FP) |
| **POS** | 67 | Totale gold (COR+INC+PAR+MIS) |
| **ACT** | 59 | Totale sistema (COR+INC+PAR+SPU) |

### 1.3 Tasso di Superamento

| Modalità | Superati | Totale | Tasso |
|----------|----------|--------|-------|
| **Strict** | 12 | 35 | **34.3%** |
| Lenient (v1) | 21 | 35 | 60.0% |

---

## 2. Metriche per Tipo di Entità

| Tipo | COR | MIS | SPU | Precisione | Richiamo | F1 |
|------|-----|-----|-----|------------|----------|----|
| ADDRESS | 1 | 2 | 2 | 0.33 | 0.33 | 0.33 |
| CADASTRAL_REF | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| DATE | 1 | 3 | 1 | 0.50 | 0.25 | 0.33 |
| DNI_NIE | 9 | 4 | 2 | 0.82 | 0.69 | 0.75 |
| ECLI | 1 | 1 | 1 | 0.50 | 0.50 | 0.50 |
| IBAN | 0 | 3 | 2 | 0.00 | 0.00 | 0.00 |
| LICENSE_PLATE | 0 | 1 | 1 | 0.00 | 0.00 | 0.00 |
| LOCATION | 10 | 1 | 0 | 1.00 | 0.91 | 0.95 |
| NSS | 0 | 1 | 0 | 0.00 | 0.00 | 0.00 |
| ORGANIZATION | 1 | 2 | 5 | 0.17 | 0.33 | 0.22 |
| PERSON | 6 | 13 | 13 | 0.32 | 0.32 | 0.32 |
| PHONE | 1 | 1 | 0 | 1.00 | 0.50 | 0.67 |
| POSTAL_CODE | 0 | 2 | 1 | 0.00 | 0.00 | 0.00 |
| PROFESSIONAL_ID | 0 | 2 | 0 | 0.00 | 0.00 | 0.00 |

---

## 3. Risultati per Categoria

| Categoria | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 62% | 75% | 4 | 0 | 1 | 0 | 2 | 0.67 |
| edge_case | 22% | 67% | 6 | 0 | 3 | 3 | 1 | 0.55 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0.57 |
| real_world | 10% | 50% | 12 | 0 | 16 | 7 | 4 | 0.36 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0.91 |

## 4. Risultati per Difficoltà

| Difficoltà | Strict | Lenient | Totale |
|------------|--------|---------|--------|
| facile | 25% | 100% | 4 |
| medio | 50% | 75% | 12 |
| difficile | 26% | 42% | 19 |

---

## 5. Test Falliti (Modalità Strict)

| Test | Cat | COR | INC | PAR | MIS | SPU | Dettaglio |
|------|-----|-----|-----|-----|-----|-----|-----------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 corrispondenza parziale |
| dni_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['12 345 678 Z'] |
| iban_with_spaces | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 corrispondenza parziale |
| phone_international | edge | 1 | 0 | 0 | 1 | 0 | MIS: ['0034612345678'] |
| date_roman_numerals | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['XV de marzo del año MMXXIV'] |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| address_floor_door | edge | 2 | 0 | 1 | 0 | 0 | PAR: 1 corrispondenza parziale |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Don Quijote de la Mancha'] |
| mixed_languages | adve | 2 | 0 | 1 | 0 | 0 | PAR: 1 corrispondenza parziale |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 corrispond... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| fullwidth_numbers | unic | 1 | 0 | 0 | 1 | 0 | MIS: ['María'] |
| notarial_header | real | 3 | 0 | 0 | 1 | 0 | MIS: ['quince de marzo de dos mil veinti... |
| testament_comparecencia | real | 3 | 0 | 2 | 0 | 0 | PAR: 2 corrispondenze parziali |
| judicial_sentence_header | real | 1 | 0 | 2 | 1 | 1 | MIS: ['diez de enero de dos mil veinticu... |
| contract_parties | real | 2 | 0 | 4 | 2 | 0 | MIS: ['28013', 'Madrid']; PAR: 4 corris... |
| bank_account_clause | real | 0 | 0 | 2 | 1 | 0 | MIS: ['A-98765432']; PAR: 2 corris... |
| professional_ids | real | 0 | 0 | 2 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Abvocat'... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 parzia... |
| vehicle_clause | real | 0 | 0 | 2 | 0 | 0 | PAR: 2 corrispondenze parziali |
| social_security | real | 0 | 0 | 1 | 0 | 0 | PAR: 1 corrispondenza parziale |

---

## 6. Confronto v1 vs v2

| Metrica | v1 (lenient) | v2 (strict) | Differenza |
|---------|--------------|-------------|------------|
| Pass rate | 60.0% | 34.3% | +25.7pp |
| F1 | 0.659 | 0.492 | +0.167 |

**Nota:** v1 usava il matching lenient (contenimento + 80% sovrapposizione). v2 usa strict (confine esatto + tipo esatto).

---

## 7. Riferimenti

- **SemEval 2013 Task 9**: Valutazione a livello di entità con 4 modalità (strict, exact, partial, type)
- **RockNER (EMNLP 2021)**: Metodologia di valutazione NER adversarial
- **NoiseBench (EMNLP 2024)**: Benchmark rumore reale vs rumore simulato
- **nervaluate**: Libreria Python per valutazione NER in stile SemEval

**Generato da:** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Data:** 04-02-2026
