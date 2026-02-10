# Modèles de Date - Test d'Intégration

**Date :** 05/02/2026
**Auteur :** AlexAlves87
**Composant :** `scripts/preprocess/spanish_date_patterns.py` intégré dans le pipeline
**Standard :** TIMEX3 pour expressions temporelles

---

## 1. Résumé Exécutif

Intégration de modèles regex pour les dates textuelles espagnoles qui complètent la détection NER.

### Résultats

| Suite de Test | Résultat |
|---------------|----------|
| Tests autonomes | 14/14 (100%) |
| Tests d'intégration | 9/9 (100%) |
| Adversarial (amélioration) | +2,9pp taux de réussite |

### Conclusion

> **Les modèles de date ajoutent de la valeur principalement pour les chiffres romains.**
> Le modèle NER détecte déjà la plupart des dates textuelles.
> Amélioration totale cumulée : Taux de réussite +20pp, F1 +0,081 depuis la baseline.

---

## 2. Méthodologie

### 2.1 Modèles Implémentés (10 total)

| Modèle | Exemple | Confiance |
|--------|---------|-----------|
| `date_roman_full` | XV de marzo del año MMXXIV | 0,95 |
| `date_roman_day_written_year` | XV de marzo de dos mil... | 0,90 |
| `date_written_full` | quince de marzo de dos mil... | 0,95 |
| `date_ordinal_full` | primero de enero de dos mil... | 0,95 |
| `date_written_day_numeric_year` | quince de marzo de 2024 | 0,90 |
| `date_ordinal_numeric_year` | primero de enero de 2024 | 0,90 |
| `date_a_written` | a veinte de abril de dos mil... | 0,90 |
| `date_el_dia_written` | el día quince de marzo de... | 0,90 |
| `date_numeric_standard` | 15 de marzo de 2024 | 0,85 |
| `date_formal_legal` | día 15 del mes de marzo del año 2024 | 0,90 |

### 2.2 Intégration

Les modèles de date ont été intégrés dans `spanish_id_patterns.py` :

```python
# Dans find_matches() :
if DATE_PATTERNS_AVAILABLE and (entity_types is None or "DATE" in entity_types):
    date_matches = find_date_matches(text)
    for dm in date_matches:
        matches.append(RegexMatch(
            text=dm.text,
            entity_type="DATE",
            ...
        ))
```

### 2.3 Reproductibilité

```bash
# Environnement
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate

# Test autonome
python scripts/preprocess/spanish_date_patterns.py

# Test intégration
python scripts/evaluate/test_date_integration.py

# Test adversarial complet
python scripts/evaluate/test_ner_predictor_adversarial_v2.py
```

---

## 3. Résultats

### 3.1 Tests d'Intégration (9/9)

| Test | Texte | Source | Résultat |
|------|-------|--------|----------|
| roman_full | XV de marzo del año MMXXIV | **regex** | ✅ |
| ordinal_full | primero de enero de dos mil... | ner | ✅ |
| notarial_date | quince de marzo de dos mil... | ner | ✅ |
| testament_date | diez de enero de dos mil... | ner | ✅ |
| written_full | veintiocho de febrero de... | ner | ✅ |
| numeric_standard | 15 de marzo de 2024 | ner | ✅ |
| multiple_dates | uno de enero...diciembre... | ner | ✅ |
| date_roman_numerals | XV de marzo del año MMXXIV | **regex** | ✅ |
| date_ordinal | primero de enero de... | ner | ✅ |

### 3.2 Observation Clé

**Le modèle NER détecte déjà la plupart des dates textuelles.** Le regex ajoute de la valeur seulement pour :
- **Chiffres romains** (XV, MMXXIV) - pas dans le vocabulaire du modèle

### 3.3 Impact sur Tests Adversariaux

| Métrique | Avant | Après | Delta |
|----------|-------|-------|-------|
| Taux de Réussite | 45,7% | **48,6%** | **+2,9pp** |
| F1 (strict) | 0,543 | **0,545** | +0,002 |
| F1 (partiel) | 0,690 | **0,705** | +0,015 |
| COR | 35 | **36** | **+1** |
| MIS | 12 | **9** | **-3** |
| PAR | 19 | 21 | +2 |

---

## 4. Progrès Total Cumulé

### 4.1 Éléments Intégrés

| Élément | Autonome | Intégration | Impact Principal |
|---------|----------|-------------|------------------|
| 1. TextNormalizer | 15/15 | ✅ | Evasion Unicode |
| 2. Checksum | 23/24 | ✅ | Ajustement confiance |
| 3. Regex IDs | 22/22 | ✅ | Identifiants espacés |
| 4. Modèles Date | 14/14 | ✅ | Chiffres romains |

### 4.2 Métriques Totales

| Métrique | Baseline | Actuel | Amélioration | Objectif | Écart |
|----------|----------|--------|--------------|----------|-------|
| **Taux de Réussite** | 28,6% | **48,6%** | **+20pp** | ≥70% | -21,4pp |
| **F1 (strict)** | 0,464 | **0,545** | **+0,081** | ≥0,70 | -0,155 |
| COR | 29 | 36 | +7 | - | - |
| MIS | 17 | 9 | -8 | - | - |
| SPU | 8 | 7 | -1 | - | - |
| PAR | 21 | 21 | 0 | - | - |

### 4.3 Progrès Visuel

```
Taux de Réussite :
Baseline   [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░] 28,6%
Actuel     [█████████████████░░░░░░░░░░░░░░░░░░] 48,6%
Objectif   [████████████████████████████░░░░░░░] 70,0%

F1 (strict) :
Baseline   [████████████████░░░░░░░░░░░░░░░░░░░] 0,464
Actuel     [███████████████████░░░░░░░░░░░░░░░░] 0,545
Objectif   [████████████████████████████░░░░░░░] 0,700
```

---

## 5. Conclusions et Travaux Futurs

### 5.1 Conclusions

1. **Progrès significatif** : +20pp taux de réussite, +0,081 F1 depuis baseline
2. **MIS réduit drastiquement** : 17 → 9 (-8 entités manquées)
3. **Pipeline hybride fonctionne** : NER + Regex + Checksum se complètent
4. **Modèle NER est robuste pour dates** : Nécessite regex seulement pour romains

### 5.2 Écart Restant

| Pour atteindre l'objectif | Nécessaire |
|---------------------------|------------|
| Taux réussite 70% | +21,4pp plus |
| F1 0,70 | +0,155 plus |
| Équivalent à | ~8-10 COR additionnels |

### 5.3 Prochaines Étapes Potentielles

| Priorité | Amélioration | Impact Estimé |
|----------|--------------|---------------|
| HAUTE | Raffinement des limites (PAR→COR) | +5-6 COR |
| MOYENNE | Augmentation données modèle | +3-4 COR |
| MOYENNE | Corriger classification CIF | +1 COR |
| BASSE | Améliorer détection phone_intl | +1 COR |

---

## 6. Références

1. **Tests autonomes :** `scripts/preprocess/spanish_date_patterns.py`
2. **Tests d'intégration :** `scripts/evaluate/test_date_integration.py`
3. **TIMEX3 :** Standard d'annotation ISO-TimeML
4. **HeidelTime/SUTime :** Tagueurs temporels de référence

---

**Temps d'exécution :** 2,51s (intégration) + 1,4s (adversarial)
**Généré par :** AlexAlves87
**Date :** 05/02/2026
