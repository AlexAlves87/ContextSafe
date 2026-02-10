# Évaluation Adversariale v2 (Standards Académiques) - legal_ner_v2

**Date :** 06/02/2026
**Modèle :** legal_ner_v2
**Tests :** 35
**Temps total :** 1,4s
**Standard :** SemEval 2013 Task 9

---

## 1. Résumé Exécutif

### 1.1 Métriques SemEval 2013 (Mode Strict)

| Métrique | Valeur |
|----------|--------|
| **F1 (strict)** | **0,776** |
| Précision (strict) | 0,776 |
| Rappel (strict) | 0,776 |
| F1 (partiel) | 0,813 |

### 1.2 Décomptes SemEval

| Métrique | Valeur | Description |
|----------|--------|-------------|
| COR | 52 | Correct (limite + type exacts) |
| INC | 1 | Limite correcte, type incorrect |
| PAR | 5 | Correspondance partielle (chevauchement) |
| MIS | 9 | Manqués (FN) |
| SPU | 9 | Fallacieux (FP) |
| **POS** | 67 | Total or (COR+INC+PAR+MIS) |
| **ACT** | 67 | Total système (COR+INC+PAR+SPU) |

### 1.3 Taux de Réussite

| Mode | Passés | Total | Taux |
|------|--------|-------|------|
| **Strict** | 19 | 35 | **54,3%** |
| Lenient (v1) | 25 | 35 | 71,4% |

---

## 2. Métriques par Type d'Entité

| Type | COR | MIS | SPU | Précision | Rappel | F1 |
|------|-----|-----|-----|-----------|--------|----|
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

## 3. Résultats par Catégorie

| Catégorie | Strict | Lenient | COR | INC | PAR | MIS | SPU | F1 strict |
|-----------|--------|---------|-----|-----|-----|-----|-----|-----------|
| adversarial | 75% | 75% | 5 | 0 | 0 | 0 | 2 | 0,83 |
| edge_case | 78% | 100% | 11 | 0 | 1 | 0 | 1 | 0,88 |
| ocr_corruption | 40% | 40% | 4 | 0 | 1 | 4 | 0 | 0,57 |
| real_world | 20% | 60% | 27 | 1 | 3 | 4 | 6 | 0,75 |
| unicode_evasion | 67% | 67% | 5 | 0 | 0 | 1 | 0 | 0,91 |

## 4. Résultats par Difficulté

| Difficulté | Strict | Lenient | Total |
|------------|--------|---------|-------|
| facile | 50% | 100% | 4 |
| moyen | 67% | 92% | 12 |
| difficile | 47% | 53% | 19 |

---

## 5. Tests Échoués (Mode Strict)

| Test | Cat | COR | INC | PAR | MIS | SPU | Détail |
|------|-----|-----|-----|-----|-----|-----|--------|
| phone_international | edge | 1 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| date_ordinal | edge | 1 | 0 | 0 | 0 | 1 | SPU: ['El'] |
| example_dni | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['12345678X'] |
| fictional_person | adve | 0 | 0 | 0 | 0 | 1 | SPU: ['Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_ | 0 | 0 | 0 | 1 | 0 | MIS: ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_ | 0 | 0 | 1 | 1 | 0 | MIS: ['12345678X']; PAR: 1 corresp... |
| ocr_extra_spaces | ocr_ | 0 | 0 | 0 | 2 | 0 | MIS: ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| fullwidth_numbers | unic | 1 | 0 | 0 | 1 | 0 | MIS: ['María'] |
| testament_comparecencia | real | 4 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| judicial_sentence_header | real | 4 | 0 | 0 | 0 | 1 | SPU: ['Sala Primera del Tribunal Supremo... |
| contract_parties | real | 6 | 0 | 0 | 2 | 1 | MIS: ['28013', 'Madrid']; SPU: ['B-12345... |
| bank_account_clause | real | 2 | 1 | 0 | 0 | 0 | INC: 1 type incorrect |
| professional_ids | real | 2 | 0 | 0 | 2 | 2 | MIS: ['12345', '67890']; SPU: ['Abogado'... |
| ecli_citation | real | 1 | 0 | 1 | 0 | 1 | SPU: ['Tribunal Supremo']; PAR: 1 corresp... |
| vehicle_clause | real | 1 | 0 | 1 | 0 | 0 | PAR: 1 correspondance partielle |
| social_security | real | 1 | 0 | 0 | 0 | 1 | SPU: ['28'] |

---

## 6. Comparaison v1 vs v2

| Métrique | v1 (lenient) | v2 (strict) | Différence |
|----------|--------------|-------------|------------|
| Pass rate | 71,4% | 54,3% | +17,1pp |
| F1 | 0,813 | 0,776 | +0,037 |

**Note :** v1 utilisait un matching lenient (confinement + 80% chevauchement). v2 utilise strict (limite exacte + type exact).

---

## 7. Références

- **SemEval 2013 Task 9** : Évaluation au niveau entité avec 4 modes (strict, exact, partiel, type)
- **RockNER (EMNLP 2021)** : Méthodologie d'évaluation NER adversariale
- **NoiseBench (EMNLP 2024)** : Benchmark bruit réel vs bruit simulé
- **nervaluate** : Bibliothèque Python pour évaluation NER style SemEval

**Généré par :** `scripts/evaluate/test_ner_predictor_adversarial_v2.py`
**Date :** 06/02/2026
