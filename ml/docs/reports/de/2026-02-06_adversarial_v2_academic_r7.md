# Adversariale Evaluierung v2 (Academic Standards) - legal_ner_v2

**Datum:** 06.02.2026
**Modell:** legal_ner_v2
**Tests:** 35
**Gesamtzeit:** 1,4s
**Standard:** SemEval 2013 Task 9

---

## 1. Management-Zusammenfassung

### 1.1 SemEval 2013 Metriken (Strikter Modus)

| Metrik | Wert |
|--------|------|
| **F1 (strikt)** | **0,776** |
| Precision (strikt) | 0,776 |
| Recall (strikt) | 0,776 |
| F1 (partiell) | 0,813 |

### 1.2 SemEval Zählungen

| Metrik | Wert | Beschreibung |
|--------|------|--------------|
| COR | 52 | Korrekt (exakte Grenze + Typ) |
| INC | 1 | Grenze korrekt, Typ inkorrekt |
| PAR | 5 | Partielle Übereinstimmung (Überlappung) |
| MIS | 9 | Verpasst (FN) |
| SPU | 9 | Espurios (FP) |
| **POS** | 67 | Total Gold (COR+INC+PAR+MIS) |
| **ACT** | 67 | Total System (COR+INC+PAR+SPU) |

### 1.3 Pass Rate

| Modus | Bestanden | Gesamt | Rate |
|-------|-----------|--------|------|
| **Strikt** | 19 | 35 | **54,3%** |
| Lenient (v1) | 25 | 35 | 71,4% |

---

## 2. Metriken nach Entitätstyp

| Typ | COR | MIS | SPU | Precision | Recall | F1 |
|-----|-----|-----|-----|-----------|--------|----|
| ADDRESS | 2 | 1 | 1 | 0,67 | 0,67 | 0,67 |
| CADASTRAL_REF | 1 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| CIF | 0 | 0 | 2 | 0,00 | 0,00 | 0,00 |
| DATE | 4 | 0 | 1 | 0,80 | 1,00 | 0,89 |
| DNI_NIE | 10 | 3 | 2 | 0,83 | 0,77 | 0,80 |
| ECLI | 1 | 1 | 1 | 0,50 | 0,50 | 0,50 |
| IBAN | 2 | 1 | 0 | 1,00 | 0,67 | 0,80 |
| LICENSE_PLATE | 0 | 1 | 1 | 0,00 | 0,00 | 0,00 |
| LOCATION | 10 | 1 | 0 | 1,00 | 0,91 | 0,95 |
| NSS | 1 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| ORGANIZATION | 3 | 0 | 3 | 0,50 | 1,00 | 0,67 |
| PERSON | 16 | 3 | 3 | 0,84 | 0,84 | 0,84 |
| PHONE | 1 | 1 | 1 | 0,50 | 0,50 | 0,50 |
| POSTAL_CODE | 1 | 1 | 0 | 1,00 | 0,50 | 0,67 |
| PROFESSIONAL_ID | 0 | 2 | 0 | 0,00 | 0,00 | 0,00 |

---

## 3. Ergebnisse nach Kategorie

| Kategorie | Strikt | Lenient | COR | INC | PAR | MIS | SPU | F1 strikt |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 75% | 75% | 5 | 0 | 0 | 0 | 2 | 0,83 |
| edge_case | 78% | 100% | 11 | 0 | 1 | 0 | 1 | 0,88 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0,57 |
| real_world | 20% | 60% | 27 | 1 | 3 | 4 | 6 | 0,75 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0,91 |

## 4. Ergebnisse nach Schwierigkeit

| Schwierigkeit | Strikt | Lenient | Gesamt |
|---------------|--------|---------|--------|
| einfach | 50% | 100% | 4 |
| mittel | 67% | 92% | 12 |
| schwer | 47% | 53% | 19 |

---

## 5. Fehlgeschlagene Tests (Strikter Modus)

| Test | Kat | COR | INC | PAR | MIS | SPU | Detail |
|------|-----|-----|-----|-----|-----|-----|--------|
| phone_international | edge | 1 | 0 | 1 | 0 | 0 | PAR: 1 partielle Match |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 partielle Match... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| fullwidth_numbers | unic | 1 | 0 | 0 | 1 | 0 | MIS: ['María'] |
| testament_comparecencia | real | 4 | 0 | 1 | 0 | 0 | PAR: 1 partielle Match |
| judicial_sentence_header | real | 4 | 0 | 0 | 0 | 1 | SPU: ['Sala Primera del Tribunal Supremo... |
| contract_parties | real | 6 | 0 | 0 | 2 | 1 | MIS: ['28013', 'Madrid']; SPU: ['B-12345... |
| bank_account_clause | real | 2 | 1 | 0 | 0 | 0 | INC: 1 Typ nicht übereinstimmend |
| professional_ids | real | 2 | 0 | 0 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Abogado'... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 partia... |
| vehicle_clause | real | 1 | 0 | 1 | 0 | 0 | PAR: 1 partielle Match |
| social_security | real | 1 | 0 | 0 | 0 | 1 | SPU: ['28'] |

---

## 6. Vergleich v1 vs v2

| Metrik | v1 (lenient) | v2 (strikt) | Differenz |
|--------|--------------|-------------|-----------|
| Pass rate | 71,4% | 54,3% | +17,1pp |
| F1 | 0,813 | 0,776 | +0,037 |

**Hinweis:** v1 verwendete Lenient Matching (Containment + 80% Überlappung). v2 verwendet Strikt (exakte Grenze + exakter Typ).

---

## 7. Referenzen

- **SemEval 2013 Task 9**: Entity-Level Evaluierung mit 4 Modi (strict, exact, partial, type)
- **RockNER (EMNLP 2021)**: Adversariale NER-Evaluierungsmethodik
- **NoiseBench (EMNLP 2024)**: Echtes Rauschen vs. Simulation Rauschen Benchmark
- **nervaluate**: Python-Bibliothek für NER-Evaluierung im SemEval-Stil

**Generiert von:** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Datum:** 06.02.2026
