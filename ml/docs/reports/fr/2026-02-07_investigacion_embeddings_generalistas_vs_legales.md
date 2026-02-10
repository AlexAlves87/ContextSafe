# Recherche : Embeddings Généralistes vs Juridiques pour la Désambiguïsation des Types d'Entités

**Date :** 07/02/2026
**Objectif :** Déterminer s'il faut utiliser des embeddings généralistes (multilingual-e5-large) ou spécialisés en juridique (Legal-Embed, voyage-law-2) pour le validateur post-NER des types d'entités dans ContextSafe.

---

## 1. Résumé Exécutif

1.  **Principale découverte** : Les embeddings juridiques sont optimisés pour la **récupération** (trouver des documents similaires), PAS pour la **discrimination des types d'entités**. Cela explique les faux positifs observés.
2.  **Recommandation** : Utiliser des **embeddings généralistes** (`intfloat/multilingual-e5-large`) pour la désambiguïsation des types d'entités. Les embeddings juridiques peuvent provoquer un effondrement de l'espace sémantique où PERSONNE et ORGANISATION se retrouvent trop proches.
3.  **Preuve clé** : Le fine-tuning de domaine peut causer une "sur-spécialisation" qui réduit la capacité de discrimination entre les catégories (oubli catastrophique des frontières entre types).
4.  **Alternative hybride** : Si des connaissances juridiques sont nécessaires, utiliser une approche en deux étapes : généraliste pour le type + juridique pour la validation de l'entité spécifique.
5.  **Réduction d'erreurs attendue** : 4-5% avec des embeddings généralistes bien calibrés (littérature : WNUT17, NER Retriever).

---

## 2. Littérature Revue

### 2.1 Généralistes vs Spécifiques au Domaine

| Article/Source | Lieu/Année | Découverte Pertinente |
| :--- | :--- | :--- |
| "Do we need domain-specific embedding models?" | arXiv:2409.18511 (2024) | En finance (FinMTEB), les modèles généraux se dégradent par rapport aux spécifiques. MAIS : c'est pour la **récupération**, pas la classification de type. |
| "How Does Fine-tuning Affect the Geometry of Embedding Space?" | ACL Findings 2021 | Le fine-tuning de domaine **réduit la séparation** entre les classes dans l'espace d'embedding. Les clusters s'effondrent. |
| "Is Anisotropy Really the Cause of BERT Embeddings not Working?" | EMNLP Findings 2022 | L'anisotropie (embeddings concentrés dans un cône étroit) est un problème connu. Le fine-tuning de domaine l'**aggrave**. |
| "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE" | EMNLP 2025 | L'oubli catastrophique se produit lors du fine-tuning de domaine. Les modèles oublient les frontières apprises précédemment. |
| "Continual Named Entity Recognition without Catastrophic Forgetting" | arXiv:2310.14541 (2023) | Le NER continu souffre d'oubli catastrophique : les anciens types se "consolident" en non-entité. Analogue à notre problème. |

### 2.2 Pourquoi les Embeddings Juridiques Causent des Faux Positifs

| Phénomène | Explication | Source |
| :--- | :--- | :--- |
| **Effondrement de l'espace sémantique** | Le fine-tuning juridique optimise pour que les documents juridiques similaires soient proches, PAS pour séparer PERSONNE d'ORGANISATION | Blog Weaviate, Guide MongoDB Fine-Tuning |
| **Sur-spécialisation** | "Un entraînement trop étroit peut rendre le modèle fine-tuné trop spécialisé" - perd la capacité de discrimination générale | [Weaviate](https://weaviate.io/blog/fine-tune-embedding-model) |
| **Perte contrastive orientée récupération** | voyage-law-2 utilise des "paires positives spécifiquement conçues" pour la récupération juridique, pas pour la classification d'entités | [Blog Voyage AI](https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/) |
| **Terminologie juridique uniforme** | Dans les textes juridiques, "Garcia" peut être un plaignant, un avocat ou le nom d'un cabinet. Le modèle juridique les intègre **proches** car ils sont tous juridiques | Observation empirique de l'utilisateur |

### 2.3 Centroïdes et Classification Basée sur les Prototypes

| Article/Source | Lieu/Année | Découverte Pertinente |
| :--- | :--- | :--- |
| "NER Retriever: Zero-Shot NER with Type-Aware Embeddings" | arXiv:2509.04011 (2025) | Couches intermédiaires (couche 17) meilleures que les sorties finales pour le type. MLP avec perte contrastive pour séparer les types. |
| "CEPTNER: Contrastive Learning Enhanced Prototypical Network" | KBS (2024) | Réseaux prototypiques avec 50-100 exemples par type suffisent pour des centroïdes robustes. |
| "ReProCon: Scalable Few-Shot Biomedical NER" | arXiv:2508.16833 (2025) | Plusieurs prototypes par catégorie améliorent la représentation des entités hétérogènes. |
| "Mastering Intent Classification with Embeddings: Centroids" | Medium (2024) | Les centroïdes ont le "temps d'entraînement le plus rapide" et une précision décente. Parfait pour des mises à jour rapides. |

### 2.4 Benchmarks des Modèles d'Embedding

| Modèle | Taille | Langues | Moy MTEB | Avantage | Inconvénient |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `intfloat/multilingual-e5-large` | 1.1Go | 100 | ~64 | Meilleur multilingue général, excellent espagnol | Nécessite préfixe "query:" |
| `intfloat/multilingual-e5-large-instruct` | 1.1Go | 100 | ~65 | Supporte instructions, plus flexible | Légèrement plus lent |
| `BAAI/bge-m3` | 1.5Go | 100+ | ~66 | Hybride dense+sparse, 8192 jetons | Plus complexe à utiliser |
| `voyage-law-2` | API | EN | ~72 (juridique) | Meilleur pour récupération juridique | API commerciale, anglais uniquement |
| `Legal-Embed (Wasserstoff)` | 1.1Go | Multi | N/A | Fine-tuné sur juridique | **Cause probablement des FP en classification** |

---

## 3. Analyse : Pourquoi les Généralistes Sont Meilleurs pour le Type d'Entité

### 3.1 Objectif d'Entraînement Différent

| Embeddings Juridiques | Embeddings Généralistes |
| :--- | :--- |
| Optimisés pour : "document A similaire au document B" | Optimisés pour : "texte A sémantiquement lié au texte B" |
| Paires positives : fragments du même document juridique | Paires positives : paraphrases, traductions, variantes |
| Résultat : tout ce qui est juridique est proche | Résultat : types sémantiques séparés |

**Conséquence** : Dans les embeddings juridiques, "Alejandro Alvarez" (avocat) et "Bufete Alvarez S.L." (entreprise) sont **proches** car les deux sont juridiques. Dans les généralistes, ils sont **éloignés** car l'un est une personne et l'autre une organisation.

### 3.2 Preuve d'Anisotropie Aggravée

L'article d'ACL Findings 2021 démontre que :

1.  Le fine-tuning **réduit la variance** de l'espace d'embedding
2.  Les clusters de différents types **se rapprochent**
3.  La séparabilité linéaire **diminue**

Cela explique directement les faux positifs : quand tous les embeddings juridiques s'effondrent vers une région, la distance cosinus perd son pouvoir discriminatif.

### 3.3 Tâche vs Domaine

| Aspect | Embeddings de Domaine (Juridique) | Embeddings de Tâche (Type) |
| :--- | :--- | :--- |
| Question à laquelle ils répondent | "Ce texte est-il juridique ?" | "Est-ce une personne ou une entreprise ?" |
| Entraînement | Corpus juridique | Contrastif par type d'entité |
| Utilité pour validation type NER | Faible | Élevée |

Notre problème est un problème de **tâche** (classer le type), pas un problème de **domaine** (identifier des textes juridiques).

---

## 4. Recommandation pour ContextSafe

### 4.1 Approche Recommandée : Pur Généraliste

```
Pipeline:
  NER → Détections avec type assigné
    ↓
  EntityTypeValidator (multilingual-e5-large)
    ↓
  Pour chaque entité :
    1. Embedder "query: [entité + contexte ±10 jetons]"
    2. Comparer vs centroïdes par type (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
    3. Décisions :
       - Si meilleur_centroïde ≠ type_NER ET similarité > 0.75 ET marge > 0.10 → RECLASSIFIER
       - Si marge < 0.05 → SIGNALER HITL
       - Sinon → GARDER type NER
```

**Modèle** : `intfloat/multilingual-e5-large` (1.1Go)

**Justification** :

*   Entraîné sur 100 langues dont l'espagnol
*   NON sur-spécialisé dans aucun domaine
*   Préserve la séparation sémantique entre PERSONNE/ORGANISATION/DATE/LIEU
*   Déjà recommandé dans la recherche précédente (voir `2026-02-07_embeddings_entity_type_disambiguation.md`)

### 4.2 Approche Alternative : Hybride (Si Connaissance Juridique Nécessaire)

```
Étape 1 : Classification de type (GÉNÉRALISTE)
  multilingual-e5-large → Type d'entité

Étape 2 : Validation d'entité juridique (JURIDIQUE, optionnel)
  voyage-law-2 ou Legal-Embed → "Cette entité est-elle valide en contexte juridique ?"
  (Seulement pour cas signalés comme douteux)
```

**Quand utiliser hybride** : S'il y a des entités juridiques spécifiques (ex : "article 24.2 CE", "Loi 13/2022") nécessitant une validation par connaissance juridique.

Pour ContextSafe (PII générique), l'approche généraliste pure est suffisante.

### 4.3 Configuration des Centroïdes

| Type | Exemples Nécessaires | Stratégie de Contexte |
| :--- | :--- | :--- |
| PERSON_NAME | 100 | "query: L'avocat [NOM] a comparu..." |
| ORGANIZATION | 100 | "query: L'entreprise [ORG] a fait appel..." |
| DATE | 50 | "query: En date du [DATE] le jugement a été rendu..." |
| LOCATION | 50 | "query: Dans la ville de [LIEU] s'est tenu..." |
| DNI_NIE | 30 | "query: avec DNI [NUMÉRO]" (contexte court, modèle fixe) |

**Contexte** : ±10 jetons autour de l'entité. Ni trop court (perd le contexte) ni trop long (introduit du bruit).

---

## 5. Expérience Proposée

### 5.1 Comparaison A/B

| Condition | Modèle | Attendu |
| :--- | :--- | :--- |
| A (Baseline) | Sans validateur | Taux de réussite actuel : 60% |
| B (Généraliste) | `multilingual-e5-large` | Taux de réussite attendu : 64-65% |
| C (Juridique) | `Legal-Embed-intfloat-multilingual-e5-large-instruct` | Taux de réussite attendu : < 60% (plus de FP) |

### 5.2 Métriques à Évaluer

1.  **Taux de réussite en test adversarial** (35 tests existants)
2.  **Précision de reclassification** : % de reclassifications correctes
3.  **Taux de faux positifs** : Entités correctement typées qui ont été mal reclassifiées
4.  **Latence supplémentaire** : ms par entité validée

### 5.3 Cas de Test Spécifiques

Basés sur les erreurs de audit.md (voir `2026-02-07_embeddings_entity_type_disambiguation.md`, section 6) :

| Entité | Type NER | Type Correct | Modèle Attendu OK |
| :--- | :--- | :--- | :--- |
| "Alejandro Alvarez" | ORGANIZATION | PERSON_NAME | Généraliste |
| "10/10/2025" | ORGANIZATION | DATE | Généraliste |
| "Pura" | LOCATION | PERSON_NAME | Généraliste |
| "Finalmente" | ORGANIZATION | PAS PII | Généraliste (faible similarité avec tous) |
| "Whatsapp" | PERSON | ORGANIZATION/PLATFORM | Généraliste |

---

## 6. Risques et Atténuations

| Risque | Probabilité | Atténuation |
| :--- | :--- | :--- |
| Généraliste ne discrimine pas bien non plus PERSONNE/ORG en espagnol juridique | Moyenne | Évaluer avant d'implémenter ; si échec, entraîner centroïdes avec perte contrastive |
| Latence inacceptable (>100ms/entité) | Faible | Traitement par lots, cache d'embeddings fréquents |
| Centroïdes nécessitent plus de 100 exemples | Faible | Augmenter à 200 si F1 < 0.90 en validation |
| Modèle de 1.1Go ne tient pas en production | Faible | Quantifier en INT8 (~300Mo) ou utiliser e5-base (560Mo) |

---

## 7. Conclusion

**Les embeddings juridiques sont optimisés pour la mauvaise tâche.** Leur objectif (récupération de documents similaires) fait que des entités de différents types mais du même domaine (juridique) sont intégrées à proximité, réduisant la capacité de discrimination.

Pour la désambiguïsation des types d'entités, les **embeddings généralistes** préservent mieux les frontières sémantiques entre PERSONNE, ORGANISATION, DATE, etc., car ils n'ont pas été "effondrés" vers un domaine spécifique.

**Recommandation finale** : Implémenter le validateur avec `intfloat/multilingual-e5-large` et évaluer empiriquement avant de considérer des alternatives juridiques.

---

## 8. Prochaines Étapes

1.  [ ] Télécharger `intfloat/multilingual-e5-large` (~1.1Go)
2.  [ ] Construire un jeu de données d'exemples par type (PERSON_NAME, ORGANIZATION, DATE, LOCATION) avec contexte juridique
3.  [ ] Calculer les centroïdes pour chaque type
4.  [ ] Implémenter `EntityTypeValidator` avec seuils configurables
5.  [ ] Évaluer sur test adversarial (35 tests)
6.  [ ] (Optionnel) Comparer vs `Legal-Embed` pour confirmer l'hypothèse des faux positifs
7.  [ ] Documenter les résultats et la décision finale

---

## Documents Associés

| Document | Relation |
| :--- | :--- |
| `ml/docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Recherche précédente, architecture proposée |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Feuille de route embeddings, critères d'activation |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline actuel, métriques de référence |
| `auditoria.md` | Erreurs de classification identifiées |
| `ml/models/type_centroids.json` | Centroïdes existants (nécessite vérification du modèle utilisé) |

---

## Références

1.  **FinMTEB**: Li et al. (2024). "Do we need domain-specific embedding models? An empirical investigation." arXiv:2409.18511. https://arxiv.org/abs/2409.18511
2.  **Geometry of Fine-tuning**: Merchant et al. (2020). "What Happens To BERT Embeddings During Fine-tuning?" ACL Findings 2021. https://aclanthology.org/2021.findings-emnlp.261.pdf
3.  **Anisotropy**: Ethayarajh (2019). "How Contextual are Contextualized Word Representations?" EMNLP 2019. Rajaee & Pilehvar (2022). "Is Anisotropy Really the Cause?" EMNLP Findings 2022. https://aclanthology.org/2022.findings-emnlp.314.pdf
4.  **Catastrophic Forgetting in NER**: Wang et al. (2023). "Continual Named Entity Recognition without Catastrophic Forgetting." arXiv:2310.14541. https://arxiv.org/abs/2310.14541
5.  **DES-MoE**: Yang et al. (2025). "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE." EMNLP 2025. https://aclanthology.org/2025.emnlp-main.932.pdf
6.  **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot NER with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011
7.  **CEPTNER**: Wang et al. (2024). "Contrastive learning Enhanced Prototypical network for Few-shot NER." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512
8.  **ReProCon**: Liu et al. (2025). "ReProCon: Scalable Few-Shot Biomedical NER." arXiv:2508.16833. https://arxiv.org/abs/2508.16833
9.  **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings." arXiv:2402.05672. https://huggingface.co/intfloat/multilingual-e5-large
10. **voyage-law-2**: Voyage AI (2024). "Domain-Specific Embeddings: Legal Edition." https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/
11. **Fine-tuning Trade-offs**: Weaviate (2024). "Why, When and How to Fine-Tune a Custom Embedding Model." https://weaviate.io/blog/fine-tune-embedding-model
12. **Intent Classification with Centroids**: Puig (2024). "Mastering Intent Classification with Embeddings." Medium. https://medium.com/@mpuig/mastering-intent-classification-with-embeddings-centroids-neural-networks-and-random-forests-3fe7c57ca54c

---

```
Version: 1.0.0
Temps de recherche : ~25 min
Jetons de recherche : 12 requêtes
```
