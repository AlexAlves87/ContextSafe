# Évaluation Adversariale - legal_ner_v2

**Date :** 2026-01-23
**Modèle :** legal_ner_v2
**Tests :** 35
**Temps Total :** 1.4s

---

## Résumé Exécutif

### Métriques Entity-Level (style seqeval)

| Métrique | Valeur |
|---------|-------|
| Précision | 0.845 |
| Rappel | 0.731 |
| **Score F1** | **0.784** |
| Vrais Positifs | 49 |
| Faux Positifs | 9 |
| Faux Négatifs | 18 |
| Score Moyen de Chevauchement | 0.935 |

### Résistance au Bruit (style NoiseBench)

| Métrique | Valeur | Référence |
|---------|-------|------------|
| F1 (texte propre) | 0.800 | - |
| F1 (avec bruit) | 0.720 | - |
| Dégradation | 0.080 | ≤0.10 attendu |
| Statut | ✅ OK | Réf. HAL Science |

### Tests par Résultat

| Métrique | Valeur |
|---------|-------|
| Tests Totaux | 35 |
| Réussis | 19 (54.3%) |
| Échoués | 16 (45.7%) |

### Par Catégorie (avec F1)

| Catégorie | Taux de Réussite | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### Par Difficulté

| Difficulté | Réussis | Total | Taux |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

---

## Analyse des Erreurs

### Tests Échoués

| ID Test | Catégorie | Manqué | FP | Détail |
|---------|-----------|--------|----|---------|
| dni_with_spaces | edge_case | 1 | 0 | Manqué : ['12 345 678 Z'] |
| phone_international | edge_case | 1 | 0 | Manqué : ['0034612345678'] |
| date_roman_numerals | edge_case | 1 | 0 | Manqué : ['XV de marzo del año MMXXIV'] |
| example_dni | adversarial | 0 | 1 | FP : ['12345678X'] |
| fictional_person | adversarial | 0 | 1 | FP : ['Don Quijote de la Mancha'] |
| ocr_zero_o_confusion | ocr_corruption | 1 | 0 | Manqué : ['ES91 21O0 0418 45O2 OOO5 1332'] |
| ocr_missing_spaces | ocr_corruption | 1 | 0 | Manqué : ['12345678X'] |
| ocr_extra_spaces | ocr_corruption | 2 | 0 | Manqué : ['1 2 3 4 5 6 7 8 Z', 'M a r í a'] |
| zero_width_space | unicode_evasion | 0 | 1 | FP : ['de'] |
| fullwidth_numbers | unicode_evasion | 2 | 0 | Manqué : ['１２３４５６７８Z', 'María'] |
| notarial_header | real_world | 1 | 0 | Manqué : ['quince de marzo de dos mil veinticuatro'... |
| judicial_sentence_header | real_world | 1 | 2 | Manqué : ['diez de enero de dos mil veinticuatro'];... |
| contract_parties | real_world | 2 | 0 | Manqué : ['28013', 'Madrid'] |
| bank_account_clause | real_world | 1 | 0 | Manqué : ['A-98765432'] |
| professional_ids | real_world | 3 | 1 | Manqué : ['12345', 'MIGUEL TORRES', '67890']; FP : [... |
| social_security | real_world | 1 | 1 | Manqué : ['281234567890']; FP : ['28'] |

---

## Résultats Détaillés

### ADVERSARIAL

#### date_in_reference [✅ PASS]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 0 | **Détecté :** 0
**Correct :** 0 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### example_dni [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 0 | **Détecté :** 1
**Correct :** 0 | **Manqué :** 0 | **FP :** 1
**Détails :** FP : ['12345678X']

#### fictional_person [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 0 | **Détecté :** 1
**Correct :** 0 | **Manqué :** 0 | **FP :** 1
**Détails :** FP : ['Don Quijote de la Mancha']

#### location_as_person [✅ PASS]

**Difficulté :** hard | **Chevauchement :** 1.00
**Attendu :** 1 | **Détecté :** 1
**Correct :** 1 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### mixed_languages [✅ PASS]

**Difficulté :** hard | **Chevauchement :** 0.94
**Attendu :** 3 | **Détecté :** 3
**Correct :** 3 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### negation_dni [✅ PASS]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 0 | **Détecté :** 0
**Correct :** 0 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### numbers_not_dni [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 0.00
**Attendu :** 0 | **Détecté :** 0
**Correct :** 0 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### organization_as_person [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 1.00
**Attendu :** 1 | **Détecté :** 1
**Correct :** 1 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

### EDGE_CASE

#### address_floor_door [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 0.83
**Attendu :** 3 | **Détecté :** 3
**Correct :** 3 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### date_ordinal [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 1.00
**Attendu :** 1 | **Détecté :** 2
**Correct :** 1 | **Manqué :** 0 | **FP :** 1
**Détails :** FP : ['El']

#### date_roman_numerals [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 1 | **Détecté :** 0
**Correct :** 0 | **Manqué :** 1 | **FP :** 0
**Détails :** Manqué : ['XV de marzo del año MMXXIV']

#### dni_with_spaces [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 1 | **Détecté :** 0
**Correct :** 0 | **Manqué :** 1 | **FP :** 0
**Détails :** Manqué : ['12 345 678 Z']

#### dni_without_letter [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 1.00
**Attendu :** 1 | **Détecté :** 1
**Correct :** 1 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### iban_with_spaces [✅ PASS]

**Difficulté :** easy | **Chevauchement :** 0.91
**Attendu :** 1 | **Détecté :** 1
**Correct :** 1 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### phone_international [❌ FAIL]

**Difficulté :** medium | **Chevauchement :** 1.00
**Attendu :** 2 | **Détecté :** 1
**Correct :** 1 | **Manqué :** 1 | **FP :** 0
**Détails :** Manqué : ['0034612345678']

#### single_letter_name [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 1.00
**Attendu :** 1 | **Détecté :** 1
**Correct :** 1 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### very_long_name [✅ PASS]

**Difficulté :** hard | **Chevauchement :** 1.00
**Attendu :** 1 | **Détecté :** 1
**Correct :** 1 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

### OCR_CORRUPTION

#### ocr_accent_loss [✅ PASS]

**Difficulté :** easy | **Chevauchement :** 1.00
**Attendu :** 2 | **Détecté :** 2
**Correct :** 2 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### ocr_extra_spaces [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 2 | **Détecté :** 0
**Correct :** 0 | **Manqué :** 2 | **FP :** 0
**Détails :** Manqué : ['1 2 3 4 5 6 7 8 Z', 'M a r í a']

#### ocr_letter_substitution [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 1.00
**Attendu :** 2 | **Détecté :** 2
**Correct :** 2 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### ocr_missing_spaces [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.88
**Attendu :** 2 | **Détecté :** 1
**Correct :** 1 | **Manqué :** 1 | **FP :** 0
**Détails :** Manqué : ['12345678X']

#### ocr_zero_o_confusion [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 1 | **Détecté :** 0
**Correct :** 0 | **Manqué :** 1 | **FP :** 0
**Détails :** Manqué : ['ES91 21O0 0418 45O2 OOO5 1332']

### REAL_WORLD

#### bank_account_clause [❌ FAIL]

**Difficulté :** medium | **Chevauchement :** 0.88
**Attendu :** 3 | **Détecté :** 2
**Correct :** 2 | **Manqué :** 1 | **FP :** 0
**Détails :** Manqué : ['A-98765432']

#### cadastral_reference [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 1.00
**Attendu :** 2 | **Détecté :** 2
**Correct :** 2 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### contract_parties [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.88
**Attendu :** 8 | **Détecté :** 6
**Correct :** 6 | **Manqué :** 2 | **FP :** 0
**Détails :** Manqué : ['28013', 'Madrid']

#### ecli_citation [✅ PASS]

**Difficulté :** easy | **Chevauchement :** 0.90
**Attendu :** 2 | **Détecté :** 3
**Correct :** 2 | **Manqué :** 0 | **FP :** 1
**Détails :** FP : ['Tribunal Supremo']

#### judicial_sentence_header [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.92
**Attendu :** 4 | **Détecté :** 5
**Correct :** 3 | **Manqué :** 1 | **FP :** 2
**Détails :** Manqué : ['diez de enero de dos mil veinticuatro']; FP : ['Nº 123/2024', 'Sala Primera del Tribunal Supremo']

#### notarial_header [❌ FAIL]

**Difficulté :** medium | **Chevauchement :** 1.00
**Attendu :** 4 | **Détecté :** 3
**Correct :** 3 | **Manqué :** 1 | **FP :** 0
**Détails :** Manqué : ['quince de marzo de dos mil veinticuatro']

#### professional_ids [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.65
**Attendu :** 4 | **Détecté :** 2
**Correct :** 1 | **Manqué :** 3 | **FP :** 1
**Détails :** Manqué : ['12345', 'MIGUEL TORRES', '67890']; FP : ['Colegio de Procuradores de Madrid']

#### social_security [❌ FAIL]

**Difficulté :** easy | **Chevauchement :** 0.00
**Attendu :** 1 | **Détecté :** 1
**Correct :** 0 | **Manqué :** 1 | **FP :** 1
**Détails :** Manqué : ['281234567890']; FP : ['28']

#### testament_comparecencia [✅ PASS]

**Difficulté :** hard | **Chevauchement :** 0.99
**Attendu :** 5 | **Détecté :** 5
**Correct :** 5 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### vehicle_clause [✅ PASS]

**Difficulté :** medium | **Chevauchement :** 0.72
**Attendu :** 2 | **Détecté :** 2
**Correct :** 2 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

### UNICODE_EVASION

#### cyrillic_o [✅ PASS]

**Difficulté :** hard | **Chevauchement :** 0.94
**Attendu :** 2 | **Détecté :** 2
**Correct :** 2 | **Manqué :** 0 | **FP :** 0
**Détails :** OK

#### fullwidth_numbers [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 0.00
**Attendu :** 2 | **Détecté :** 0
**Correct :** 0 | **Manqué :** 2 | **FP :** 0
**Détails :** Manqué : ['１２３４５６７８Z', 'María']

#### zero_width_space [❌ FAIL]

**Difficulté :** hard | **Chevauchement :** 1.00
**Attendu :** 2 | **Détecté :** 3
**Correct :** 2 | **Manqué :** 0 | **FP :** 1
**Détails :** FP : ['de']

---

## Références

- **seqeval** : Métriques d'évaluation au niveau entité pour NER
- **NoiseBench (ICLR 2024)** : Évaluation bruit réel vs simulé
- **HAL Science** : Évaluation de l'impact de l'OCR (~10pt de dégradation F1 attendue)

**Généré par :** `scripts/evaluate/test_ner_predictor_adversarial.py`
**Date :** 2026-01-23
