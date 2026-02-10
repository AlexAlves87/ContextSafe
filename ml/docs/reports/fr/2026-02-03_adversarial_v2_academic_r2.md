# Évaluation Adversariale v2 (Standards Académiques) - legal_ner_v2

**Date :** 03/02/2026
**Modèle :** legal_ner_v2
**Tests :** 35
**Temps total :** 1,4s
**Standard :** SemEval 2013 Task 9

---

## 1. Résumé Exécutif

### 1.1 Métriques SemEval 2013 (Mode Strict)

| Métrique | Valeur |
|----------|--------|
| **F1 (strict)** | **0,444** |
| Précision (strict) | 0,475 |
| Rappel (strict) | 0,418 |
| F1 (partiel) | 0,603 |

### 1.2 Décomptes SemEval

| Métrique | Valeur | Description |
|----------|--------|-------------|
| COR | 28 | Correct (limite + type exacts) |
| INC | 0 | Limite correcte, type incorrect |
| PAR | 20 | Correspondance partielle (chevauchement) |
| MIS | 19 | Manqués (FN) |
| SPU | 11 | Fallacieux (FP) |
| **POS** | 67 | Total or (COR+INC+PAR+MIS) |
| **ACT** | 59 | Total système (COR+INC+PAR+SPU) |

### 1.3 Taux de Réussite

| Mode | Passés | Total | Taux |
|------|--------|-------|------|
| **Strict** | 11 | 35 | **31,4%** |
| Lenient (v1) | 18 | 35 | 51,4% |

---

## 2. Métriques par Type d'Entité

| Type | COR | MIS | SPU | Précision | Rappel | F1 |
|------|-----|-----|-----|-----------|--------|----|
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

## 3. Résultats par Catégorie

| Catégorie | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 62% | 75% | 4 | 0 | 1 | 0 | 2 | 0,67 |
| edge_case | 22% | 56% | 5 | 0 | 3 | 4 | 2 | 0,45 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0,57 |
| real_world | 10% | 40% | 12 | 0 | 15 | 8 | 5 | 0,36 |
| unicode_evasion | 33% | 33% | 3 | 0 | 0 | 3 | 2 | 0,55 |

## 4. Résultats par Difficulté

| Difficulté | Strict | Lenient | Total |
|------------|--------|---------|-------|
| facile | 25% | 100% | 4 |
| moyen | 50% | 67% | 12 |
| difficile | 21% | 32% | 19 |

---

## 5. Tests Échoués (Mode Strict)

| Test | Cat | COR | INC | PAR | MIS | SPU | Détail |
|------|-----|-----|-----|-----|-----|-----|--------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| dni_with_spaces | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['12 345 678 Z'] |
| iban_with_spaces | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| phone_international | edge | 1 | 0 | 0 | 1 | 0 | MIS: ['0034612345678'] |
| date_roman_numerals | edge | 0 | 0 | 0 | 1 | 0 | MIS: ['XV de marzo del año MMXXIV'] |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| address_floor_door | edge | 1 | 0 | 1 | 1 | 1 | MIS: ['Calle Mayor 15, 3º B']; SPU: ['Ca... |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Don Quijote de la Mancha'] |
| mixed_languages | adve | 2 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 corresp... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| cyrillic_o | unic | 1 | 0 | 0 | 1 | 1 | MIS: ['12345678Х']; SPU: ['12345678X'] |
| fullwidth_numbers | unic | 0 | 0 | 0 | 2 | 1 | MIS: ['１２３４５６７８Z', 'María']; SPU: ['1234... |
| notarial_header | real | 3 | 0 | 0 | 1 | 0 | MIS: ['quince de marzo de dos mil veinti... |
| testament_comparecencia | real | 3 | 0 | 1 | 1 | 1 | MIS: ['Calle Alcalá número 123, piso 4º,... |
| judicial_sentence_header | real | 1 | 0 | 2 | 1 | 1 | MIS: ['diez de enero de dos mil veinticu... |
| contract_parties | real | 2 | 0 | 4 | 2 | 0 | MIS: ['28013', 'Madrid']; PAR: 4 corresp... |
| bank_account_clause | real | 0 | 0 | 2 | 1 | 0 | MIS: ['A-98765432']; PAR: 2 corr... |
| professional_ids | real | 0 | 0 | 2 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Abogado'... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 partie... |
| vehicle_clause | real | 0 | 0 | 2 | 0 | 0 | PAR: 2 correspondances partielles |
| social_security | real | 0 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |

---

## 6. Comparaison v1 vs v2

| Métrique | v1 (lenient) | v2 (strict) | Différence |
|----------|--------------|-------------|------------|
| Pass rate | 51,4% | 31,4% | +20,0pp |
| F1 | 0,603 | 0,444 | +0,159 |

**Note :** v1 utilisait un matching lenient (confinement + 80% chevauchement). v2 utilise strict (limite exacte + type exact).

---

## 7. Références

- **SemEval 2013 Task 9** : Évaluation au niveau entité avec 4 modes (strict, exact, partiel, type)
- **RockNER (EMNLP 2021)** : Méthodologie d'évaluation NER adversariale
- **NoiseBench (EMNLP 2024)** : Benchmark bruit réel vs bruit simulé
- **nervaluate** : Bibliothèque Python pour évaluation NER style SemEval

**Généré par :** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Date :** 03/02/2026
