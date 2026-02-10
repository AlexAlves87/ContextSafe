# Checksum Validators - Test d'Intégration

**Date :** 04/02/2026
**Auteur :** AlexAlves87
**Composant :** Intégration de validateurs dans `scripts/inference/ner_predictor.py`
**Standard :** Algorithmes officiels espagnols (BOE)

---

## 1. Résumé Exécutif

Intégration et validation de validateurs de checksum dans le pipeline NER pour la post-validation des identifiants espagnols.

### Résultats

| Catégorie | Passés | Total | % |
|-----------|--------|-------|---|
| Tests unitaires | 13 | 13 | 100% |
| Tests d'intégration | 6 | 7 | 85,7% |
| Tests de confiance | 1 | 1 | 100% |
| **TOTAL** | **20** | **21** | **95,2%** |

### Conclusion

> **L'intégration des validateurs de checksum fonctionne correctement.**
> Le seul échec (IBAN valide non détecté) est un problème du modèle NER, pas de la validation.
> La confiance est ajustée de manière appropriée : +10% pour les valides, -20% pour les invalides.

---

## 2. Méthodologie

### 2.1 Conception de l'Intégration

| Aspect | Implémentation |
|--------|----------------|
| Emplacement | `scripts/inference/ner_predictor.py` |
| Types validables | DNI_NIE, IBAN, NSS, CIF |
| Moment | Post-extraction d'entités |
| Sortie | `checksum_valid`, `checksum_reason` dans PredictedEntity |

### 2.2 Ajustement de Confiance

| Résultat Checksum | Ajustement |
|-------------------|------------|
| Valide (`is_valid=True`) | `confidence * 1,1` (max 0,99) |
| Invalide, format ok (`conf=0,5`) | `confidence * 0,8` |
| Format invalide (`conf<0,5`) | `confidence * 0,5` |

### 2.3 Reproductibilité

```bash
# Environnement
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Exécution
python scripts/evaluate/test_checksum_integration.py

# Sortie attendue : 20/21 passed (95,2%)
```

---

## 3. Résultats

### 3.1 Tests Unitaires (13/13 ✅)

| Validateur | Test | Entrée | Résultat |
|------------|------|--------|----------|
| DNI | valide | `12345678Z` | ✅ Vrai |
| DNI | invalide | `12345678A` | ✅ Faux |
| DNI | zéros | `00000000T` | ✅ Vrai |
| NIE | X valide | `X0000000T` | ✅ Vrai |
| NIE | Y valide | `Y0000000Z` | ✅ Vrai |
| NIE | Z valide | `Z0000000M` | ✅ Vrai |
| NIE | invalide | `X0000000A` | ✅ Faux |
| IBAN | valide | `ES9121000418450200051332` | ✅ Vrai |
| IBAN | espaces | `ES91 2100 0418...` | ✅ Vrai |
| IBAN | invalide | `ES0000000000000000000000` | ✅ Faux |
| NSS | format | `281234567800` | ✅ Faux |
| CIF | valide | `A12345674` | ✅ Vrai |
| CIF | invalide | `A12345670` | ✅ Faux |

### 3.2 Tests d'Intégration (6/7)

| Test | Entrée | Détection | Checksum | Résultat |
|------|--------|-----------|----------|----------|
| dni_valid | `DNI 12345678Z` | ✅ conf=0,99 | valid=True | ✅ |
| dni_invalid | `DNI 12345678A` | ✅ conf=0,73 | valid=False | ✅ |
| nie_valid | `NIE X0000000T` | ✅ conf=0,86 | valid=True | ✅ |
| nie_invalid | `NIE X0000000A` | ✅ conf=0,61 | valid=False | ✅ |
| iban_valid | `IBAN ES91...` | ❌ Non détecté | - | ❌ |
| iban_invalid | `IBAN ES00...` | ✅ conf=0,25 | valid=False | ✅ |
| person | `Don José García` | ✅ conf=0,98 | valid=None | ✅ |

### 3.3 Ajustement de Confiance (1/1 ✅)

| ID | Type | Conf Base | Checksum | Conf Finale | Ajustement |
|----|------|-----------|----------|-------------|------------|
| `12345678Z` | DNI valide | ~0,90 | ✅ | **0,99** | +10% |
| `12345678A` | DNI invalide | ~0,91 | ❌ | **0,73** | -20% |

**Différence nette :** DNI valide a +0,27 confiance en plus que l'invalide.

---

## 4. Analyse des Erreurs

### 4.1 Seul Échec : IBAN Valide Non Détecté

| Aspect | Détail |
|--------|--------|
| Test | `iban_valid` |
| Entrée | `"Transferir a IBAN ES9121000418450200051332."` |
| Attendu | Détection IBAN avec checksum valide |
| Résultat | Modèle NER n'a pas détecté l'entité IBAN |
| Cause | Limitation du modèle legal_ner_v2 |

**Note :** Cet échec ne vient PAS de la validation de checksum, mais du modèle NER. La validation de checksum pour IBAN fonctionne correctement (prouvé dans les tests unitaires et le test IBAN invalide).

### 4.2 Observation : IBAN Invalide Inclut Préfixe

Le modèle a détecté `"IBAN ES0000000000000000000000"` incluant le mot "IBAN". Cela cause un format invalide (`invalid_format`) au lieu de `invalid_checksum`.

**Implication :** Le nettoyage du texte extrait avant validation peut être nécessaire.

---

## 5. Impact sur le Pipeline NER

### 5.1 Bénéfices Observés

| Bénéfice | Preuve |
|----------|--------|
| **Distinction valide/invalide** | DNI valide 0,99 vs invalide 0,73 |
| **Métadonnées supplémentaires** | `checksum_valid`, `checksum_reason` |
| **Réduction potentielle SPU** | IDs avec checksum invalide ont une confiance plus faible |

### 5.2 Cas d'Usage

| Scénario | Action Recommandée |
|----------|--------------------|
| checksum_valid=True | Haute confiance, traiter normalement |
| checksum_valid=False, reason=invalid_checksum | Possible coquille/OCR, vérifier manuellement |
| checksum_valid=False, reason=invalid_format | Possible faux positif, considérer filtrage |

---

## 6. Conclusions et Travaux Futurs

### 6.1 Conclusions

1. **Intégration réussie :** Les validateurs s'exécutent automatiquement dans le pipeline NER
2. **Ajustement de confiance fonctionne :** +10% pour les valides, -20% pour les invalides
3. **Métadonnées disponibles :** `checksum_valid` et `checksum_reason` dans chaque entité
4. **Surcharge minimale :** ~0ms supplémentaire (opérations chaînes/maths)

### 6.2 Prochaines Étapes

| Priorité | Tâche | Impact |
|----------|-------|--------|
| HAUTE | Évaluer impact sur métriques SemEval (réduction SPU) | Réduire faux positifs |
| MOYENNE | Nettoyer texte avant validation (retirer "IBAN ", etc.) | Améliorer précision |
| BASSE | Ajouter validation pour plus de types (téléphone, plaque) | Couverture |

### 6.3 Intégration Complète

La validation de checksum est maintenant intégrée dans :

```
ner_predictor.py
├── normalize_text_for_ner()     # Robustesse Unicode/OCR
├── _extract_entities()          # BIO → entités
└── validate_entity_checksum()   # ← NOUVEAU : post-validation
```

---

## 7. Références

1. **Tests autonomes :** `docs/reports/2026-02-04_checksum_validators_standalone.md`
2. **Recherche de base :** `docs/reports/2026-01-28_investigacion_hybrid_ner.md`
3. **Script d'intégration :** `scripts/inference/ner_predictor.py`
4. **Test d'intégration :** `scripts/evaluate/test_checksum_integration.py`

---

**Temps d'exécution :** 2,37s
**Généré par :** AlexAlves87
**Date :** 04/02/2026
