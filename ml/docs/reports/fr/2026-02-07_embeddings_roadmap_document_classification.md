# Embeddings pour ContextSafe : Feuille de Route et Critères d'Activation

**Date :** 07/02/2026
**Objectif :** Documenter l'approche par embeddings évaluée, les alternatives mises en œuvre,
et les critères selon lesquels le passage aux embeddings serait justifiable à l'avenir.

---

## 1. Résumé Exécutif

Deux propositions impliquant des embeddings ont été évaluées :

| Proposition | Source | Modèle | Décision |
|-------------|--------|--------|----------|
| Classification de documents avec embeddings | Améliorations Architecturales v2.1, Module A | `intfloat/multilingual-e5-small` | **Différée** — Regex implémentée |
| Balayage des lacunes avec embeddings | Stratégie Filet de Sécurité A | `intfloat/multilingual-e5-small` | **Rejetée** — Similarité cosinus inadéquate |

**État actuel :** Un classificateur basé sur les regex/mots-clés (`DocumentTypeClassifier`) a été implémenté,
couvrant les exigences immédiates avec 0 octet de modèle, <1ms de latence et ~95% de précision estimée
pour les documents juridiques espagnols.

Les embeddings sont documentés comme **option de mise à l'échelle future** lorsque des critères
spécifiques seront remplis (Section 5).

---

## 2. Proposition Évaluée : Classification de Documents avec Embeddings

### 2.1 Modèle Proposé

| Spécification | Valeur |
|---------------|--------|
| Modèle | `intfloat/multilingual-e5-small` (Wang et al., arXiv:2402.05672) |
| Paramètres | 117,65M |
| Taille FP32 | 448 Mo |
| Taille INT8 ONNX | 112 Mo |
| Dimension Embedding | 384 |
| Jetons max | 512 |
| Latence estimée (CPU INT8) | ~200ms |
| Langues supportées | 94-100 |
| Licence | MIT |
| RAM exécution (FP32) | ~500 Mo |
| RAM exécution (INT8) | ~200 Mo |

**Source de vérification :** Carte du modèle HuggingFace `intfloat/multilingual-e5-small`.

### 2.2 Architecture Proposée

```
Document → Embedding (e5-small) → Similarité Cosinus vs centroïdes → Type → Config NER
```

Ce N'EST PAS du RAG-NER (le terme utilisé dans la proposition v2.1 est incorrect).
C'est de la **classification de documents + configuration conditionnelle**
(voir `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md`, Section 2).

### 2.3 Pourquoi Elle a Été Différée

| Facteur | Embeddings | Regex (implémentée) |
|---------|------------|---------------------|
| Taille | 112-448 Mo | 0 octet |
| Latence | ~200ms | <1ms |
| Précision estimée | ~99% | ~95%+ |
| Complexité | Élevée (runtime ONNX, quantification) | Triviale |
| RAM supplémentaire | 200-500 Mo | 0 |
| Maintenance | Modèle versionné, mises à jour | Motifs modifiables |

Pour ~7 types de documents juridiques avec des en-têtes très distinctifs, la regex est
suffisante. Les 4% de précision supplémentaires ne justifient ni les 200 Mo du modèle ni la
complexité de maintenance.

---

## 3. Proposition Évaluée : Balayage des Lacunes avec Embeddings

### 3.1 Concept

Utiliser des embeddings pour détecter des fragments "suspects" non identifiés par le NER :

```
Texte complet → Segmenter en morceaux → Embedding de chaque morceau
    → Comparer vs "centroïde de risque PII" → Alerter si similarité élevée
```

### 3.2 Pourquoi Elle a Été Rejetée

1. **La similarité cosinus ne détecte pas les PII** : La similarité sémantique mesure la proximité thématique,
   pas la présence de données personnelles. "Juan García vit à Madrid" et "L'entreprise opère
   à Madrid" ont une similarité sémantique élevée mais un seul contient des PII nominales.

2. **Il n'existe pas de "centroïde de risque PII"** : Les données personnelles (noms, DNI, IBAN,
   adresses) occupent des régions sémantiques complètement disjointes. Il n'y a pas de point dans
   l'espace des embeddings qui représente "ceci contient des PII"
   (voir Ethayarajh, EMNLP 2019, sur l'anisotropie des embeddings).

3. **Article de référence** : Netflix/Cornell 2024 documente les limites de la similarité cosinus
   pour la détection de caractéristiques discrètes vs continues. Les PII sont intrinsèquement
   discrètes (présentes ou absentes).

4. **Alternative implémentée** : Les contrôles de cohérence déterministes (`ExportValidator`,
   `src/contextsafe/domain/document_processing/services/export_validator.py`) couvrent
   le cas des faux négatifs par type de document de manière plus fiable et sans
   dépendances supplémentaires.

---

## 4. Alternative Implémentée : Classificateur Regex

### 4.1 Implémentation

```
src/contextsafe/domain/document_processing/services/document_classifier.py
```

| Caractéristique | Détail |
|-----------------|--------|
| Types supportés | SENTENCIA, ESCRITURA, FACTURA, RECURSO, DENUNCIA, CONTRATO, GENERIC |
| Méthode | Regex sur les 500 premiers caractères (en majuscules) |
| Motifs par type | 4-8 mots-clés distinctifs |
| Repli | Nom du fichier si le texte ne classifie pas |
| Confiance | Ratio de motifs trouvés / total par type |
| Latence | <1ms |
| Dépendances | 0 (seulement `re` de stdlib) |

### 4.2 Motifs Clés

| Type | Motifs principaux |
|------|-------------------|
| SENTENCIA | `SENTENCIA`, `JUZGADO`, `TRIBUNAL`, `FALLO`, `MAGISTRAD[OA]` |
| ESCRITURA | `ESCRITURA`, `NOTAR[IÍ]`, `PROTOCOLO`, `OTORGAMIENTO` |
| FACTURA | `FACTURA`, `BASE IMPONIBLE`, `IVA`, `TOTAL FACTURA` |
| RECURSO | `RECURSO`, `APELACI[OÓ]N`, `CASACI[OÓ]N` |
| DENUNCIA | `DENUNCIA`, `ATESTADO`, `DILIGENCIAS PREVIAS` |
| CONTRATO | `CONTRATO`, `CL[AÁ]USULA`, `ESTIPULACIONES` |

### 4.3 Intégration avec les Contrôles de Cohérence

Le classificateur alimente les règles de validation d'exportation :

```
Document → DocumentTypeClassifier → type
                                       ↓
ExportValidator.validate(type, ...) → Applique les règles SC-001..SC-004
```

| Règle | Type | Catégories minimales | Sévérité |
|-------|------|----------------------|----------|
| SC-001 | ESCRITURA | PERSON_NAME ≥1, DNI_NIE ≥1 | CRITIQUE |
| SC-002 | SENTENCIA | DATE ≥1 | AVERTISSEMENT |
| SC-003 | FACTURA | ORGANIZATION ≥1 | AVERTISSEMENT |
| SC-004 | DENUNCIA | PERSON_NAME ≥1 | AVERTISSEMENT |

---

## 5. Critères d'Activation pour Passer aux Embeddings

Les embeddings ne devraient être reconsidérés QUE si **au moins 2** de ces critères sont remplis :

### 5.1 Critères Fonctionnels

| # | Critère | Seuil |
|---|---------|-------|
| CF-1 | La précision de la regex tombe sous 90% | Mesurer avec corpus de validation |
| CF-2 | >15 types de documents ajoutés | La regex devient ingérable |
| CF-3 | Documents sans en-tête standardisé | OCR dégradé, scanners variés |
| CF-4 | Exigence de classification multilingue | Documents en catalan, basque, galicien |

### 5.2 Critères d'Infrastructure

| # | Critère | Seuil |
|---|---------|-------|
| CI-1 | RAM disponible en production | ≥32 Go (actuellement l'objectif est 16 Go) |
| CI-2 | Le pipeline utilise déjà le runtime ONNX | Évite d'ajouter une nouvelle dépendance |
| CI-3 | Latence actuelle du pipeline | <2s total (marge pour +200ms) |

### 5.3 Chemin d'Implémentation (si activé)

```
Étape 1 : Collecter corpus de validation (50+ docs par type)
Étape 2 : Évaluer la précision actuelle de la regex avec le corpus
Étape 3 : Si précision < 90%, évaluer d'abord TF-IDF + LogReg (~50Ko, <5ms)
Étape 4 : Seulement si TF-IDF < 95%, passer à e5-small INT8 ONNX
Étape 5 : Générer des centroïdes par type avec corpus étiqueté
Étape 6 : Valider avec des tests adversariaux (documents mixtes, OCR dégradé)
```

### 5.4 Modèle Recommandé (si passage à l'échelle)

| Option | Taille | Latence | Cas d'utilisation |
|--------|--------|---------|-------------------|
| TF-IDF + LogReg | ~50 Ko | <5ms | Première étape de mise à l'échelle |
| `intfloat/multilingual-e5-small` INT8 | 112 Mo | ~200ms | Classification multilingue |
| `BAAI/bge-small-en-v1.5` INT8 | 66 Mo | ~150ms | Seulement anglais/espagnol |

**Note :** `intfloat/multilingual-e5-small` reste la meilleure option pour le multilingue
si nécessaire. Mais TF-IDF est l'étape intermédiaire correcte avant les embeddings neuronaux.

---

## 6. Impact sur le Pipeline NER

### 6.1 État Actuel (implémenté)

```
Document ingéré
    ↓
DocumentTypeClassifier.classify(premiers_500_caractères) ← REGEX
    ↓
ConfidenceZone.classify(score, catégorie, checksum)      ← TRIAGE
    ↓
CompositeNerAdapter.detect_entities(text)                ← NER
    ↓
ExportValidator.validate(type, entités, révisions)       ← LOQUET DE SÉCURITÉ
    ↓
[Export autorisé ou bloqué]
```

### 6.2 État Futur (si embeddings activés)

```
Document ingéré
    ↓
DocumentTypeClassifier.classify(premiers_500_caractères) ← REGEX (repli)
    ↓
EmbeddingClassifier.classify(premiers_512_tokens)        ← EMBEDDINGS
    ↓
merge_classifications(résultat_regex, résultat_emb)      ← FUSION
    ↓
CompositeNerAdapter.detect_entities(text, type_doc=type) ← NER CONTEXTUEL
    ↓
ExportValidator.validate(type, entités, révisions)       ← LOQUET DE SÉCURITÉ
```

L'interface du classificateur (`DocumentClassification` dataclass) est déjà conçue pour
être remplaçable sans changements dans le reste du pipeline.

---

## 7. Conclusion

L'approche actuelle (regex) est la décision correcte pour l'état présent du projet.
Les embeddings représentent une amélioration incrémentale qui n'est justifiée que face à une croissance
significative des types de documents ou une dégradation mesurable de la précision.

L'architecture hexagonale permet de passer à l'échelle sans refactoring : le `DocumentTypeClassifier`
peut être remplacé par un `EmbeddingClassifier` implémentant la même interface
(`DocumentClassification`), sans impact sur le reste du pipeline.

---

## Documents Associés

| Document | Relation |
|----------|----------|
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Évaluation critique de la proposition RAG-NER |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline NER actuel (5 éléments) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Évaluation adversariale du pipeline |
| `src/contextsafe/domain/document_processing/services/document_classifier.py` | Classificateur regex implémenté |
| `src/contextsafe/domain/document_processing/services/export_validator.py` | Loquet de Sécurité + Contrôles de Cohérence |
| `src/contextsafe/domain/entity_detection/services/confidence_zone.py` | Triage par zones de confiance |

## Références

| Référence | Lieu | Pertinence |
|-----------|------|------------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Modèle évalué |
| Ethayarajh, "How Contextual are Contextualized Word Representations?" | EMNLP 2019 | Anisotropie des embeddings |
| Netflix/Cornell, "Limitations of Cosine Similarity" | arXiv (2024) | Limitations pour la détection discrète |
| Lewis et al., "Retrieval-Augmented Generation" | NeurIPS 2020 | Définition correcte du RAG |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | Vrai RAG appliqué au NER |
