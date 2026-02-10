# Évaluation Adversariale v2 (Standards Académiques) - legal_ner_v2

**Date :** 05/02/2026
**Modèle :** legal_ner_v2
**Tests :** 35
**Temps total :** 1,4s
**Standard :** SemEval 2013 Task 9

---

## 1. Résumé Exécutif

### 1.1 Métriques SemEval 2013 (Mode Strict)

| Métrique | Valeur |
|----------|--------|
| **F1 (strict)** | **0,545** |
| Précision (strict) | 0,554 |
| Rappel (strict) | 0,537 |
| F1 (partiel) | 0,705 |

### 1.2 Décomptes SemEval

| Métrique | Valeur | Description |
|----------|--------|-------------|
| COR | 36 | Correct (limite + type exacts) |
| INC | 1 | Limite correcte, type incorrect |
| PAR | 21 | Correspondance partielle (chevauchement) |
| MIS | 9 | Manqués (FN) |
| SPU | 7 | Fallacieux (FP) |
| **POS** | 67 | Total or (COR+INC+PAR+MIS) |
| **ACT** | 65 | Total système (COR+INC+PAR+SPU) |

### 1.3 Taux de Réussite

| Mode | Passés | Total | Taux |
|------|--------|-------|------|
| **Strict** | 17 | 35 | **48,6%** |
| Lenient (v1) | 25 | 35 | 71,4% |

---

## 2. Métriques par Type d'Entité

| Type | COR | MIS | SPU | Précision | Rappel | F1 |
|------|-----|-----|-----|-----------|--------|----|
| ADDRESS | 1 | 2 | 2 | 0,33 | 0,33 | 0,33 |
| CADASTRAL_REF | 1 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| CIF | 0 | 0 | 1 | 0,00 | 0,00 | 0,00 |
| DATE | 2 | 2 | 3 | 0,40 | 0,50 | 0,44 |
| DNI_NIE | 10 | 3 | 1 | 0,91 | 0,77 | 0,83 |
| ECLI | 1 | 1 | 1 | 0,50 | 0,50 | 0,50 |
| IBAN | 1 | 2 | 1 | 0,50 | 0,33 | 0,40 |
| LICENSE_PLATE | 0 | 1 | 1 | 0,00 | 0,00 | 0,00 |
| LOCATION | 10 | 1 | 0 | 1,00 | 0,91 | 0,95 |
| NSS | 1 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| ORGANIZATION | 1 | 2 | 5 | 0,17 | 0,33 | 0,22 |
| PERSON | 6 | 13 | 13 | 0,32 | 0,32 | 0,32 |
| PHONE | 2 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| POSTAL_CODE | 0 | 2 | 1 | 0,00 | 0,00 | 0,00 |
| PROFESSIONAL_ID | 0 | 2 | 0 | 0,00 | 0,00 | 0,00 |

---

## 3. Résultats par Catégorie

| Catégorie | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 62% | 75% | 4 | 0 | 1 | 0 | 2 | 0,67 |
| edge_case | 67% | 100% | 10 | 0 | 2 | 0 | 1 | 0,80 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0,57 |
| real_world | 20% | 60% | 13 | 1 | 17 | 4 | 4 | 0,37 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0,91 |

## 4. Résultats par Difficulté

| Difficulté | Strict | Lenient | Total |
|------------|--------|---------|-------|
| facile | 75% | 100% | 4 |
| moyen | 58% | 92% | 12 |
| difficile | 37% | 53% | 19 |

---

## 5. Tests Échoués (Mode Strict)

| Test | Cat | COR | INC | PAR | MIS | SPU | Détail |
|------|-----|-----|-----|-----|-----|-----|--------|
| very_long_name | edge | 0 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| address_floor_door | edge | 2 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Don Quijote de la Mancha'] |
| mixed_languages | adve | 2 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 corresp... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| fullwidth_numbers | unic | 1 | 0 | 0 | 1 | 0 | MIS: ['María'] |
| notarial_header | real | 3 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| testament_comparecencia | real | 3 | 0 | 2 | 0 | 0 | PAR: 2 correspondances partielles |
| judicial_sentence_header | real | 1 | 0 | 3 | 0 | 1 | SPU: ['Sala Primera del Tribunal Supremo... |
| contract_parties | real | 2 | 0 | 4 | 2 | 0 | MIS: ['28013', 'Madrid']; PAR: 4 corresp... |
| bank_account_clause | real | 0 | 1 | 2 | 0 | 0 | INC: 1 type incorrect; PAR: 2 corresp... |
| professional_ids | real | 0 | 0 | 2 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Abogado'... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 corresp... |
| vehicle_clause | real | 0 | 0 | 2 | 0 | 0 | PAR: 2 correspondances partielles |

---

## 6. Comparaison v1 vs v2

| Métrique | v1 (lenient) | v2 (strict) | Différence |
|----------|--------------|-------------|------------|
| Pass rate | 71,4% | 48,6% | +22,9pp |
| F1 | 0,705 | 0,545 | +0,159 |

**Note :** v1 utilisait un matching lenient (confinement + 80% chevauchement). v2 utilise strict (limite exacte + type exact).

---

## 7. Références

- **SemEval 2013 Task 9** : Évaluation au niveau entité avec 4 modes (strict, exact, partiel, type)
- **RockNER (EMNLP 2021)** : Méthodologie d'évaluation NER adversariale
- **NoiseBench (EMNLP 2024)** : Benchmark bruit réel vs bruit simulé
- **nervaluate** : Bibliothèque Python pour évaluation NER style SemEval

**Généré par :** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Date :** 05/02/2026
