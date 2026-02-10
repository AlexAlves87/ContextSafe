# Analyse des Écarts : Tests Actuels vs Standards Académiques

**Date :** 2026-01-29
**Auteur :** AlexAlves87
**Fichier analysé :** `scripts/evaluate/test_ner_predictor_adversarial.py`

---

## 1. Résumé des Écarts

| Aspect | Standard Académique | Implémentation Actuelle | Sévérité |
|--------|---------------------|-------------------------|----------|
| Mode d'évaluation | Strict (SemEval 2013) | Indulgent (custom) | **CRITIQUE** |
| 4 Modes SemEval | strict, exact, partial, type | Seulement 1 mode custom | ÉLEVÉE |
| Librairie de métriques | seqeval ou nervaluate | Implémentation custom | ÉLEVÉE |
| Métriques détaillées | COR/INC/PAR/MIS/SPU | Seulement TP/FP/FN | MOYENNE |
| Métriques par type | F1 par PERSON, DNI, etc. | Seulement F1 agrégé | MOYENNE |
| Référence NoiseBench | EMNLP 2024 | "ICLR 2024" (erreur) | FAIBLE |
| Documentation du mode | Explicite dans le rapport | Non documenté | MOYENNE |

---

## 2. Analyse Détaillée

### 2.1 CRITIQUE : Le Mode de Correspondance N'est Pas Strict

**Code Actuel (lignes 458-493) :**

```python
def entities_match(expected: dict, detected: dict, tolerance: int = 5) -> bool:
    # Type must match
    if expected["type"] != detected["type"]:
        return False

    # Containment (detected contains expected or vice versa)
    if exp_text in det_text or det_text in exp_text:
        return True

    # Length difference tolerance
    if abs(len(exp_text) - len(det_text)) <= tolerance:
        # Check character overlap
        common = sum(1 for c in exp_text if c in det_text)
        if common >= len(exp_text) * 0.8:
            return True
```

**Problèmes :**
1. Autorise **containment** (Si "José García" est dans "Don José García López", ça compte comme match)
2. Autorise **80% de chevauchement de caractères** (pas de frontière exacte)
3. Autorise **tolérance de 5 caractères** en longueur

**Standard SemEval Strict :**
> "Correspondance exacte de la chaîne de surface de la frontière ET correspondance du type d'entité"

**Impact :** Les résultats actuels (F1=0.784, taux de réussite 54.3%) pourraient être **GONFLÉS** car les correspondances partielles sont acceptées comme correctes.

### 2.2 ÉLEVÉE : N'utilise ni seqeval ni nervaluate

**Standard :** Utiliser des librairies validées contre conlleval.

**Actuel :** Implémentation de métriques personnalisée.

**Risque :** Les métriques personnalisées peuvent ne pas être comparables avec la littérature académique.

### 2.3 ÉLEVÉE : Un Seul Mode d'Évaluation

**SemEval 2013 définit 4 modes :**

| Mode | Frontière | Type | Usage |
|------|-----------|------|-------|
| **strict** | Exact | Exact | Principal, rigoureux |
| exact | Exact | Ignoré | Analyse de frontière |
| partial | Chevauchement | Ignoré | Analyse indulgente |
| type | Chevauchement | Exact | Analyse de classification |

**Actuel :** Un seul mode personnalisé (similaire à partial/indulgent).

**Impact :** Nous ne pouvons pas séparer les erreurs de frontière des erreurs de type.

### 2.4 MOYENNE : Pas de Métriques COR/INC/PAR/MIS/SPU

**SemEval 2013 :**
- **COR** : Correct (frontière ET type exacts)
- **INC** : Incorrect (frontière exacte, type incorrect)
- **PAR** : Partial (frontière avec chevauchement)
- **MIS** : Missing (FN)
- **SPU** : Spurious (FP)

**Actuel :** Seulement TP/FP/FN (ne distingue pas INC de PAR).

### 2.5 MOYENNE : Pas de Métriques par Type d'Entité

**Standard :** Rapporter F1 pour chaque type (PERSON, DNI_NIE, IBAN, etc.)

**Actuel :** Seulement F1 agrégé.

**Impact :** Nous ne savons pas quels types d'entités performent le moins bien.

### 2.6 FAIBLE : Erreur de Référence

**Ligne 10 :** `NoiseBench (ICLR 2024)`

**Correct :** `NoiseBench (EMNLP 2024)`

---

## 3. Impact sur les Résultats Rapportés

### 3.1 Estimation de la Différence Strict vs Indulgent

Basé sur la littérature, le mode strict produit typiquement **5-15% de F1 en moins** que le mode indulgent :

| Métrique | Actuel (indulgent) | Estimé (strict) |
|----------|--------------------|-----------------|
| F1 | 0.784 | 0.67-0.73 |
| Taux de réussite | 54.3% | 40-48% |

**Les résultats actuels sont optimistes.**

### 3.2 Tests Affectés par la Correspondance Indulgente

Tests où la correspondance indulgente accepte comme correct ce que le strict rejetterait :

| Test | Situation | Impact |
|------|-----------|--------|
| `very_long_name` | Nom long, frontière exacte ? | Possible |
| `address_floor_door` | Adresse complexe | Possible |
| `testament_comparecencia` | Entités multiples | Élevé |
| `judicial_sentence_header` | Dates textuelles | Élevé |

---

## 4. Plan de Remédiation

### 4.1 Changements Requis

1. **Implémenter le mode strict** (priorité CRITIQUE)
   - La frontière doit être exacte (normalisée)
   - Le type doit être exact

2. **Ajouter nervaluate** (priorité ÉLEVÉE)
   ```bash
   pip install nervaluate
   ```

3. **Rapporter 4 modes** (priorité ÉLEVÉE)
   - strict (principal)
   - exact
   - partial
   - type

4. **Ajouter métriques par type** (priorité MOYENNE)

5. **Corriger référence NoiseBench** (priorité FAIBLE)

### 4.2 Stratégie de Migration

Pour maintenir la comparabilité avec les résultats précédents :

1. Exécuter avec **les deux modes** (indulgent ET strict)
2. Rapporter **les deux** dans la documentation
3. Utiliser **strict comme métrique principale** à l'avenir
4. Documenter la différence pour la baseline

---

## 5. Nouveau Script Proposé

Créer `test_ner_predictor_adversarial_v2.py` avec :

1. Mode strict par défaut
2. Intégration avec nervaluate
3. Métriques COR/INC/PAR/MIS/SPU
4. F1 par type d'entité
5. Option de mode legacy pour comparaison

---

## 6. Conclusions

**Les résultats actuels (F1=0.784, 54.3% réussite) ne sont pas comparables avec la littérature académique** parce que :

1. Ils utilisent une correspondance indulgente, pas stricte
2. Ils n'utilisent pas de librairies standard (seqeval, nervaluate)
3. Ils ne rapportent pas de métriques granulaires (par type, COR/INC/PAR)

**Action Immédiate :** Avant de procéder à l'intégration de TextNormalizer, nous devons :

1. Créer le script v2 avec les standards académiques
2. Ré-établir la baseline avec le mode strict
3. ENSUITE évaluer l'impact de l'amélioration

---

**Généré par :** AlexAlves87
**Date :** 2026-01-29
