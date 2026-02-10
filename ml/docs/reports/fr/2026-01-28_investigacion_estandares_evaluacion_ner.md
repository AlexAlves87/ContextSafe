# Recherche : Normes Académiques pour l'Évaluation NER

**Date :** 2026-01-28
**Auteur :** AlexAlves87
**Type :** Revue de Littérature Académique
**État :** Terminé

---

## 1. Résumé Exécutif

Cette recherche documente les normes académiques pour l'évaluation des systèmes NER, en mettant l'accent sur :
1. Métriques au niveau de l'entité (SemEval 2013 Task 9)
2. Évaluation contradictoire (RockNER, NoiseBench)
3. Frameworks d'évaluation (seqeval, nervaluate)
4. Meilleures pratiques pour les tests de robustesse

### Principales Découvertes

| Découverte | Source | Impact |
|------------|--------|--------|
| 4 modes d'évaluation : strict, exact, partiel, type | SemEval 2013 | **CRITIQUE** |
| seqeval est la norme de facto pour le F1 au niveau de l'entité | CoNLL, HuggingFace | Haut |
| RockNER : perturbations au niveau entité + contexte | EMNLP 2021 | Haut |
| NoiseBench : bruit réel >> bruit simulé en difficulté | EMNLP 2024 | Haut |
| nervaluate fournit des métriques plus granulaires que seqeval | MantisAI | Moyen |

---

## 2. Méthodologie

### 2.1 Sources Consultées

| Source | Type | Année | Pertinence |
|--------|------|-------|------------|
| SemEval 2013 Task 9 | Tâche Partagée | 2013 | Définition des métriques |
| RockNER (EMNLP 2021) | Papier ACL | 2021 | Évaluation contradictoire |
| NoiseBench (EMNLP 2024) | Papier ACL | 2024 | Bruit réaliste |
| seqeval | Librairie | 2018+ | Implémentation standard |
| nervaluate | Librairie | 2020+ | Métriques étendues |
| David Batista Blog | Tutoriel | 2018 | Explication détaillée |

### 2.2 Critères de Recherche

- "adversarial NER evaluation benchmark methodology"
- "NER robustness testing framework seqeval entity level"
- "SemEval 2013 task 9 entity level metrics"
- "RockNER adversarial NER EMNLP methodology"
- "NoiseBench NER evaluation realistic noise"

---

## 3. Normes d'Évaluation au Niveau de l'Entité

### 3.1 SemEval 2013 Task 9 : Les 4 Modes d'Évaluation

**Source :** [Named-Entity evaluation metrics based on entity-level](https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/)

La norme SemEval 2013 définit **4 modes** d'évaluation :

| Mode | Frontière | Type | Description |
|------|-----------|------|-------------|
| **Strict** | Exact | Exact | Frontière ET type doivent correspondre |
| **Exact** | Exact | Ignoré | Seulement frontière exacte |
| **Partiel** | Chevauchement | Ignoré | Chevauchement partiel suffit |
| **Type** | Chevauchement | Exact | Chevauchement + type correct |

#### 3.1.1 Définition des Métriques de Base

| Métrique | Définition |
|----------|------------|
| **COR** (Correct) | Système et gold sont identiques |
| **INC** (Incorrect) | Système et gold ne correspondent pas |
| **PAR** (Partiel) | Système et gold ont un chevauchement partiel |
| **MIS** (Manquant) | Gold non capturé par le système (FN) |
| **SPU** (Fallacieux) | Système produit quelque chose non présent dans le gold (FP) |
| **POS** (Possible) | COR + INC + PAR + MIS = total gold |
| **ACT** (Actuel) | COR + INC + PAR + SPU = total système |

#### 3.1.2 Formules de Calcul

**Pour les modes exacts (strict, exact) :**
```
Précision = COR / ACT
Rappel = COR / POS
F1 = 2 * (P * R) / (P + R)
```

**Pour les modes partiels (partiel, type) :**
```
Précision = (COR + 0.5 × PAR) / ACT
Rappel = (COR + 0.5 × PAR) / POS
F1 = 2 * (P * R) / (P + R)
```

### 3.2 seqeval : Implémentation Standard

**Source :** [seqeval GitHub](https://github.com/chakki-works/seqeval)

seqeval est le framework standard pour l'évaluation de l'étiquetage de séquences, validé contre le script Perl `conlleval` de CoNLL-2000.

#### Caractéristiques

| Fonctionnalité | Description |
|----------------|-------------|
| Format | CoNLL (tags BIO/BIOES) |
| Métriques | Précision, Rappel, F1 par type et global |
| Mode par défaut | Simule conlleval (indulgent avec B/I) |
| Mode strict | Seulement correspondances exactes |

#### Utilisation Correcte

```python
from seqeval.metrics import classification_report, f1_score
from seqeval.scheme import IOB2

# Mode strict (recommandé pour évaluation rigoureuse)
f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
report = classification_report(y_true, y_pred, mode='strict', scheme=IOB2)
```

**IMPORTANT :** Le mode par défaut de seqeval est indulgent. Pour une évaluation rigoureuse, utiliser `mode='strict'`.

### 3.3 nervaluate : Métriques Étendues

**Source :** [nervaluate GitHub](https://github.com/MantisAI/nervaluate)

nervaluate implémente entièrement les 4 modes de SemEval 2013.

#### Avantages sur seqeval

| Aspect | seqeval | nervaluate |
|--------|---------|------------|
| Modes | 2 (défaut, strict) | 4 (strict, exact, partiel, type) |
| Granularité | Par type d'entité | Par type + par scénario |
| Métriques | P/R/F1 | P/R/F1 + COR/INC/PAR/MIS/SPU |

#### Utilisation

```python
from nervaluate import Evaluator

evaluator = Evaluator(true_labels, pred_labels, tags=['PER', 'ORG', 'LOC'])
results, results_per_tag = evaluator.evaluate()

# Accéder au mode strict
strict_f1 = results['strict']['f1']

# Accéder aux métriques détaillées
cor = results['strict']['correct']
inc = results['strict']['incorrect']
par = results['partial']['partial']
```

---

## 4. Évaluation Contradictoire : Normes Académiques

### 4.1 RockNER (EMNLP 2021)

**Source :** [RockNER - ACL Anthology](https://aclanthology.org/2021.emnlp-main.302/)

RockNER propose un framework systématique pour créer des exemples contradictoires naturels.

#### Taxonomie des Perturbations

| Niveau | Méthode | Description |
|--------|---------|-------------|
| **Niveau entité** | Remplacement Wikidata | Substituer entités par d'autres de la même classe sémantique |
| **Niveau contexte** | BERT MLM | Générer substitutions de mots avec LM |
| **Combiné** | Les deux | Appliquer les deux pour une adversarialité maximale |

#### Benchmark OntoRock

- Dérivé de OntoNotes
- Applique des perturbations systématiques
- Mesure la dégradation du F1

#### Découverte Clé

> "Even the best model has a significant performance drop... models seem to memorize in-domain entity patterns instead of reasoning from the context."

### 4.2 NoiseBench (EMNLP 2024)

**Source :** [NoiseBench - ACL Anthology](https://aclanthology.org/2024.emnlp-main.1011/)

NoiseBench démontre que le bruit simulé est **significativement plus facile** que le bruit réel.

#### Types de Bruit Réel

| Type | Source | Description |
|------|--------|-------------|
| Erreurs d'experts | Annotateurs experts | Erreurs de fatigue, interprétation |
| Crowdsourcing | Amazon Turk, etc. | Erreurs de non-experts |
| Annotation automatique | Regex, heuristiques | Erreurs systématiques |
| Erreurs LLM | GPT, etc. | Hallucinations, incohérences |

#### Découverte Clé

> "Real noise is significantly more challenging than simulated noise, and current state-of-the-art models for noise-robust learning fall far short of their theoretically achievable upper bound."

### 4.3 Taxonomie des Perturbations pour NER

Basé sur la littérature, les perturbations contradictoires sont classées en :

| Catégorie | Exemples | Papiers |
|-----------|----------|---------|
| **Niveau caractère** | Coquilles, erreurs OCR, homoglyphes | RockNER, NoiseBench |
| **Niveau token** | Synonymes, inflexions | RockNER |
| **Niveau entité** | Remplacement par entités similaires | RockNER |
| **Niveau contexte** | Modifier le contexte environnant | RockNER |
| **Niveau format** | Espaces, ponctuation, casse | NoiseBench |
| **Niveau sémantique** | Négations, exemples fictifs | Custom |

---

## 5. Revue des Tests Actuels vs Normes

### 5.1 Tests Contradictoires Actuels

Notre script `test_ner_predictor_adversarial.py` a :

| Catégorie | Tests | Couverture |
|-----------|-------|------------|
| edge_case | 9 | Conditions limites |
| adversarial | 8 | Confusion sémantique |
| ocr_corruption | 5 | Erreurs OCR |
| unicode_evasion | 3 | Évasion Unicode |
| real_world | 10 | Documents réels |

### 5.2 Écarts Identifiés

| Écart | Norme | État Actuel | Sévérité |
|-------|-------|-------------|----------|
| Mode strict vs défaut | seqeval strict | Non spécifié | **CRITIQUE** |
| 4 modes SemEval | nervaluate | 1 seul mode | HAUT |
| Perturbations niveau entité | RockNER | Pas systématique | HAUT |
| Métriques COR/INC/PAR/MIS/SPU | SemEval 2013 | Non rapportées | MOYEN |
| Bruit réel vs simulé | NoiseBench | Simulé seulement | MOYEN |
| Perturbations niveau contexte | RockNER | Partiel | MOYEN |

### 5.3 Métriques Actuelles vs Requises

| Métrique | Actuel | Requis | Écart |
|----------|--------|--------|-------|
| F1 global | ✅ | ✅ | OK |
| Précision/Rappel | ✅ | ✅ | OK |
| F1 par type d'entité | ❌ | ✅ | **MANQUANT** |
| Mode strict | ❓ | ✅ | **VÉRIFIER** |
| COR/INC/PAR/MIS/SPU | ❌ | ✅ | **MANQUANT** |
| 4 modes SemEval | ❌ | ✅ | **MANQUANT** |

---

## 6. Recommandations d'Amélioration

### 6.1 Priorité CRITIQUE

1. **Vérifier le mode strict dans seqeval**
   ```python
   # Changer de :
   f1 = f1_score(y_true, y_pred)
   # À :
   f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
   ```

2. **Rapporter les métriques par type d'entité**
   ```python
   report = classification_report(y_true, y_pred, mode='strict')
   ```

### 6.2 Priorité HAUTE

3. **Implémenter les 4 modes de SemEval**
   - Utiliser nervaluate au lieu de (ou en plus de) seqeval
   - Rapporter strict, exact, partiel, type

4. **Ajouter perturbations niveau entité (style RockNER)**
   - Remplacer noms par d'autres noms espagnols
   - Remplacer DNIs par d'autres DNIs valides
   - Garder le contexte, changer l'entité

### 6.3 Priorité MOYENNE

5. **Rapporter COR/INC/PAR/MIS/SPU**
   - Permet une analyse plus fine des erreurs
   - Distingue entre erreurs de frontière et erreurs de type

6. **Ajouter perturbations niveau contexte**
   - Modifier verbes/adjectifs environnants
   - Utiliser BERT/spaCy pour substitutions naturelles

---

## 7. Checklist d'Évaluation Académique

### 7.1 Avant de Rapporter les Résultats

- [ ] Spécifier le mode d'évaluation (strict/défaut)
- [ ] Utiliser format CoNLL standard (BIO/BIOES)
- [ ] Rapporter F1, Précision, Rappel
- [ ] Rapporter métriques par type d'entité
- [ ] Documenter version de seqeval/nervaluate utilisée
- [ ] Inclure intervalles de confiance si variance

### 7.2 Pour Évaluation Contradictoire

- [ ] Catégoriser perturbations (Caractère, Token, Entité, Contexte)
- [ ] Mesurer dégradation relative (F1_clean - F1_adversarial)
- [ ] Rapporter taux de réussite par catégorie de difficulté
- [ ] Inclure analyse d'erreurs avec exemples
- [ ] Comparer avec baseline (modèle non modifié)

### 7.3 Pour Publication/Documentation

- [ ] Décrire méthodologie reproductible
- [ ] Publier dataset de test (ou générateur)
- [ ] Rapporter temps d'exécution
- [ ] Inclure analyse statistique si applicable

---

## 8. Conclusions

### 8.1 Actions Immédiates

1. **Revoir script contradictoire** pour vérifier mode strict
2. **Ajouter nervaluate** pour métriques complètes
3. **Réorganiser les tests** selon taxonomie RockNER

### 8.2 Impact sur les Résultats Actuels

Les résultats actuels (F1=0.784, 54.3% taux de réussite) pourraient changer si :
- Le mode n'était pas strict (résultats seraient plus bas en strict)
- Les métriques par type révèlent des faiblesses spécifiques
- Les 4 modes montrent un comportement différent en frontière vs type

---

## 9. Références

### Papiers Académiques

1. **RockNER: A Simple Method to Create Adversarial Examples for Evaluating the Robustness of Named Entity Recognition Models**
   - Lin et al., EMNLP 2021
   - URL: https://aclanthology.org/2021.emnlp-main.302/

2. **NoiseBench: Benchmarking the Impact of Real Label Noise on Named Entity Recognition**
   - Merdjanovska et al., EMNLP 2024
   - URL: https://aclanthology.org/2024.emnlp-main.1011/

3. **SemEval-2013 Task 9: Extraction of Drug-Drug Interactions from Biomedical Texts**
   - Segura-Bedmar et al., SemEval 2013
   - Définition des métriques au niveau de l'entité

### Outils et Librairies

4. **seqeval**
   - URL: https://github.com/chakki-works/seqeval

5. **nervaluate**
   - URL: https://github.com/MantisAI/nervaluate

6. **Named-Entity Evaluation Metrics Based on Entity-Level**
   - David Batista, 2018
   - URL: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Temps de recherche :** 45 min
**Généré par :** AlexAlves87
**Date :** 2026-01-28
