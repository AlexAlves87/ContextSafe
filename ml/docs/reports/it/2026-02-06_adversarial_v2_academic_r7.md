# Valutazione Adversarial v2 (Standard Accademici) - legal_ner_v2

**Data:** 06-02-2026
**Modello:** legal_ner_v2
**Test:** 35
**Tempo totale:** 1.4s
**Standard:** SemEval 2013 Task 9

---

## 1. Riepilogo Esecutivo

### 1.1 Metriche SemEval 2013 (Modalità Strict)

| Metrica | Valore |
|---------|--------|
| **F1 (strict)** | **0.776** |
| Precisione (strict) | 0.776 |
| Richiamo (strict) | 0.776 |
| F1 (parziale) | 0.813 |

### 1.2 Conteggi SemEval

| Metrica | Valore | Descrizione |
|---------|--------|-------------|
| COR | 52 | Corretti (confine + tipo esatti) |
| INC | 1 | Confine corretto, tipo errato |
| PAR | 5 | Corrispondenza parziale (sovrapposizione) |
| MIS | 9 | Persi (FN) |
| SPU | 9 | Spuri (FP) |
| **POS** | 67 | Totale gold (COR+INC+PAR+MIS) |
| **ACT** | 67 | Totale sistema (COR+INC+PAR+SPU) |

### 1.3 Tasso di Superamento

| Modalità | Superati | Totale | Tasso |
|----------|----------|--------|-------|
| **Strict** | 19 | 35 | **54.3%** |
| Lenient (v1) | 25 | 35 | 71.4% |

---

## 2. Metriche per Tipo di Entità

| Tipo | COR | MIS | SPU | Precisione | Richiamo | F1 |
|------|-----|-----|-----|------------|----------|----|
| ADDRESS | 2 | 1 | 1 | 0.67 | 0.67 | 0.67 |
| CADASTRAL_REF | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| CIF | 0 | 0 | 2 | 0.00 | 0.00 | 0.00 |
| DATE | 4 | 0 | 1 | 0.80 | 1.00 | 0.89 |
| DNI_NIE | 10 | 3 | 2 | 0.83 | 0.77 | 0.80 |
| ECLI | 1 | 1 | 1 | 0.50 | 0.50 | 0.50 |
| IBAN | 2 | 1 | 0 | 1.00 | 0.67 | 0.80 |
| LICENSE_PLATE | 0 | 1 | 1 | 0.00 | 0.00 | 0.00 |
| LOCATION | 10 | 1 | 0 | 1.00 | 0.91 | 0.95 |
| NSS | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| ORGANIZATION | 3 | 0 | 3 | 0.50 | 1.00 | 0.67 |
| PERSON | 16 | 3 | 3 | 0.84 | 0.84 | 0.84 |
| PHONE | 1 | 1 | 1 | 0.50 | 0.50 | 0.50 |
| POSTAL_CODE | 1 | 1 | 0 | 1.00 | 0.50 | 0.67 |
| PROFESSIONAL_ID | 0 | 2 | 0 | 0.00 | 0.00 | 0.00 |

---

## 3. Risultati per Categoria

| Categoria | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 75% | 75% | 5 | 0 | 0 | 0 | 2 | 0.83 |
| edge_case | 78% | 100% | 11 | 0 | 1 | 0 | 1 | 0.88 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0.57 |
| real_world | 20% | 60% | 27 | 1 | 3 | 4 | 6 | 0.75 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0.91 |

## 4. Risultati per Difficoltà

| Difficoltà | Strict | Lenient | Totale |
|------------|--------|---------|--------|
| facile | 50% | 100% | 4 |
| medio | 67% | 92% | 12 |
| difficile | 47% | 53% | 19 |

---

## 5. Test Falliti (Modalità Strict)

| Test | Cat | COR | INC | PAR | MIS | SPU | Dettaglio |
|------|-----|-----|-----|-----|-----|-----|-----------|
| phone_international | edge | 1 | 0 | 1 | 0 | 0 | PAR: 1 corrispondenza parziale |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 corrispond... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| fullwidth_numbers | unic | 1 | 0 | 0 | 1 | 0 | MIS: ['María'] |
| testament_comparecencia | real | 4 | 0 | 1 | 0 | 0 | PAR: 1 corrispondenza parziale |
| judicial_sentence_header | real | 4 | 0 | 0 | 0 | 1 | SPU: ['Sala Primera del Tribunal Supremo... |
| contract_parties | real | 6 | 0 | 0 | 2 | 1 | MIS: ['28013', 'Madrid']; SPU: ['B-12345... |
| bank_account_clause | real | 2 | 1 | 0 | 0 | 0 | INC: 1 tipo errato |
| professional_ids | real | 2 | 0 | 0 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Abvocat'... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 parzia... |
| vehicle_clause | real | 1 | 0 | 1 | 0 | 0 | PAR: 1 corrispondenza parziale |
| social_security | real | 1 | 0 | 0 | 0 | 1 | SPU: ['28'] |

---

## 6. Confronto v1 vs v2

| Metrica | v1 (lenient) | v2 (strict) | Differenza |
|---------|--------------|-------------|------------|
| Pass rate | 71.4% | 54.3% | +17.1pp |
| F1 | 0.813 | 0.776 | +0.037 |

**Nota:** v1 usava il matching lenient (contenimento + 80% sovrapposizione). v2 usa strict (confine esatto + tipo esatto).

---

## 7. Riferimenti

- **SemEval 2013 Task 9**: Valutazione a livello di entità con 4 modalità (strict, exact, partial, type)
- **RockNER (EMNLP 2021)**: Metodologia di valutazione NER adversarial
- **NoiseBench (EMNLP 2024)**: Benchmark rumore reale vs rumore simulato
- **nervaluate**: Libreria Python per valutazione NER in stile SemEval

**Generato da:** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Data:** 06-02-2026
