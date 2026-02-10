# Recherche : Embeddings pour la Désambiguïsation des Types d'Entités dans le NER

**Date :** 07/02/2026
**Objectif :** Résoudre les erreurs de classification de type d'entité dans le système NER de ContextSafe (ex : "Alejandro Alvarez" classé comme ORGANIZATION au lieu de PERSON_NAME)

---

## 1. Résumé Exécutif

1. **Problème identifié** : Le modèle NER actuel confond les types d'entités, classant les noms de personnes comme des organisations, les dates comme des organisations, et les mots courants en majuscules comme des PII.

2. **Solution proposée** : Validateur post-NER basé sur des embeddings qui compare chaque détection avec des centroïdes sémantiques par type d'entité.

3. **Modèle recommandé** : `intfloat/multilingual-e5-large` (1,1 Go) avec une possible mise à niveau vers `Legal-Embed` pour le domaine juridique.

4. **Technique principale** : Classification basée sur les centroïdes avec seuil de reclassification (seuil 0,75, marge 0,1).

5. **Réduction d'erreurs attendue** : ~4,5% selon la littérature (benchmark WNUT17).

---

## 2. Littérature Examinée

| Article | Lieu | Année | Découverte Pertinente |
|---------|------|-------|-----------------------|
| NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings | arXiv (2509.04011) | 2025 | Les couches intermédiaires (couche 17) capturent mieux les informations de type que les sorties finales. Le MLP avec perte contrastive atteint le zéro-shot sur des types non vus. |
| CEPTNER: Contrastive Learning Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems (ScienceDirect) | 2024 | Les réseaux prototypiques avec apprentissage contrastif séparent efficacement les types d'entités avec peu d'exemples (50-100). |
| Recent Advances in Named Entity Recognition: A Comprehensive Survey | arXiv (2401.10825) | 2024 | Les approches hybrides (règles + ML + embeddings) surpassent constamment les modèles uniques. |
| Redundancy-Enhanced Framework for Error Correction in NER | OpenReview | 2025 | Le post-processeur avec raffineur Transformer + embeddings de balises d'entité atteint 4,48% de réduction d'erreur dans WNUT17. |
| Multilingual E5 Text Embeddings: A Technical Report | arXiv (2402.05672) | 2024 | Le modèle multilingual-e5-large prend en charge 100 langues avec d'excellentes performances en espagnol. Nécessite le préfixe "query:" pour les embeddings de recherche. |

---

## 3. Meilleures Pratiques Identifiées

1. **Inclure le contexte** : L'intégration de l'entité AVEC son contexte environnant (10-15 mots) améliore considérablement la désambiguïsation.

2. **Utiliser les couches intermédiaires** : Les représentations des couches moyennes (couche 15-17) contiennent plus d'informations de type que les sorties finales.

3. **Apprentissage contrastif** : L'entraînement avec perte contrastive sépare mieux les types dans l'espace des embeddings.

4. **Seuil avec marge** : Ne pas reclasser uniquement par une similarité plus élevée ; exiger une marge minimale (>0,1) pour éviter les faux positifs.

5. **Exemples par type** : 50-100 exemples confirmés par catégorie sont suffisants pour construire des centroïdes robustes.

6. **Domaine spécifique** : Les modèles affinés pour le domaine (juridique dans notre cas) améliorent les performances.

7. **Signalement pour HITL** : Lorsque les similarités sont proches (<0,05 de différence), marquer pour examen humain au lieu de reclasser automatiquement.

---

## 4. Recommandation pour ContextSafe

### 4.1 Architecture Proposée

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline NER Actuel                          │
│  (RoBERTa + SpaCy + Regex → Fusion Intelligente)                │
60 └─────────────────────┬───────────────────────────────────────────┘
                      │ Détections avec type assigné
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Validateur de Type d'Entité (NOUVEAU)               │
│                                                                  │
│  1. Extraire entité + contexte (±15 tokens)                     │
│  2. Générer embedding avec multilingual-e5-large                │
│  3. Calculer similarité cosinus avec centroïdes par type        │
│  4. Décision :                                                  │
│     - Si meilleur_type ≠ type_NER ET similarité > 0,75          │
│       ET marge > 0,1 → RECLASSER                                │
│     - Si marge < 0,05 → MARQUER POUR HITL                       │
│     - Sinon → CONSERVER type NER                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Détections validées/corrigées
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Glossaire & Anonymisation                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Modèle Sélectionné

**Principal** : `intfloat/multilingual-e5-large`
- Taille : 1,1 Go
- Langues : 100 (excellent espagnol)
- Latence : ~50-100ms par embedding
- Nécessite le préfixe "query:" pour les embeddings

**Alternative (évaluer)** : `Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct`
- Affiné pour le domaine juridique
- Même taille de base
- Potentiellement meilleur pour les documents juridiques espagnols

### 4.3 Construction des Centroïdes

Catégories prioritaires (confusion fréquente) :

| Catégorie | Exemples Nécessaires | Source |
|-----------|----------------------|--------|
| PERSON_NAME | 100 | Noms de auditoria.md + index de noms |
| ORGANIZATION | 100 | Entreprises, institutions de documents juridiques |
| DATE | 50 | Dates aux formats JJ/MM/AAAA, JJ-MM-AAAA |
| LOCATION | 50 | Villes, provinces espagnoles |

**Format d'exemple** (avec contexte) :
```
"query: L'avocat Alejandro Alvarez a comparu comme témoin au procès"
"query: La société Telefónica S.A. a déposé un pourvoi en cassation"
"query: En date du 10/10/2025 le jugement a été rendu"
```

### 4.4 Intégration avec le Pipeline Existant

Emplacement proposé : `src/contextsafe/infrastructure/nlp/validators/entity_type_validator.py`

```python
class EntityTypeValidator:
    """
    Post-processor that validates/corrects NER entity type assignments
    using embedding similarity to type centroids.

    Based on: NER Retriever (arXiv 2509.04011), CEPTNER (KBS 2024)
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        centroids_path: Path = None,
        reclassify_threshold: float = 0.75,
        margin_threshold: float = 0.10,
        hitl_margin: float = 0.05,
    ):
        ...

    def validate(
        self,
        entity_text: str,
        context: str,
        predicted_type: str,
    ) -> ValidationResult:
        """
        Returns ValidationResult with:
        - corrected_type: str
        - confidence: float
        - action: 'KEEP' | 'RECLASSIFY' | 'FLAG_HITL'
        """
        ...
```

### 4.5 Métriques de Succès

| Métrique | Objectif | Mesure |
|----------|----------|--------|
| Réduction des erreurs de type | ≥4% | Comparer avant/après sur l'ensemble de validation |
| Latence supplémentaire | <100ms/entité | Benchmark sur CPU 16 Go |
| Faux positifs de reclassification | <2% | Examen manuel des reclassifications |
| Couverture HITL | <10% marqués | Pourcentage marqué pour examen humain |

---

## 5. Références

1. **NER Retriever** : Zhang et al. (2025). "NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011

2. **CEPTNER** : Wang et al. (2024). "CEPTNER: Contrastive learning Enhanced Prototypical network for Two-stage Few-shot Named Entity Recognition." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512

3. **NER Survey** : Li et al. (2024). "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study." arXiv:2401.10825. https://arxiv.org/abs/2401.10825

4. **Error Correction Framework** : Chen et al. (2025). "A Redundancy-Enhanced Framework for Error Correction in Named Entity Recognition." OpenReview. https://openreview.net/forum?id=2jFWhxJE5pQ

5. **Multilingual E5** : Wang et al. (2024). "Multilingual E5 Text Embeddings: A Technical Report." arXiv:2402.05672. https://arxiv.org/abs/2402.05672

6. **Legal-Embed** : Wasserstoff-AI. (2024). "Legal-Embed-intfloat-multilingual-e5-large-instruct." HuggingFace. https://huggingface.co/Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct

---

## 6. Erreurs de Classification Identifiées (Audit)

Analyse du fichier `auditoria.md` du document STSJ ICAN 3407/2025 :

| Entité | Type Assigné | Type Correct | Modèle |
|--------|--------------|--------------|--------|
| `"10/10/2025"` | ORGANIZATION (Org_038) | DATE | Date confondue avec code |
| `"05-11-2024"` | ORGANIZATION | DATE | Date au format JJ-MM-AAAA |
| `"Pura"` | LOCATION (Lugar_001) | PERSON_NAME | Nom court sans honorifique |
| `"Finalmente"` | ORGANIZATION (Org_012) | PAS DE PII | Adverbe en majuscule |
| `"Terminaba"` | ORGANIZATION (Org_017) | PAS DE PII | Verbe en majuscule |
| `"Quien"` | ORGANIZATION | PAS DE PII | Pronom en majuscule |
| `"Whatsapp"` | PERSON | ORGANIZATION/PLATFORM | Nom de plateforme |

**Motif principal identifié** : Le modèle RoBERTa classe comme ORGANIZATION tout mot en majuscule en début de phrase qu'il ne reconnaît pas clairement comme un autre type.

---

## Documents Associés

| Document | Relation |
|----------|----------|
| `auditoria.md` | Source des erreurs de classification analysées |
| `docs/PLAN_CORRECCION_AUDITORIA.md` | Plan de correction précédent (7 problèmes identifiés) |
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Évaluation précédente des embeddings (classification de documents) |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Feuille de route des embeddings pour la classification |
| `ml/README.md` | Instructions ML (format de rapport) |

---

## Prochaines Étapes

1. [ ] Télécharger le modèle `intfloat/multilingual-e5-large` (~1,1 Go)
2. [ ] Construire un jeu de données d'exemples par type (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
3. [ ] Implémenter `EntityTypeValidator` dans `infrastructure/nlp/validators/`
4. [ ] Calculer et persister les centroïdes par type
5. [ ] Intégrer le validateur dans le pipeline NER existant
6. [ ] Évaluer la réduction des erreurs sur l'ensemble de validation
7. [ ] (Optionnel) Évaluer `Legal-Embed` vs `multilingual-e5-large`

---

```
Version : 1.0.0
Temps de recherche : ~15 min
```
