# Recherche : Lacunes du Pipeline Hybride NER-PII

**Date :** 30-01-2026
**Auteur :** AlexAlves87
**Objectif :** Analyser les lacunes critiques du pipeline hybride en se basant sur la littérature académique 2024-2026
**Version :** 2.0.0 (réécrit avec des fondements académiques)

---

## 1. Résumé Exécutif

Cinq lacunes ont été identifiées dans le pipeline hybride NER-PII de ContextSafe. Pour chaque lacune, une revue de la littérature académique a été menée dans des sources de premier plan (ACL, EMNLP, COLING, NAACL, TACL, Nature Scientific Reports, Springer, arXiv). Les recommandations proposées sont basées sur des preuves publiées, et non sur l'intuition.

| Lacune | Priorité | Papiers Revus | Recommandation Principale |
|--------|----------|---------------|---------------------------|
| Stratégie de Fusion | **HAUTE** | 7 | Pipeline 3 phases (RECAP) + priorité par type |
| Calibrage Confiance | **HAUTE** | 5 | Prédiction Conforme + BRB pour regex |
| Benchmark Comparatif | **MOYENNE** | 3 | nervaluate (SemEval'13) avec correspondance partielle |
| Latence/Mémoire | **MOYENNE** | 4 | ONNX Runtime + Quantification INT8 |
| Gazetteers | **BASSE** | 5 | Intégration style GAIN comme post-filtre |

---

## 2. Littérature Revue

| Papier/Système | Lieu/Source | Année | Découverte Pertinente |
|----------------|-------------|-------|-----------------------|
| RECAP: Hybrid PII Detection | arXiv 2510.07551 | 2025 | Pipeline 3 phases : détection → désambiguïsation multi-label → consolidation spans |
| Hybrid rule-based NLP + ML for PII (Mishra et al.) | Nature Scientific Reports | 2025 | F1 0.911 sur docs financiers, fusion chevauchements par min(start)/max(end) |
| Conformal Prediction for NER | arXiv 2601.16999 | 2026 | Ensembles de prédiction avec garanties de couverture ≥95%, calibrage stratifié |
| JCLB: Contrastive Learning + BRB | Springer Cybersecurity | 2024 | Belief Rule Base assigne confiance apprise aux regex, D-CMA-ES optimise paramètres |
| CMiNER | Expert Systems with Applications | 2025 | Estimateurs de confiance au niveau entité pour données bruitées |
| B2NER | COLING 2025 | 2025 | Benchmark NER unifié, 54 datasets, adaptateurs LoRA ≤50MB, surpasse GPT-4 |
| nervaluate (SemEval'13 Task 9) | GitHub/MantisAI | 2024 | Métriques COR/INC/PAR/MIS/SPU avec correspondance partielle |
| T2-NER | TACL | 2023 | Framework 2 étapes basé sur spans pour entités chevauchantes et discontinues |
| GNNer | ACL SRW 2022 | 2022 | Graph Neural Networks pour réduire les spans chevauchants |
| GAIN: Gazetteer-Adapted Integration | SemEval-2022 | 2022 | Divergence KL pour adapter réseau gazetteer au modèle de langue, 1er dans 3 tracks |
| Presidio | Microsoft Open Source | 2025 | `_remove_duplicates` : confiance la plus élevée gagne, inclusion → span plus grand |
| Soft Gazetteers | ACL 2020 | 2020 | Liaison d'entités translingue pour gazetteers dans ressources limitées |
| SPLR (span-based nested NER) | J. Supercomputing | 2025 | F1 87.5 sur ACE2005 avec Fonction de Connaissance Préalable |
| HuggingFace Optimum + ONNX | MarkTechPost/HuggingFace | 2025 | Benchmark PyTorch vs ONNX Runtime vs quantifié INT8 |
| PyDeID | PHI De-identification | 2025 | regex + spaCy NER, F1 87.9% sur notes cliniques, 0.48s/note |

---

## 3. Lacune 1 : Stratégie de Fusion (HAUTE)

### 3.1 Problème

Quand le transformeur NER et Regex détectent la même entité avec des limites ou types différents, lequel préférer ?

```
Texte: "Don José García avec DNI 12 345 678 Z"

NER détecte :   "José García avec DNI 12 345 678" (PERSON étendu, partiel)
Regex détecte : "12 345 678 Z" (DNI_NIE, complet)
```

### 3.2 État de l'Art

#### 3.2.1 RECAP Framework (arXiv 2510.07551, 2025)

Le framework le plus récent et complet pour la fusion PII hybride implémente **trois phases** :

1.  **Phase I - Détection de base :** Regex pour PII structuré (IDs, téléphones) + LLM pour non-structuré (noms, adresses). Produit multi-labels, chevauchements et faux positifs.

2.  **Phase II - Désambiguïsation Multi-label :** Pour entités avec multiples labels, le texte, span et labels candidats sont passés à un LLM avec prompt contextuel qui sélectionne le label correct.

3.  **Phase III - Consolidation :** Deux filtres :
    *   **Résolution de chevauchement déterministe :** Entités de priorité inférieure complètement contenues dans spans plus longs sont supprimées.
    *   **Filtrage contextuel de faux positifs :** Séquences numériques courtes sont vérifiées avec contexte de la phrase environnante.

**Résultat :** F1 moyen 0.657 sur 13 locales, surpassant NER pur (0.360) de 82% et zero-shot LLM (0.558) de 17%.

#### 3.2.2 Microsoft Presidio (2025)

Presidio implémente `__remove_duplicates()` avec des règles simples :
*   **Score de confiance le plus élevé gagne** parmi détections chevauchantes
*   **Inclusion :** Si une PII est contenue dans une autre, le **texte le plus long** est utilisé
*   **Intersection partielle :** Les deux sont retournés concaténés
*   Pas de priorité par type, seulement par score

#### 3.2.3 Mishra et al. (Nature Scientific Reports, 2025)

Pour documents financiers, fusion de chevauchements :
*   `start = min(start1, start2)`
*   `end = max(end1, end2)`
*   Le chevauchement est fusionné en une seule entité consolidée

**Limitation :** Ne distingue pas les types — inutile quand NER détecte PERSON et Regex détecte DNI dans le même span.

#### 3.2.4 T2-NER (TACL, 2023)

Framework 2 étapes basé sur spans :
1.  Extraire tous les spans d'entité (chevauchants et plats)
2.  Classifier paires de spans pour résoudre discontinuités

**Aperçu applicable :** Séparer détection de spans de leur classification permet de gérer les chevauchements de façon modulaire.

#### 3.2.5 GNNer (ACL Student Research Workshop, 2022)

Utilise Graph Neural Networks pour réduire spans chevauchants dans NER basé sur spans. Les spans candidats sont nœuds dans un graphe, et GNN apprend à supprimer ceux qui se chevauchent.

**Aperçu applicable :** Le chevauchement n'est pas toujours une erreur — entités imbriquées (nom dans adresse) sont légitimes.

### 3.3 Implémentation Actuelle de ContextSafe

Fichier : `scripts/inference/ner_predictor.py`, méthode `_merge_regex_detections()`

```python
# Stratégie actuelle (lignes 430-443):
for ner_ent in ner_entities:
    replaced = False
    for match in regex_matches:
        if overlaps(match, ner_ent):
            if regex_len > ner_len * 1.2:  # Regex 20% plus long
                replaced = True
                break
    if not replaced:
        ner_to_keep.append(ner_ent)
```

**Règle actuelle :** Si regex est ≥20% plus long que NER et il y a chevauchement → préférer regex.

### 3.4 Analyse Comparative

| Système | Stratégie | Gère Imbriqué | Utilise Type | Utilise Confiance |
|---------|-----------|---------------|--------------|-------------------|
| RECAP | 3 phases + LLM | ✅ | ✅ | Implicite |
| Presidio | Score le plus élevé | ❌ | ❌ | ✅ |
| Mishra et al. | fusion min/max | ❌ | ❌ | ❌ |
| ContextSafe actuel | Regex plus long gagne | ❌ | ❌ | ❌ |
| **Proposé** | **Priorité type + validation** | **✅** | **✅** | **✅** |

### 3.5 Recommandation Basée sur Preuves

Inspiré par RECAP (3 phases) mais sans dépendre de LLM (notre exigence est inférence CPU sans LLM), nous proposons :

**Phase 1 : Détection Indépendante**
*   Transformeur NER détecte entités sémantiques (PERSON, ORGANIZATION, LOCATION)
*   Regex détecte entités structurelles (DNI, IBAN, PHONE, DATE)

**Phase 2 : Résolution de Chevauchements par Priorité de Type**

Basé sur preuves RECAP (regex excelle dans PII structuré, NER dans sémantique) :

```python
MERGE_PRIORITY = {
    # Type → (priorité, source_préférée)
    # Regex avec checksum = confiance maximale (preuve : Mishra et al. 2025)
    "DNI_NIE": (10, "regex"),      # Checksum vérifiable
    "IBAN": (10, "regex"),         # Checksum vérifiable
    "NSS": (10, "regex"),          # Checksum vérifiable
    "PHONE": (8, "regex"),         # Format bien défini
    "POSTAL_CODE": (8, "regex"),   # 5 chiffres exacts
    "LICENSE_PLATE": (8, "regex"), # Format bien défini
    # NER excelle dans entités sémantiques (RECAP, PyDeID)
    "DATE": (6, "any"),            # Les deux valides
    "PERSON": (4, "ner"),          # NER meilleur avec contexte
    "ORGANIZATION": (4, "ner"),    # NER meilleur avec contexte
    "LOCATION": (4, "ner"),        # NER meilleur avec contexte
    "ADDRESS": (4, "ner"),         # NER meilleur avec contexte
}
```

**Phase 3 : Consolidation**
*   Entités **contenues** de types différents : garder les deux (imbriqué légitime, comme dans GNNer)
*   Entités **contenues** de même type : préférer la plus spécifique (source préférée)
*   Chevauchement **partiel** : préférer type de priorité plus élevée
*   Pas de chevauchement : garder les deux

| Situation | Règle | Preuve |
|-----------|-------|--------|
| Pas de chevauchement | Garder les deux | Standard |
| Chevauchement, types diff. | Priorité plus élevée gagne | RECAP Phase III |
| Inclusion, types diff. | Garder les deux (imbriqué) | GNNer, T2-NER |
| Inclusion, même type | Source préférée selon tableau | Presidio (span plus grand) |
| Chevauchement partiel, même type | Confiance plus élevée gagne | Presidio |

---

## 4. Lacune 2 : Calibrage de Confiance (HAUTE)

### 4.1 Problème

Regex retourne confiance fixe (0.95), NER retourne probabilité softmax. Elles ne sont pas directement comparables.

### 4.2 État de l'Art

#### 4.2.1 Prédiction Conforme pour NER (arXiv 2601.16999, Janvier 2026)

**Papier le plus récent et pertinent.** Introduit framework pour produire **ensembles de prédiction** avec garanties de couverture :

*   Donné niveau de confiance `1-α`, génère ensembles de prédiction garantis de contenir l'étiquette correcte
*   Utilise **scores de non-conformité** :
    *   `nc1` : `1 - P̂(y|x)` — basé sur probabilité, pénalise basse confiance
    *   `nc2` : probabilité cumulative dans séquences classées
    *   `nc3` : basé sur rang, produit ensembles de taille fixe

**Découvertes Clés :**
*   `nc1` surpasse substantiellement `nc2` (qui produit ensembles "extrêmement grands")
*   **Calibrage stratifié par longueur** corrige mauvais calibrage systématique dans longues séquences
*   **Calibrage par langue** améliore couverture (Anglais : 93.82% → 96.24% après stratification)
*   Correction de Šidák pour multiples entités : confiance par entité = `(1-α)^(1/s)` pour `s` entités

**Applicabilité à ContextSafe :** Le calibrage stratifié par longueur est directement applicable. Textes longs (contrats) peuvent avoir scores systématiquement différents de textes courts.

#### 4.2.2 JCLB : Belief Rule Base (Springer Cybersecurity, 2024)

Introduit une approche pour **assigner confiance aux règles regex** de manière apprise :

*   Règles regex sont formalisées comme une **Belief Rule Base (BRB)**
*   Chaque règle a **degrés de croyance** optimisés par D-CMA-ES
*   La BRB filtre catégories d'entité et évalue leur exactitude simultanément
*   Paramètres BRB sont optimisés contre données d'entraînement

**Aperçu clé :** Les règles regex NE devraient PAS avoir confiance fixe. Leur confiance doit être apprise/calibrée contre données réelles.

#### 4.2.3 CMiNER (Expert Systems with Applications, 2025)

Conçoit **estimateurs de confiance au niveau entité** qui :
*   Évaluent qualité initiale de datasets bruités
*   Assistent durant l'entraînement en ajustant poids

**Aperçu applicable :** La confiance au niveau entité (pas token) est plus utile pour décisions de fusion.

#### 4.2.4 Conf-MPU (Zhou et al., 2022)

Classification binaire niveau token pour prédire probabilité de chaque token étant une entité, puis utilise scores de confiance pour estimation de risque.

**Aperçu applicable :** Séparer "est-ce une entité ?" de "quel type ?" permet de calibrer en deux étapes.

### 4.3 Implémentation Actuelle de ContextSafe

```python
# Modèles Regex (spanish_id_patterns.py):
RegexMatch(..., confidence=0.95)  # Valeur fixe codée en dur

# Modèle NER :
confidence = softmax(logits).max()  # Probabilité réelle [0.5-0.99]

# Ajustement par checksum (ner_predictor.py, lignes 473-485):
if is_valid:
    final_confidence = min(match.confidence * 1.1, 0.99)
elif checksum_conf < 0.5:
    final_confidence = match.confidence * 0.5
```

### 4.4 Analyse du Problème

| Source | Confiance | Calibrée | Problème |
|--------|-----------|----------|----------|
| NER softmax | 0.50-0.99 | ✅ | Peut être mal calibrée pour textes longs (CP 2026) |
| Regex sans checksum | 0.95 fixe | ❌ | Sur-confiance dans correspondances ambiguës |
| Regex avec checksum valide | 0.99 | ⚠️ | Approprié pour IDs avec checksum |
| Regex avec checksum invalide | 0.475 | ✅ | Pénalité appropriée |

### 4.5 Recommandation Basée sur Preuves

#### Niveau 1 : Confiance de base différenciée par type (inspiré par JCLB/BRB)

Ne pas utiliser confiance fixe. Assigner **confiance de base** selon le niveau de validation disponible :

```python
REGEX_BASE_CONFIDENCE = {
    # Avec checksum vérifiable (confiance maximale, Mishra et al. 2025)
    "DNI_NIE":  {"checksum_valid": 0.98, "checksum_invalid": 0.35, "format_only": 0.70},
    "IBAN":     {"checksum_valid": 0.99, "checksum_invalid": 0.30, "format_only": 0.65},
    "NSS":      {"checksum_valid": 0.95, "checksum_invalid": 0.35, "format_only": 0.65},

    # Sans checksum, avec format bien défini
    "PHONE":         {"with_prefix": 0.90, "without_prefix": 0.75},
    "POSTAL_CODE":   {"valid_province": 0.85, "format_only": 0.70},
    "LICENSE_PLATE": {"modern_format": 0.90, "old_format": 0.80},

    # Ambigu
    "DATE":  {"full_textual": 0.85, "partial": 0.60, "ambiguous": 0.50},
    "EMAIL": {"standard": 0.95},
}
```

**Justification :** JCLB a montré que confiance de règle devrait être apprise/différenciée, non fixe. Sans accès aux données d'entraînement pour optimiser BRB (comme D-CMA-ES dans JCLB), nous utilisons heuristiques basées sur niveau de validation disponible (checksum > format > correspondance simple).

#### Niveau 2 : Calibrage stratifié (inspiré par CP 2026)

Pour Transformeur NER, considérer calibrage par longueur de texte :
*   Textes courts (1-10 tokens) : seuil confiance minimal 0.60
*   Textes moyens (11-50 tokens) : seuil 0.50
*   Textes longs (51+ tokens) : seuil 0.45

**Justification :** Papier Prédiction Conforme (2026) a montré que textes longs ont couverture systématiquement différente. Stratifier par longueur corrige ce mauvais calibrage.

#### Niveau 3 : Seuil de confiance opérationnel

Basé sur RECAP et PyDeID :
*   **≥0.80 :** Anonymisation automatique
*   **0.50-0.79 :** Anonymisation avec drapeau "réviser"
*   **<0.50 :** Ne pas anonymiser, rapporter comme "douteux"

---

## 5. Lacune 3 : Benchmark Comparatif (MOYENNE)

### 5.1 État de l'Art en Évaluation NER

#### 5.1.1 Métriques : seqeval vs nervaluate

| Framework | Type | Correspondance Partielle | Niveau | Standard |
|-----------|------|--------------------------|--------|----------|
| **seqeval** | Strict niveau-entité | ❌ | Entité complète | Eval CoNLL |
| **nervaluate** | Multi-scénario | ✅ | COR/INC/PAR/MIS/SPU | SemEval'13 Tâche 9 |

**seqeval** (standard CoNLL) :
*   Précision, Rappel, F1 au niveau entité complète
*   Seulement correspondance exacte : type correct ET span complet
*   Micro/macro moyenne par type

**nervaluate** (SemEval'13 Tâche 9) :
*   4 scénarios : strict, exact, partiel, type
*   5 catégories : COR (correct), INC (type incorrect), PAR (span partiel), MIS (manqué), SPU (fallacieux)
*   Correspondance partielle : `Précision = (COR + 0.5 × PAR) / ACT`

**Recommandation :** Utiliser **les deux** métriques. seqeval pour comparabilité avec littérature (CoNLL), nervaluate pour analyse d'erreur plus fine.

#### 5.1.2 Benchmark B2NER (COLING 2025)

*   54 datasets, 400+ types d'entité, 6 langues
*   Benchmark unifié pour Open NER
*   Adaptateurs LoRA ≤50MB surpassent GPT-4 de 6.8-12.0 F1

**Applicabilité :** B2NER confirme que LoRA est viable pour NER spécialisé, mais nécessite données de qualité (54 datasets raffinés).

### 5.2 Données ContextSafe Disponibles

| Configuration | F1 Strict | Taux de Validation | Source |
|---------------|-----------|--------------------|--------|
| NER seul (legal_ner_v2 base) | 0.464 | 28.6% | Baseline |
| NER + Normaliseur | 0.492 | 34.3% | Cycle ML |
| NER + Regex | 0.543 | 45.7% | Cycle ML |
| **Pipeline complet (5 elem)** | **0.788** | **60.0%** | Cycle ML |
| LoRA fine-tuning pur | 0.016 | 5.7% | Exp. 2026-02-04 |
| GLiNER zero-shot | 0.325 | 11.4% | Exp. 2026-02-04 |

### 5.3 Benchmark En Attente

| Test | Métrique | État |
|------|----------|------|
| Évaluer avec nervaluate (match partiel) | COR/INC/PAR/MIS/SPU | En attente |
| Regex seul (sans NER) | F1 strict + partiel | En attente |
| NER + Checksum (sans modèles regex) | F1 strict + partiel | En attente |
| Comparaison ventilation type-entité | F1 par type | En attente |

### 5.4 Recommandation

Créer script `scripts/evaluate/benchmark_nervaluate.py` qui :
1.  Exécute pipeline complet contre ensemble de test adversarial
2.  Rapporte métriques seqeval (strict, pour comparabilité)
3.  Rapporte métriques nervaluate (4 scénarios, pour analyse d'erreur)
4.  Ventile par type d'entité
5.  Compare ablations (NER seul, Regex seul, Hybride)

---

## 6. Lacune 4 : Latence/Mémoire (MOYENNE)

### 6.1 Objectif

| Métrique | Cible | Justification |
|----------|-------|---------------|
| Latence | <500ms par page A4 (~600 tokens) | UX réactive |
| Mémoire | <2GB modèle en RAM | Déploiement sur 16GB |
| Débit | >10 pages/seconde (batch) | Traitement massif |

### 6.2 État de l'Art en Optimisation d'Inférence

#### 6.2.1 ONNX Runtime + Quantification (HuggingFace Optimum, 2025)

HuggingFace Optimum permet :
*   Export vers ONNX
*   Optimisation de graphe (fusion opérateurs, élimination nœuds redondants)
*   Quantification INT8 (dynamique ou statique)
*   Benchmarking intégré : PyTorch vs torch.compile vs ONNX vs ONNX quantifié

**Résultats rapportés :**
*   Optimisé TensorRT : jusqu'à 432 inférences/seconde (ResNet-50, pas NER)
*   ONNX Runtime : accélération typique 2-4x sur PyTorch vanilla sur CPU

#### 6.2.2 PyDeID (2025)

Système hybride regex + spaCy NER pour dé-identification :
*   **0.48 secondes/note** vs 6.38 secondes/note du système de base
*   Facteur accélération 13x avec regex optimisé + NER
*   F1 87.9% avec le pipeline rapide

**Applicabilité directe :** PyDeID démontre qu'un pipeline hybride regex+NER peut traiter 1 document en <0.5s.

#### 6.2.3 Pipeline d'Optimisation Transformeur

```
PyTorch FP32 → Export ONNX → Optimisation Graphe → Quantification INT8
    baseline        2x             2-3x                 3-4x
```

### 6.3 Estimation Théorique pour ContextSafe

| Composant | CPU (PyTorch) | CPU (ONNX INT8) | Mémoire |
|-----------|---------------|-----------------|---------|
| TextNormalizer | <1ms | <1ms | ~0 |
| NER (RoBERTa-BNE ~125M) | ~200-400ms | ~50-100ms | ~500MB → ~200MB |
| Validateurs Checksum | <1ms | <1ms | ~0 |
| Modèles Regex | <5ms | <5ms | ~0 |
| Modèles Date | <2ms | <2ms | ~0 |
| Raffinement Limites | <1ms | <1ms | ~0 |
| **Total** | **~210-410ms** | **~60-110ms** | **~500MB → ~200MB** |

**Conclusion :** Avec ONNX INT8, devrait atteindre <500ms/page avec large marge.

### 6.4 Recommandation

1.  **D'abord mesurer** latence actuelle avec PyTorch (script `benchmark_latency.py`)
2.  **Si satisfait** <500ms sur CPU : documenter et différer optimisation ONNX
3.  **Si échec** : export ONNX + quantification INT8 (prioriser)
4.  **Documenter** processus pour réplicabilité dans autres langues

---

## 7. Lacune 5 : Gazetteers (BASSE)

### 7.1 État de l'Art

#### 7.1.1 GAIN: Gazetteer-Adapted Integration Network (SemEval-2022)

*   **Adaptation divergence KL :** Réseau Gazetteer s'adapte au modèle de langue minimisant divergence KL
*   **2 étapes :** D'abord adapter gazetteer au modèle, puis entraîner NER supervisé
*   **Résultat :** 1er dans 3 tracks (Chinois, Code-mixte, Bangla), 2e dans 10 tracks
*   **Aperçu :** Gazetteers sont plus utiles quand intégrés comme fonctionnalité additionnelle, pas comme recherche directe

#### 7.1.2 Gazetteer-Enhanced Attentive Neural Networks (EMNLP 2019)

*   Réseau auxiliaire encodant "régularité de nom" utilisant seulement gazetteers
*   Incorporé dans NER principal pour meilleure reconnaissance
*   **Réduit exigences données d'entraînement** significativement

#### 7.1.3 Soft Gazetteers pour NER Ressources Limitées (ACL 2020)

*   Dans langues sans gazetteers exhaustifs, utiliser liaison d'entités translingue
*   Wikipedia comme source de connaissance
*   Expérimenté dans 4 langues ressources limitées

#### 7.1.4 Réduction Correspondance Fallacieuse

*   Gazetteers bruts génèrent **beaucoup de faux positifs** (correspondance fallacieuse)
*   Filtrer par "popularité entité" améliore F1 de +3.70%
*   **Gazetteers Propres > Gazetteers Complets**

### 7.2 Gazetteers Disponibles dans ContextSafe

| Gazetteer | Enregistrements | Source | Dans Pipeline |
|-----------|-----------------|--------|---------------|
| Noms de famille | 27,251 | INE | ❌ |
| Prénoms hommes | 550 | INE | ❌ |
| Prénoms femmes | 550 | INE | ❌ |
| Noms archaïques | 6,010 | Généré | ❌ |
| Municipalités | 8,115 | INE | ❌ |
| Codes postaux | 11,051 | INE | ❌ |

### 7.3 Recommandation Basée sur Preuves

**Ne pas intégrer gazetteers dans le pipeline central** pour les raisons suivantes basées sur littérature :

1.  **Correspondance fallacieuse** (EMNLP 2019) : Sans filtrage de popularité, les gazetteers génèrent faux positifs
2.  **Pipeline fonctionne déjà** (F1 0.788) : Bénéfice marginal des gazetteers est faible
3.  **Complexité de réplicabilité** : Gazetteers sont spécifiques à la langue, chaque langue a besoin de sources différentes

**Usage recommandé comme post-filtre :**
*   **Validation de nom :** Si NER détecte PERSON, vérifier si prénom/nom est dans gazetteer → booster confiance +0.05
*   **Validation Code Postal :** Si regex détecte POSTAL_CODE 28001, vérifier si correspond à municipalité réelle → booster confiance +0.10
*   **NE PAS utiliser pour détection :** Ne pas chercher noms gazetteer directement dans texte (risque de correspondance fallacieuse)

---

## 8. Plan d'Action

### 8.1 Actions Immédiates (Haute Priorité)

| Action | Base Académique | Fichier |
|--------|-----------------|---------|
| Implémenter stratégie fusion 3 phases | RECAP (2025) | `ner_predictor.py` |
| Supprimer confiance fixe 0.95 dans regex | JCLB/BRB (2024) | `spanish_id_patterns.py` |
| Ajouter tableau priorité par type | RECAP, Presidio | `ner_predictor.py` |

### 8.2 Actions d'Amélioration (Moyenne Priorité)

| Action | Base Académique | Fichier |
|--------|-----------------|---------|
| Évaluer avec nervaluate (match partiel) | SemEval'13 Tâche 9 | `benchmark_nervaluate.py` |
| Créer benchmark latence | PyDeID (2025) | `benchmark_latency.py` |
| Documenter calibrage longueur | CP NER (2026) | Guide réplicabilité |

### 8.3 Actions Différées (Basse Priorité)

| Action | Base Académique | Fichier |
|--------|-----------------|---------|
| Gazetteers comme post-filtre | GAIN (2022) | `ner_predictor.py` |
| Export ONNX + INT8 | HuggingFace Optimum | `scripts/export/` |

---

## 9. Conclusions

### 9.1 Découvertes Clés de Recherche

1.  **Le pipeline hybride est SOTA pour PII** — RECAP (2025), PyDeID (2025), et Mishra et al. (2025) confirment que regex + NER surpasse chaque composant séparément.

2.  **La confiance regex ne devrait pas être fixe** — JCLB (2024) a démontré qu'assigner confiance apprise aux règles améliore significativement la performance.

3.  **Le calibrage par longueur de texte est important** — Prédiction Conforme (2026) a démontré mauvais calibrage systématique dans longues séquences.

4.  **nervaluate complète seqeval** — SemEval'13 Tâche 9 offre métriques de correspondance partielle qui capturent erreurs de limites que seqeval ignore.

5.  **ONNX INT8 est viable pour latence <500ms** — PyDeID a démontré <0.5s/document avec pipeline hybride optimisé.

### 9.2 État des Modèles Évalués

| Modèle | Évaluation | F1 Adversarial | État |
|--------|------------|----------------|------|
| **RoBERTa-BNE CAPITEL NER** (`legal_ner_v2`) | Pipeline complet 5 éléments | **0.788** | **ACTIF** |
| GLiNER-PII (zero-shot) | Évalué sur 35 tests adversariaux | 0.325 | Écarté (inférieur) |
| LoRA Legal-XLM-R-base (`lora_ner_v1`) | Évalué sur 35 tests adversariaux | 0.016 | Écarté (sur-apprentissage) |
| MEL (Modèle Juridique Espagnol) | Investigué | N/A (pas version NER) | Écarté |
| Legal-XLM-R-base (joelniklaus) | Investigué pour multilingue | N/A | En attente pour expansion future |

> **Note :** Le modèle de base du pipeline est `roberta-base-bne-capitel-ner` (RoBERTa-BNE, ~125M params, vocab 50,262),
> fine-tuned avec données synthétiques v3 (30% injection bruit). Ce n'est **PAS** XLM-RoBERTa.

### 9.3 Recommandations pour Réplicabilité

Pour répliquer dans d'autres langues, les adaptateurs sont :

| Composant | Espagne (ES) | France (FR) | Italie (IT) | Adaptation |
|-----------|--------------|-------------|-------------|------------|
| Modèle NER | RoBERTa-BNE CAPITEL | JuriBERT/CamemBERT | Legal-BERT-IT | Fine-tune NER par langue |
| NER Multilingue (alternative) | Legal-XLM-R | Legal-XLM-R | Legal-XLM-R | Modèle multilingue unique |
| Modèles Regex | DNI/NIE, IBAN ES | CNI, IBAN FR | CF, IBAN IT | Nouveau fichier regex |
| Validateurs Checksum | mod-23 (DNI) | mod-97 (IBAN) | Codice Fiscale | Nouveau validateur |
| Priorités Fusion | Tableau 3.5 | Même structure | Même structure | Ajuster types |
| Calibrage Confiance | Tableau 4.5 | Même structure | Même structure | Calibrer par type local |
| Gazetteers | INE | INSEE | ISTAT | Sources nationales |

---

**Généré par :** AlexAlves87
**Date :** 30-01-2026
**Version :** 2.0.0 — Réécrit avec recherche académique (v1.0 manquait de fondement)
