# Adversariale Evaluierung v2 (Academic Standards) - legal_ner_v2

**Datum:** 03.02.2026
**Modell:** legal_ner_v2
**Tests:** 35
**Gesamtzeit:** 1,4s
**Standard:** SemEval 2013 Task 9

---

## 1. Management-Zusammenfassung

### 1.1 SemEval 2013 Metriken (Strikter Modus)

| Metrik | Wert |
|--------|------|
| **F1 (strikt)** | **0,444** |
| Precision (strikt) | 0,475 |
| Recall (strikt) | 0,418 |
| F1 (partiell) | 0,603 |

### 1.2 SemEval Zählungen

| Metrik | Wert | Beschreibung |
|--------|------|--------------|
| COR | 28 | Korrekt (exakte Grenze + Typ) |
| INC | 0 | Grenze korrekt, Typ inkorrekt |
| PAR | 20 | Partielle Übereinstimmung (Überlappung) |
| MIS | 19 | Verpasst (FN) |
| SPU | 11 | Espurios (FP) |
| **POS** | 67 | Total Gold (COR+INC+PAR+MIS) |
| **ACT** | 59 | Total System (COR+INC+PAR+SPU) |

### 1.3 Pass Rate

| Modus | Bestanden | Gesamt | Rate |
|-------|-----------|--------|------|
| **Strikt** | 11 | 35 | **31,4%** |
| Lenient (v1) | 18 | 35 | 51,4% |

---

## 2. Metriken nach Entitätstyp

| Typ | COR | MIS | SPU | Precision | Recall | F1 |
|-----|-----|-----|-----|-----------|--------|----|
| ADDRESS | 0 | 3 | 3 | 0,00 | 0,00 | 0,00 |
| CADASTRAL_REF | 1 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| DATE | 1 | 3 | 1 | 0,50 | 0,25 | 0,33 |
| DNI_NIE | 7 | 6 | 4 | 0,64 | 0,54 | 0,58 |
| ECLI | 1 | 1 | 1 | 0,50 | 0,50 | 0,50 |
| IBAN | 0 | 3 | 2 | 0,00 | 0,00 | 0,00 |
| LICENSE_PLATE | 0 | 1 | 1 | 0,00 | 0,00 | 0,00 |
| LOCATION | 10 | 1 | 0 | 1,00 | 0,91 | 0,95 |
| NSS | 0 | 1 | 0 | 0,00 | 0,00 | 0,00 |
| ORGANIZATION | 1 | 2 | 5 | 0,17 | 0,33 | 0,22 |
| PERSON | 6 | 13 | 13 | 0,32 | 0,32 | 0,32 |
| PHONE | 1 | 1 | 0 | 1,00 | 0,50 | 0,67 |
| POSTAL_CODE | 0 | 2 | 1 | 0,00 | 0,00 | 0,00 |
| PROFESSIONAL_ID | 0 | 2 | 0 | 0,00 | 0,00 | 0,00 |

---

## 3. Ergebnisse nach Kategorie

| Kategorie | Strikt | Lenient | COR | INC | PAR | MIS | SPU | F1 strikt |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 62% | 75% | 4 | 0 | 1 | 0 | 2 | 0,67 |
| edge_case | 22% | 56% | 5 | 0 | 3 | 4 | 2 | 0,45 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0,57 |
| real_world | 10% | 40% | 12 | 0 | 15 | 8 | 5 | 0,36 |
| unicode_evasion | 33% | 33% | 3 | 0 | 0 | 3 | 2 | 0,55 |

## 4. Ergebnisse nach Schwierigkeit

| Schwierigkeit | Strikt | Lenient | Gesamt |
|---------------|--------|---------|--------|
| einfach | 25% | 100% | 4 |
| mittel | 50% | 67% | 12 |
| schwer | 21% | 32% | 19 |

---

## 5. Fehlgeschlagene Tests (Strikter Modus)

| Test | Kat | COR | INC | PAR | MIS | SPU | Detail |
|------|-----|-----|-----|-----|-----|-----|--------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 partielle Match |
| dni_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['12 345 678 Z'] |
| iban_with_spaces | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 partielle Match |
| phone_international | edge | 1 | 0 | 0 | 1 | 0 | MIS: ['0034612345678'] |
| date_roman_numerals | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['XV de marzo del año MMXXIV'] |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| address_floor_door | edge | 1 | 0 | 1 | 1 | 1 | MIS: ['Calle Mayor 15, 3º B']; SPU: ['Ca... |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Don Quijote de la Mancha'] |
| mixed_languages | adve | 2 | 0 | 1 | 0 | 0 | PAR: 1 partielle Match |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 partielle Match... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| cyrillic_o | unic | 1 | 0 | 0 | 1 | 1 | MIS: ['12345678Х']; SPU: ['12345678X'] |
| fullwidth_numbers | unic | 0 | 0 | 0 | 2 | 1 | MIS: ['１２３４５６７８Z', 'María']; SPU: ['1234... |
| notarial_header | real | 3 | 0 | 0 | 1 | 0 | MIS: ['quince de marzo de dos mil veinti... |
| testament_comparecencia | real | 3 | 0 | 1 | 1 | 1 | MIS: ['Calle Alcalá número 123, piso 4º,... |
| judicial_sentence_header | real | 1 | 0 | 2 | 1 | 1 | MIS: ['diez de enero de dos mil veinticu... |
| contract_parties | real | 2 | 0 | 4 | 2 | 0 | MIS: ['28013', 'Madrid']; PAR: 4 partia... |
| bank_account_clause | real | 0 | 0 | 2 | 1 | 0 | MIS: ['A-98765432']; PAR: 2 partielle Matc... |
| professional_ids | real | 0 | 0 | 2 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Abogado'... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 partia... |
| vehicle_clause | real | 0 | 0 | 2 | 0 | 0 | PAR: 2 partielle Matches |
| social_security | real | 0 | 0 | 1 | 0 | 0 | PAR: 1 partielle Match |

---

## 6. Vergleich v1 vs v2

| Metrik | v1 (lenient) | v2 (strikt) | Differenz |
|--------|--------------|-------------|-----------|
| Pass rate | 51,4% | 31,4% | +20,0pp |
| F1 | 0,603 | 0,444 | +0,159 |

**Hinweis:** v1 verwendete Lenient Matching (Containment + 80% Überlappung). v2 verwendet Strikt (exakte Grenze + exakter Typ).

---

## 7. Referenzen

- **SemEval 2013 Task 9**: Entity-Level Evaluierung mit 4 Modi (strict, exact, partial, type)
- **RockNER (EMNLP 2021)**: Adversariale NER-Evaluierungsmethodik
- **NoiseBench (EMNLP 2024)**: Echtes Rauschen vs. Simulation Rauschen Benchmark
- **nervaluate**: Python-Bibliothek für NER-Evaluierung im SemEval-Stil

**Generiert von:** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Datum:** 03.02.2026
