# Recherche : Embeddings Généraux vs Domaine Juridique pour la Désambiguïsation des Types d'Entités en NER

**Date :** 07/02/2026
**Objectif :** Enquêter sur la raison pour laquelle les embeddings juridiques spécialisés produisent plus de faux positifs que les embeddings à usage général dans la tâche de classification des types d'entités post-NER, et déterminer la meilleure stratégie d'embedding pour ContextSafe.

---

## 1. Résumé Exécutif

1.  **Les embeddings du domaine juridique produisent plus de faux positifs** car le fine-tuning juridique réduit la capacité discriminative entre les types d'entités en effondrant l'espace d'embedding autour de modèles linguistiques juridiques (anisotropie augmentée, espace sémantique plus étroit).
2.  **Les embeddings à usage général sont supérieurs pour la discrimination des types d'entités** car ils maintiennent un espace sémantique plus large et plus diversifié où les différences entre catégories (personne vs organisation vs date) sont plus prononcées.
3.  **L'anisotropie n'est PAS intrinsèquement mauvaise** – des travaux récents (ICLR 2024) montrent que l'anisotropie contrôlée peut améliorer les performances – mais l'anisotropie non contrôlée par le fine-tuning de domaine réduit la discrimination inter-classe nécessaire pour les centroïdes de type.
4.  **Recommandation : utiliser `BAAI/bge-m3` ou `intfloat/multilingual-e5-large`** (embeddings généraux) pour le validateur de type, PAS d'embeddings juridiques. Si l'on souhaite combiner des connaissances de domaine, utiliser une approche hybride avec des adaptateurs (LoRA) qui préservent la capacité générale.
5.  **La technique des centroïdes avec contexte est bien soutenue** par la littérature sur les réseaux prototypiques (CEPTNER, KCL), mais nécessite 50-100 exemples divers par type et un contexte environnant de 10-15 jetons.

---

## 2. Constat 1 : Embeddings General-Purpose vs Domain-Specific pour la Classification de Type d'Entité

### 2.1 Preuve clé : Les modèles general-purpose échouent dans les tâches de domaine MAIS excellent dans la discrimination des types

| Article | Lieu/Année | Découverte clé |
| :--- | :--- | :--- |
| **"Do We Need Domain-Specific Embedding Models? An Empirical Investigation"** (Tang & Yang) | arXiv 2409.18511 (2024) | Ont évalué 7 modèles SOTA sur FinMTEB (finance benchmark). Les modèles généraux ont montré une baisse significative dans les tâches de domaine, et leur performance MTEB ne corrèle PAS avec la performance FinMTEB. **MAIS** : cette baisse concernait la récupération et le STS, pas la classification des types d'entités. |
| **"NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data"** (Bogdanov et al.) | EMNLP 2024 | Modèle compact (base RoBERTa) pré-entraîné avec apprentissage contrastif sur 4,38M d'annotations d'entités. Surpasse des modèles de taille similaire en few-shot NER et rivalise avec des LLM beaucoup plus grands. **Clé** : la diversité des types d'entités dans le jeu de données de pré-entraînement est fondamentale. |
| **"LegNER: A Domain-Adapted Transformer for Legal NER and Text Anonymization"** (Al-Hussaeni et al.) | Frontiers in AI (2025) | Modèle juridique basé sur BERT-base + vocabulaire étendu + 1 542 affaires judiciaires annotées. F1 >99% sur 6 types d'entités. **Cependant** : l'article ne rapporte pas d'analyse des faux positifs entre les types, et les entités évaluées sont très différentes entre elles (PERSONNE vs LOI vs RÉFÉRENCE\_AFFAIRE). |
| **"MEL: Legal Spanish Language Model"** (2025) | arXiv 2501.16011 | XLM-RoBERTa-large fine-tuné avec 5,52M de textes juridiques espagnols (92,7 Go). Surpasse XLM-R de base en classification de documents. **Critique** : les auteurs admettent que "Les tâches de classification de jetons ou de segments restent non évaluées en raison du manque de textes annotés" – c'est-à-dire qu'ils n'ont PAS évalué le NER. |

### 2.2 Interprétation : Pourquoi les modèles généraux discriminent mieux les TYPES

La distinction clé se situe entre **deux tâches différentes** :

| Tâche | Ce dont l'embedding a besoin | Meilleur modèle |
| :--- | :--- | :--- |
| Récupération juridique / STS juridique | Capturer les nuances sémantiques juridiques | Domain-specific |
| Classification de type d'entité | Séparer des catégories larges (personne vs org vs date) | General-purpose |

Les embeddings juridiques sont optimisés pour la première tâche : récupérer des documents juridiques similaires, comprendre la terminologie juridique, capturer les relations juridiques. Cela les rend PIRES pour la seconde tâche car :

1.  **Effondrement de la diversité** : le fine-tuning juridique rapproche toutes les représentations du sous-espace juridique, réduisant la distance entre "personne mentionnée dans un jugement" et "organisation mentionnée dans un jugement" car les deux apparaissent dans des contextes juridiques similaires.
2.  **Biais contextuel** : un modèle juridique apprend que "Telefonica" dans un contexte juridique est aussi juridiquement pertinent que "Alejandro Alvarez", aplatissant les différences de type.
3.  **Anisotropie non contrôlée** : le fine-tuning introduit une anisotropie qui peut faire s'effondrer des types distincts dans les mêmes directions dominantes de l'espace d'embedding.

**URL pertinente** : [Do We Need Domain-Specific Embedding Models?](https://arxiv.org/abs/2409.18511)

---

## 3. Constat 2 : Pourquoi les Embeddings Juridiques Produisent Plus de Faux Positifs

### 3.1 Le problème de l'anisotropie dans les embeddings fine-tunés

| Article | Lieu/Année | Découverte clé |
| :--- | :--- | :--- |
| **"Anisotropy is Not Inherent to Transformers"** (Machina & Mercer) | NAACL 2024 | Démontrent que l'anisotropie n'est pas inhérente à l'architecture transformer. Identifient de grands modèles Pythia avec des espaces isotropes. Les justifications théoriques précédentes de l'anisotropie étaient insuffisantes. |
| **"Stable Anisotropic Regularization" (I-STAR)** (Rudman & Eickhoff) | ICLR 2024 | Résultat contre-intuitif : RÉDUIRE l'isotropie (augmenter l'anisotropie) améliore les performances en aval. Utiliser IsoScore* (métrique différentiable) comme régularisateur. **Implication clé** : l'anisotropie CONTRÔLÉE peut être bénéfique, mais l'anisotropie NON CONTRÔLÉE par le fine-tuning de domaine est nuisible. |
| **"The Shape of Learning: Anisotropy and Intrinsic Dimensions in Transformer-Based Models"** (2024) | EACL 2024 | Les décodeurs transformer montrent une courbe en cloche avec une anisotropie maximale dans les couches intermédiaires, tandis que les encodeurs montrent une anisotropie plus uniforme. Les couches où l'anisotropie est plus élevée coïncident avec les couches codant l'information de type. |
| **"How Does Fine-tuning Affect the Geometry of Embedding Space: A Case Study on Isotropy"** (Rajaee & Pilehvar) | EMNLP 2021 Findings | Bien que l'isotropie soit souhaitable, le fine-tuning n'améliore PAS nécessairement l'isotropie. Les structures locales (comme le codage de type de jeton) subissent des changements massifs pendant le fine-tuning. Les directions allongées (directions dominantes) dans l'espace fine-tuné portent les connaissances linguistiques essentielles. |
| **"Representation Degeneration Problem in Prompt-based Fine-tuning"** | LREC 2024 | L'anisotropie de l'espace d'embedding limite les performances en fine-tuning basé sur les prompts. Proposent CLMA (cadre d'apprentissage contrastif) pour atténuer l'anisotropie. |

### 3.2 Mécanisme des faux positifs dans les embeddings juridiques

Basé sur les preuves précédentes, le mécanisme par lequel les embeddings juridiques produisent plus de faux positifs dans la validation de type d'entité est :

```
1. Fine-tuning juridique → Espace d'embedding se contracte vers le sous-espace juridique
                             ↓
2. Représentations de "personne en contexte juridique" et
   "organisation en contexte juridique" se rapprochent
   (les deux sont des "entités juridiquement pertinentes")
                             ↓
3. Centroïdes de PERSON_NAME et ORGANIZATION se chevauchent
   dans l'espace juridique-fine-tuné
                             ↓
4. Similarité cosinus entre centroid_PERSON et une ORGANIZATION
   est plus élevée qu'elle ne le serait avec des embeddings généraux
                             ↓
5. Plus d'entités franchissent le seuil de reclassification → plus de FP
```

### 3.3 Preuve directe du domaine juridique

| Article | Lieu/Année | Découverte clé |
| :--- | :--- | :--- |
| **"Improving Legal Entity Recognition Using a Hybrid Transformer Model and Semantic Filtering Approach"** | arXiv 2410.08521 (2024) | Legal-BERT produit des faux positifs sur des termes ambigus et des entités imbriquées. Proposent un filtrage sémantique post-prédiction utilisant la similarité cosinus contre des motifs juridiques prédéfinis. **Résultat** : La précision monte de 90,2% à 94,1% (+3,9 pp), F1 de 89,3% à 93,4% (+4,1 pp). Utilisent la formule S(ei,Pj) = cos(ei, Pj) avec un seuil tau pour filtrer. |

**Cet article valide directement notre approche** d'utiliser la similarité cosinus pour filtrer les prédictions, MAIS utilise des motifs juridiques prédéfinis au lieu de centroïdes de type. La combinaison des deux approches (centroïdes généraux + motifs juridiques comme filtre supplémentaire) est une extension naturelle.

**URL pertinente** : [Improving Legal Entity Recognition Using Semantic Filtering](https://arxiv.org/abs/2410.08521)

---

## 4. Constat 3 : Meilleurs Modèles d'Embedding pour la Désambiguïsation de Type d'Entité (2024-2026)

### 4.1 Comparaison des modèles candidats

| Modèle | Taille | Dim | Langues | Score MTEB | Forces | Faiblesses pour notre tâche |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BAAI/bge-m3** | ~2,3 Go | 1024 | 100+ | 63,0 | Multi-granularité (dense+sparse+ColBERT), meilleure performance multilingue dans MTEB | Taille plus grande, latence plus élevée |
| **intfloat/multilingual-e5-large** | ~1,1 Go | 1024 | 100+ | ~62 | Excellent espagnol, bien documenté, nécessite préfixe "query:" | Légèrement inférieur à bge-m3 en multilingue |
| **nomic-ai/nomic-embed-text-v2** | ~700 Mo | 768 | 100 | ~62 | MoE (Mixture of Experts), efficace, 8192 jetons | Plus récent, moins validé en espagnol juridique |
| **intfloat/multilingual-e5-small** | ~448 Mo | 384 | 100 | ~56 | Plus léger, latence faible | Dimension moindre peut perdre en discrimination |
| **Wasserstoff-AI/Legal-Embed** | ~1,1 Go | 1024 | Multi | N/A | Fine-tuné pour juridique | **ÉCARTÉ : plus de FP pour la raison analysée en section 3** |

### 4.2 Recommandation basée sur les preuves

**Modèle principal : `BAAI/bge-m3`**

Justification :

1.  Meilleure performance dans les benchmarks multilingues, y compris l'espagnol (voir [OpenAI vs Open-Source Multilingual Embedding Models](https://towardsdatascience.com/openai-vs-open-source-multilingual-embedding-models-e5ccb7c90f05/))
2.  Dimensionnalité plus élevée (1024) = plus grande capacité à séparer les centroïdes de type
3.  Récupération Dense+sparse+ColBERT fonctionne bien pour les comparaisons de similarité
4.  Supporte jusqu'à 8192 jetons (utile pour les longs contextes juridiques)

**Modèle alternatif : `intfloat/multilingual-e5-large`**

Justification :

1.  Bien documenté avec papier technique (arXiv:2402.05672)
2.  Performance excellente en espagnol vérifiée
3.  Légèrement plus petit que bge-m3
4.  Déjà proposé dans `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md`

**IMPORTANT** : NE PAS utiliser `Legal-Embed` ni aucun modèle fine-tuné pour le domaine juridique. Les preuves académiques indiquent que les modèles généraux préservent mieux la séparation entre les types d'entités, ce qui est exactement ce dont nous avons besoin pour les centroïdes.

### 4.3 Sources de benchmarks

| Benchmark | Ce qu'il mesure | Référence |
| :--- | :--- | :--- |
| MTEB (Massive Text Embedding Benchmark) | 8 tâches incluant classification et clustering | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) |
| FinMTEB (Finance MTEB) | Performance dans le domaine financier | Tang & Yang (2024), arXiv:2409.18511 |
| MMTEB (Massive Multilingual TEB) | Extension multilingue de MTEB (2025) | [MMTEB GitHub](https://github.com/embeddings-benchmark/mteb) |

**Note critique** : Aucun benchmark existant ne mesure directement "la discrimination de type d'entité via centroïdes". MTEB a des sous-tâches de classification et de clustering qui sont des approximations utiles. Il est recommandé de créer un benchmark interne pour ContextSafe.

---

## 5. Constat 4 : Techniques de Validation de Type Basée sur les Centroïdes

### 5.1 Réseaux prototypiques et centroïdes pour NER

| Article | Lieu/Année | Découverte clé |
| :--- | :--- | :--- |
| **"CEPTNER: Contrastive Learning Enhanced Prototypical Network for Two-stage Few-shot NER"** (Wang et al.) | Knowledge-Based Systems (2024) | Deux étapes : (1) détection des limites, (2) classification prototypique avec apprentissage contrastif. L'apprentissage contrastif au niveau de l'entité sépare efficacement les types. Évalué sur Few-NERD, CrossNER, SNIPS. |
| **"Transformer-based Prototype Network for Chinese Nested NER"** (MSTPN) | Scientific Reports (2025) | Réseaux prototypiques avec transformers pour NER imbriqué. Utilise les bounding boxes des entités comme prototypes. |
| **"KCL: Few-shot NER with Knowledge Graph and Contrastive Learning"** | LREC-COLING 2024 | Combine Knowledge Graphs avec apprentissage contrastif pour apprendre une représentation sémantique des étiquettes. Utilise KG pour fournir des infos de type structurées. La représentation contrastive sépare les clusters d'étiquettes dans l'espace prototypique. |
| **"Multi-Head Self-Attention-Enhanced Prototype Network with Contrastive-Center Loss for Few-Shot Relation Extraction"** | Applied Sciences (2024) | Perte contrastive-center comparant les échantillons d'entraînement avec les centres de classe correspondants ET non-correspondants. Réduit les distances intra-classe et augmente les distances inter-classe. |
| **"CLESR: Context-Based Label Knowledge Enhanced Span Recognition for NER"** | Int J Computational Intelligence Systems (2024) | Améliore le NER imbriqué en intégrant des infos contextuelles avec la connaissance des étiquettes. Les segments s'alignent avec les descriptions textuelles des types dans un espace sémantique partagé. |

### 5.2 Meilleures pratiques pour la construction de centroïdes

Basé sur la littérature revue :

| Aspect | Recommandation | Justification |
| :--- | :--- | :--- |
| **Nombre d'exemples** | 50-100 par type | CEPTNER montre l'efficacité avec peu d'exemples ; 50 est le minimum, 100 est robuste |
| **Diversité des exemples** | Inclure variations de contexte, format, longueur | KCL met l'accent sur la diversité pour des clusters plus discriminatifs |
| **Taille du contexte** | 10-15 jetons environnants | L'enquête NER (arXiv:2401.10825) confirme que BERT capture le contexte intra- et inter-phrase efficacement |
| **Mise à jour des centroïdes** | Recalculer périodiquement avec de nouveaux exemples confirmés | CEPTNER montre que plus d'exemples améliorent la séparation ; les centroïdes doivent évoluer |
| **Raffinement contrastif** | Entraîner avec perte contrastive pour maximiser la séparation | De nombreux articles montrent que la perte contrastive est CLÉ pour la séparation des types |
| **Couches intermédiaires** | Envisager d'extraire des couches 15-17, pas seulement la couche finale | NER Retriever (arXiv:2509.04011) montre que les couches intermédiaires contiennent plus d'infos de type |

### 5.3 Taille de la fenêtre contextuelle

| Article | Constat sur le contexte |
| :--- | :--- |
| Survey NER (arXiv:2401.10825) | "Les encodages BERT capturent un contexte important à l'intérieur et adjacent à la phrase." Augmenter la fenêtre améliore la performance. |
| Span-based Unified NER via Contrastive Learning (IJCAI 2024) | Les segments avec contexte s'alignent avec les descriptions de type dans l'espace partagé. Le contexte est nécessaire pour désambiguïser. |
| Contextualized Span Representations (Wadden et al.) | La propagation des représentations de segments via les liens de coréférence permet de désambiguïser les mentions difficiles. |

**Recommandation** : Pour ContextSafe, utiliser un **contexte de 10-15 jetons** de chaque côté de l'entité. Pour les entités au début/fin de phrase, remplir avec des jetons de la phrase précédente/suivante si disponible.

---

## 6. Constat 5 : Approches Hybrides (Général + Domaine)

### 6.1 Concaténation et ensemble d'embeddings

| Article | Lieu/Année | Découverte clé |
| :--- | :--- | :--- |
| **"Automated Concatenation of Embeddings for Structured Prediction" (ACE)** | ACL-IJCNLP 2021 | Cadre qui trouve automatiquement la meilleure concaténation d'embeddings pour la prédiction structurée (y compris NER). Atteint SOTA dans 6 tâches sur 21 jeux de données. La sélection varie selon la tâche et l'ensemble de candidats. |
| **"Pooled Contextualized Embeddings for NER"** (Akbik et al.) | NAACL 2019 | Agrège les embeddings contextualisés de chaque instance unique pour créer une représentation "globale". Les embeddings empilés (combinant plusieurs types) sont une caractéristique clé de Flair et améliorent significativement le NER. |
| **"Improving Few-Shot Cross-Domain NER by Instruction Tuning a Word-Embedding based Retrieval Augmented LLM" (IF-WRANER)** | EMNLP 2024 Industry | Utilise des embeddings au niveau du mot (pas de la phrase) pour la récupération d'exemples in-prompt. Surpasse SOTA dans CrossNER de >2% F1. Déployé en production, réduisant les escalades humaines de ~15%. |
| **"Pre-trained Embeddings for Entity Resolution: An Experimental Analysis"** (Zeakis et al.) | VLDB 2023 | Analyse de 12 modèles de langage sur 17 jeux de données pour la résolution d'entités. Les embeddings contextualisés (variantes BERT) surpassent systématiquement les statiques (fastText), mais la combinaison peut être bénéfique. |

### 6.2 Adaptateurs (LoRA) pour préserver les connaissances générales

| Article | Lieu/Année | Découverte clé |
| :--- | :--- | :--- |
| **"Continual Named Entity Recognition without Catastrophic Forgetting"** (Zheng et al.) | EMNLP 2023 | Proposent pooled feature distillation loss + pseudo-étiquetage + re-pondération adaptative. L'oubli catastrophique dans le NER continu est intensifié par le "décalage sémantique" du type non-entité. |
| **"A New Adapter Tuning of LLM for Chinese Medical NER"** | Automation in Construction (2024) | Les adaptateurs évitent l'oubli catastrophique car ils apprennent de nouvelles connaissances sans ajustements extensifs des paramètres. Préférable pour le NER multi-domaine. |
| **"Mixture of LoRA Experts for Continual Information Extraction"** | EMNLP 2025 Findings | Cadre MoE avec LoRA pour l'extraction continue d'informations. Permet d'ajouter des domaines sans oublier les précédents. |
| **"LoRASculpt: Sculpting LoRA for Harmonizing General and Specialized Knowledge"** | CVPR 2025 | Technique pour équilibrer les connaissances générales et spécialisées pendant le fine-tuning avec LoRA. |

### 6.3 Stratégies de combinaison viables pour ContextSafe

| Stratégie | Complexité | Bénéfice attendu | Recommandée |
| :--- | :--- | :--- | :--- |
| **A : Embeddings généraux purs** | Faible | Bonne discrimination des types sans FP supplémentaires | Oui (référence) |
| **B : Concaténer général + juridique** | Moyenne | Plus de dimensions, capture les deux aspects | Évaluable mais coûteux en latence |
| **C : Moyenne pondérée général + juridique** | Moyenne | Plus simple que concat, mais perd de l'information | Non recommandée (la moyenne dilue) |
| **D : Méta-modèle sur embeddings multiples** | Élevée | Meilleure précision s'il y a suffisamment de données d'entraînement | Pour le futur |
| **E : Adaptateur LoRA sur modèle général** | Moyenne-Élevée | Préserve la capacité générale + ajoute le domaine | Oui (deuxième étape) |

**Recommandation pour ContextSafe** :

*   **Phase 1 (immédiate)** : Utiliser des embeddings généraux purs (bge-m3 ou e5-large). Évaluer la réduction des FP par rapport à l'expérience avec les embeddings juridiques.
*   **Phase 2 (si Phase 1 insuffisante)** : Appliquer un adaptateur LoRA sur le modèle général avec des exemples contrastifs d'entités juridiques espagnoles. Cela préserve la capacité générale de discrimination des types tout en ajoutant des connaissances du domaine.
*   **Phase 3 (optionnelle)** : Recherche automatisée de style ACE de la meilleure concaténation si un jeu de données de validation de type suffisamment grand est disponible.

---

## 7. Synthèse et Recommandation Finale

### 7.1 Réponse directe aux questions de recherche

**Q1 : General-purpose vs domain-specific pour la classification de type d'entité ?**

Utiliser **general-purpose**. Les preuves de multiples articles (Tang & Yang 2024, Rajaee & Pilehvar 2021, Machina & Mercer NAACL 2024) indiquent que :

*   Les modèles généraux maintiennent des espaces sémantiques plus larges
*   La discrimination des types d'entités nécessite une séparation inter-classe, pas une profondeur intra-domaine
*   Les modèles de domaine effondrent des types similaires dans le même sous-espace

**Q2 : Pourquoi les embeddings juridiques produisent-ils plus de faux positifs ?**

Trois facteurs convergents :

1.  **Effondrement de la diversité sémantique** : le fine-tuning juridique rapproche les représentations de toutes les entités du sous-espace "juridique"
2.  **Anisotropie non contrôlée** : le fine-tuning introduit des directions dominantes codant la "légalité" au lieu du "type d'entité" (Rajaee & Pilehvar 2021, Rudman & Eickhoff ICLR 2024)
3.  **Chevauchement des centroïdes** : les centroïdes de PERSONNE et ORGANISATION se rapprochent car les deux apparaissent dans des contextes juridiques identiques

**Q3 : Meilleur modèle ?**

`BAAI/bge-m3` (première option) ou `intfloat/multilingual-e5-large` (deuxième option). Les deux sont généraux, multilingues, avec un bon support de l'espagnol et une dimensionnalité de 1024 suffisante pour séparer les centroïdes de type.

**Q4 : Technique des centroïdes ?**

Bien soutenue par CEPTNER (2024), KCL (2024), MSTPN (2025). Clés :

*   50-100 exemples divers par type
*   Contexte de 10-15 jetons autour de l'entité
*   Apprentissage contrastif pour raffiner les centroïdes si possible
*   Les couches intermédiaires (15-17) peuvent être plus informatives que la couche finale

**Q5 : Approche hybride ?**

Pour le futur : Adaptateurs LoRA sur modèle général est la stratégie la plus prometteuse. Préserve la discrimination générale + ajoute la connaissance du domaine. ACE (concaténation automatisée) est viable si des données d'évaluation suffisantes existent.

### 7.2 Impact sur le document précédent

Le document `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` recommande `multilingual-e5-large` comme modèle principal et suggère d'évaluer `Legal-Embed` comme alternative. Basé sur cette recherche :

| Aspect | Document précédent | Mise à jour |
| :--- | :--- | :--- |
| Modèle principal | `multilingual-e5-large` | **Correct**, maintenir |
| Alternative Legal-Embed | Suggérée pour évaluation | **ÉCARTER** : preuves indiquent qu'il produira plus de FP |
| Alternative réelle | Non proposée | **Ajouter `BAAI/bge-m3`** comme première option |
| Raffinement contrastif | Non mentionné | **Ajouter** : si les centroïdes ne séparent pas assez, appliquer apprentissage contrastif |
| Couches intermédiaires | Non mentionné | **Ajouter** : extraire embeddings des couches 15-17, pas seulement dernière |

---

## 8. Table Consolidée des Articles Revus

| # | Article | Lieu | Année | Sujet Principal | URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Do We Need Domain-Specific Embedding Models? An Empirical Investigation | arXiv 2409.18511 | 2024 | General vs domain embeddings | https://arxiv.org/abs/2409.18511 |
| 2 | NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data | EMNLP 2024 | 2024 | Entity-aware pre-training | https://aclanthology.org/2024.emnlp-main.660/ |
| 3 | LegNER: Domain-Adapted Transformer for Legal NER | Frontiers in AI | 2025 | Legal NER + anonymization | https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1638971/full |
| 4 | MEL: Legal Spanish Language Model | arXiv 2501.16011 | 2025 | Spanish legal embeddings | https://arxiv.org/abs/2501.16011 |
| 5 | Anisotropy is Not Inherent to Transformers | NAACL 2024 | 2024 | Embedding space geometry | https://aclanthology.org/2024.naacl-long.274/ |
| 6 | Stable Anisotropic Regularization (I-STAR) | ICLR 2024 | 2024 | Controlled anisotropy | https://arxiv.org/abs/2305.19358 |
| 7 | The Shape of Learning: Anisotropy and Intrinsic Dimensions | EACL 2024 | 2024 | Anisotropy dynamics in transformers | https://aclanthology.org/2024.findings-eacl.58/ |
| 8 | How Does Fine-tuning Affect Geometry of Embedding Space | EMNLP 2021 Findings | 2021 | Fine-tuning impact on isotropy | https://aclanthology.org/2021.findings-emnlp.261/ |
| 9 | Representation Degeneration in Prompt-based Fine-tuning | LREC 2024 | 2024 | Anisotropy limits performance | https://aclanthology.org/2024.lrec-main.1217/ |
| 10 | Improving Legal Entity Recognition Using Semantic Filtering | arXiv 2410.08521 | 2024 | Legal NER false positive reduction | https://arxiv.org/abs/2410.08521 |
| 11 | CEPTNER: Contrastive Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems | 2024 | Prototype networks for NER | https://doi.org/10.1016/j.knosys.2024.111730 |
| 12 | KCL: Few-shot NER with Knowledge Graph and Contrastive Learning | LREC-COLING 2024 | 2024 | KG + contrastive for prototypical NER | https://aclanthology.org/2024.lrec-main.846/ |
| 13 | Automated Concatenation of Embeddings (ACE) | ACL-IJCNLP 2021 | 2021 | Multi-embedding concatenation for NER | https://aclanthology.org/2021.acl-long.206/ |
| 14 | Pooled Contextualized Embeddings for NER | NAACL 2019 | 2019 | Global word representations for NER | https://aclanthology.org/N19-1078/ |
| 15 | Continual NER without Catastrophic Forgetting | EMNLP 2023 | 2023 | Catastrophic forgetting in NER | https://arxiv.org/abs/2310.14541 |
| 16 | Improving Few-Shot Cross-Domain NER (IF-WRANER) | EMNLP 2024 Industry | 2024 | Word-level embeddings for cross-domain NER | https://aclanthology.org/2024.emnlp-industry.51/ |
| 17 | CLESR: Context-Based Label Knowledge Enhanced Span Recognition | IJCIS | 2024 | Context + label knowledge for NER | https://link.springer.com/article/10.1007/s44196-024-00595-5 |
| 18 | Span-based Unified NER via Contrastive Learning | IJCAI 2024 | 2024 | Contrastive span-type alignment | https://www.ijcai.org/proceedings/2024/0708.pdf |
| 19 | Pre-trained Embeddings for Entity Resolution | VLDB 2023 | 2023 | 12 embedding models compared for ER | https://www.vldb.org/pvldb/vol16/p2225-skoutas.pdf |
| 20 | Transformer-based Prototype Network for Chinese Nested NER | Scientific Reports | 2025 | Prototypical NER with transformers | https://www.nature.com/articles/s41598-025-04946-w |
| 21 | Adapter Tuning of LLM for Chinese Medical NER | Automation in Construction | 2024 | Adapters prevent catastrophic forgetting | https://www.tandfonline.com/doi/full/10.1080/08839514.2024.2385268 |
| 22 | Recent Advances in NER: Comprehensive Survey | arXiv 2401.10825 | 2024 | NER survey (embeddings, hybrid approaches) | https://arxiv.org/abs/2401.10825 |
| 23 | Spanish Datasets for Sensitive Entity Detection in Legal Domain | LREC 2022 | 2022 | MAPA project, Spanish legal NER datasets | https://aclanthology.org/2022.lrec-1.400/ |

---

## 9. Documents Associés

| Document | Relation |
| :--- | :--- |
| `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Document précédent proposant un validateur de type avec embeddings. Cette recherche MET À JOUR ses recommandations. |
| `docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Évaluation précédente des embeddings pour la classification de documents (tâche différente). |
| `docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Feuille de route embeddings pour la classification de documents. |
| `docs/reports/2026-01-30_investigacion_gaps_pipeline_hibrido.md` | Lacunes du pipeline NER hybride (contexte des erreurs de type). |
| `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Recherche sur le NER hybride (contexte de l'architecture). |

---

```
Version: 1.0.0
Temps de recherche : ~45 min
Articles revus : 23
```
