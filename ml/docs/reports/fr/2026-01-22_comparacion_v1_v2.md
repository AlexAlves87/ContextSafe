# Comparaison : Modèle v1 vs v2 (Entraînement avec Bruit)

**Date :** 2026-01-22
**Type :** Analyse Comparative
**Statut :** Terminé

---

## Résumé Exécutif

| Métrique | v1 | v2 | Changement |
|---------|-----|-----|--------|
| Taux de Réussite Adversarial | 45.7% (16/35) | 54.3% (19/35) | **+8.6 pp** |
| F1 Test Synthétique | 99.87% | 100% | +0.13 pp |
| Jeu de Données | v2 (propre) | v3 (30% bruit) | - |

**Conclusion :** L'injection de bruit OCR pendant l'entraînement a amélioré la robustesse du modèle de +8.6 points de pourcentage dans les tests adversariaux.

---

## Méthodologie

### Différences d'Entraînement

| Aspect | v1 | v2 |
|---------|-----|-----|
| Jeu de Données | `ner_dataset_v2` | `ner_dataset_v3` |
| Injection de Bruit | 0% | 30% |
| Types de Bruit | - | l↔I, 0↔O, accents, espaces |
| Hyperparamètres | Identiques | Identiques |
| Modèle de Base | roberta-bne-capitel-ner | roberta-bne-capitel-ner |

### Tests Adversariaux (35 cas)

| Catégorie | Tests |
|-----------|-------|
| edge_case | 9 |
| adversarial | 8 |
| ocr_corruption | 5 |
| unicode_evasion | 3 |
| real_world | 10 |

---

## Résultats par Catégorie

### Comparaison des Taux de Réussite

| Catégorie | v1 | v2 | Amélioration |
|-----------|-----|-----|--------|
| edge_case | 55.6% (5/9) | 66.7% (6/9) | +11.1 pp |
| adversarial | 37.5% (3/8) | 62.5% (5/8) | **+25.0 pp** |
| ocr_corruption | 20.0% (1/5) | 40.0% (2/5) | **+20.0 pp** |
| unicode_evasion | 33.3% (1/3) | 33.3% (1/3) | 0 pp |
| real_world | 60.0% (6/10) | 50.0% (5/10) | -10.0 pp |

### Analyse par Catégorie

**Améliorations Significatives (+20 pp ou plus) :**
- **adversarial** : +25 pp - Meilleure discrimination du contexte (négation, exemples)
- **ocr_corruption** : +20 pp - Le bruit à l'entraînement a aidé directement

**Aucun Changement :**
- **unicode_evasion** : 33.3% - Nécessite une normalisation du texte, pas seulement de l'entraînement

**Régression :**
- **real_world** : -10 pp - Possible sur-apprentissage du bruit, moins de robustesse aux modèles complexes

---

## Détail des Tests Changés

### Tests RÉUSSIS en v2 (précédemment ÉCHOUÉS)

| Test | Catégorie | Note |
|------|-----------|------|
| `ocr_letter_substitution` | ocr_corruption | DNl → DNI (l vs I) |
| `ocr_accent_loss` | ocr_corruption | José → Jose |
| `negation_dni` | adversarial | "NO tener DNI" - ne détecte plus de PII |
| `organization_as_person` | adversarial | García y Asociados → ORG |
| `location_as_person` | adversarial | San Fernando → LOCATION |

### Tests ÉCHOUÉS en v2 (précédemment RÉUSSIS)

| Test | Catégorie | Note |
|------|-----------|------|
| `notarial_header` | real_world | Régression possible sur les dates écrites |
| `judicial_sentence_header` | real_world | Régression possible sur les noms en majuscules |

---

## Conclusions

### Principales Découvertes

1. **L'entraînement avec bruit fonctionne** : +8.6 pp d'amélioration globale, surtout en OCR et adversarial
2. **Le bruit spécifique compte** : l↔I, accents améliorés, mais 0↔O et espaces échouent encore
3. **Compromis observé** : Gain de robustesse au bruit mais perte de précision sur les modèles complexes

### Limites de l'Approche

1. **Bruit insuffisant pour 0↔O** : IBAN avec O au lieu de 0 échoue encore
2. **Normalisation nécessaire** : L'évasion Unicode nécessite un prétraitement, pas seulement de l'entraînement
3. **Complexité du monde réel** : Les documents complexes nécessitent plus de données d'entraînement

### Recommandations

| Priorité | Action | Impact Attendu |
|-----------|--------|------------------|
| HAUTE | Ajouter la normalisation Unicode en prétraitement | +10% unicode_evasion |
| HAUTE | Plus de variété de bruit 0↔O à l'entraînement | +5-10% ocr_corruption |
| MOYENNE | Plus d'exemples real_world dans le jeu de données | Récupérer -10% real_world |
| MOYENNE | Pipeline hybride (Regex → NER → Validation) | +15-20% selon la littérature |

---

## Prochaines Étapes

1. **Implémenter le pipeline hybride** selon la recherche PMC12214779
2. **Ajouter text_normalizer.py** comme prétraitement avant l'inférence
3. **Étendre le jeu de données** avec plus d'exemples de documents réels
4. **Évaluer la couche CRF** pour améliorer la cohérence des séquences

---

## Fichiers Associés

- `docs/reports/2026-01-20_adversarial_evaluation.md` - Évaluation v1
- `docs/reports/2026-01-21_adversarial_evaluation_v2.md` - Évaluation v2
- `docs/reports/2026-01-16_investigacion_pipeline_pii.md` - Bonnes pratiques
- `scripts/preprocess/inject_ocr_noise.py` - Script d'injection de bruit

---

**Date :** 2026-01-22
