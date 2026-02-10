# Évaluation Critique : Proposition d'Embeddings (RAG-NER) pour ContextSafe

**Date :** 07/02/2026
**Objectif :** Évaluer la validité technique et la nécessité du Module A de la proposition
"Améliorations Architecturales v2.1" — utilisation de `intfloat/multilingual-e5-small` pour
la pré-classification des documents et la configuration dynamique du NER.

---

## 1. Résumé Exécutif

La proposition suggère d'utiliser des embeddings (`intfloat/multilingual-e5-small`, ~120Mo) comme
"Élément 0" du pipeline NER pour classer les types de documents et ajuster dynamiquement
les seuils de détection. Après avoir examiné la littérature académique, vérifié les
spécifications du modèle et comparé avec l'état actuel du pipeline de ContextSafe,
**la conclusion est que l'idée de base a du mérite partiel, mais l'implémentation proposée
est une sur-ingénierie et le terme "RAG-NER" est techniquement incorrect**.

### Verdict

| Aspect | Évaluation |
|--------|------------|
| Concept (NER conscient du type de document) | Valide et utile |
| Terme "RAG-NER" | Incorrect : ce n'est pas du RAG |
| Modèle proposé (`multilingual-e5-small`) | Surdimensionné pour la tâche |
| Nécessité réelle dans ContextSafe | Moyenne : alternatives plus simples disponibles |
| Priorité vs autres améliorations | Faible par rapport aux améliorations HITL et d'audit |

---

## 2. Analyse du Terme "RAG-NER"

### Qu'est-ce que le RAG dans la littérature

Le RAG (Retrieval-Augmented Generation) a été introduit par Lewis et al. (NeurIPS 2020)
et fait référence spécifiquement à la **récupération de documents/passages d'une base de
connaissances pour augmenter la génération** d'un modèle de langage.

Les véritables articles RAG+NER (2024-2025) sont :

| Article | Lieu | Ce qu'il fait réellement |
|---------|------|--------------------------|
| **RA-NER** (Dai et al.) | ICLR 2024 Tiny Papers | Récupère des entités similaires d'une base externe pour aider le NER |
| **RENER** (Shiraishi et al.) | arXiv 2410.13118 | Récupère des exemples annotés similaires comme apprentissage en contexte pour le NER |
| **RA-IT Open NER** | arXiv 2406.17305 | Instruction tuning avec exemples récupérés pour le NER ouvert |
| **IF-WRANER** | arXiv 2411.00451 | Récupération au niveau des mots pour le NER few-shot cross-domain |
| **RAG-BioNER** | arXiv 2508.06504 | Prompting dynamique avec RAG pour le NER biomédical |

### Ce que propose le document v2.1

Ce qui est décrit n'est PAS du RAG. C'est de la **classification de type de document + configuration
conditionnelle du NER**. Il n'y a pas de récupération de documents/exemples d'une base de
connaissances. Il n'y a pas d'augmentation de la génération. C'est un classificateur suivi d'un commutateur.

**Diagramme réel de la proposition :**
```
Document → Embedding (e5-small) → Similarité Cosinus → Type détecté → Switch de config → NER
```

**Diagramme réel du RAG-NER (RA-NER, Amazon) :**
```
Texte d'entrée → Récupérer entités similaires de la base → Injecter comme contexte au NER → Prédiction
```

Ce sont des architectures fondamentalement différentes. Étiqueter la proposition comme "RAG-NER"
est incorrect et pourrait induire en erreur dans la documentation technique ou les publications.

---

## 3. Vérification du Modèle Proposé

### Spécifications réelles de `intfloat/multilingual-e5-small`

| Spécification | Affirmation v2.1 | Valeur réelle | Source |
|---------------|------------------|---------------|--------|
| Poids | ~120 Mo | **448 Mo (FP32), 112 Mo (INT8 ONNX)** | HuggingFace |
| Paramètres | Non indiqué | 117,65M | HuggingFace |
| Dimension embedding | Non indiqué | 384 | Article arXiv:2402.05672 |
| Jetons max | 512 | 512 (correct) | HuggingFace |
| Latence | <200ms sur CPU | Plausible pour 512 jetons INT8 | - |
| Langues | Non indiqué | 94-100 langues | HuggingFace |
| Licence | Non indiqué | MIT | HuggingFace |

**Problèmes détectés :**
- L'affirmation de "~120 Mo" n'est vraie qu'avec la quantification INT8 ONNX. Le modèle FP32 pèse
  448 Mo. Le document ne précise pas que la quantification est requise.
- En mémoire (exécution), le modèle FP32 consomme ~500Mo de RAM. Avec INT8, ~200Mo.
- Sur le matériel cible de 16Go de RAM (déjà chargé avec RoBERTa + Presidio + spaCy),
  la marge disponible est limitée.

### Benchmark de référence

| Benchmark | Résultat | Contexte |
|-----------|----------|----------|
| Mr. TyDi (retrieval MRR@10) | 64,4 moy | Bon pour la récupération multilingue |
| MTEB Classification (Amazon) | 88,7% précision | Acceptable pour la classification |

Le modèle est compétent pour les tâches d'embeddings. La question est de savoir si un modèle
de 117M paramètres est nécessaire pour classer ~5 types de documents juridiques.

---

## 4. Analyse des Besoins : État Actuel vs Proposition

### Pipeline actuel de ContextSafe

Le `CompositeNerAdapter` implémente déjà des mécanismes de contextualisation sophistiqués :

| Mécanisme existant | Description |
|--------------------|-------------|
| **Ancres Contextuelles** (Phase 1) | Force les catégories selon le contexte juridique espagnol |
| **Vote Pondéré** (Phase 2) | Regex=5, RoBERTa=2, Presidio=1,5, spaCy=1 |
| **Tiebreaker de Risque RGPD** (Phase 3) | Priorité : PERSON_NAME=100 → POSTAL_CODE=20 |
| **30+ Motifs de Faux Positifs** | Bloque références légales, DOI, ORCID, ISBN |
| **Filtre Stopwords Espagnols** | Évite la détection d'articles/pronoms |
| **Liste Blanche Termes Génériques** | Termes jamais anonymisés (État, RGPD, etc.) |
| **Matrioshka (entités imbriquées)** | Gestion des entités imbriquées |

Le pipeline actuel n'a PAS :
- Classification de type de document
- Seuils dynamiques par catégorie
- Seuils dynamiques par type de document

### ContextSafe a-t-il besoin de la classification de documents ?

**Partiellement oui**, mais pas comme proposé. Les avantages réels seraient :
- Ajuster le seuil IBAN dans les factures (plus strict) vs jugements (plus souple)
- Activer/désactiver des catégories selon le contexte (ex. date de naissance pertinente
  dans les jugements pénaux, pas dans les factures)
- Réduire les faux positifs de noms propres dans les documents avec beaucoup de raisons sociales

### Alternatives plus simples et efficaces

| Méthode | Taille | Latence | Précision estimée | Complexité |
|---------|--------|---------|-------------------|------------|
| **Regex sur en-têtes** | 0 Ko (code) | <1ms | ~95%+ | Triviale |
| **TF-IDF + LogisticRegression** | ~50 Ko | <5ms | ~97%+ | Faible |
| **e5-small (INT8 ONNX)** | 112 Mo | ~200ms | ~99% | Élevée |
| **e5-small (FP32)** | 448 Mo | ~400ms | ~99% | Élevée |

Pour les documents juridiques espagnols, les en-têtes sont extrêmement distinctifs :
- `"SENTENCIA"`, `"JUZGADO"`, `"TRIBUNAL"` → Jugement
- `"ESCRITURA"`, `"NOTARIO"`, `"PROTOCOLO"` → Acte Notarié
- `"FACTURA"`, `"BASE IMPONIBLE"`, `"IVA"` → Facture
- `"RECURSO"`, `"APELACIÓN"`, `"CASACIÓN"` → Appel/Recours

Un classificateur basé sur des regex/mots-clés dans les 200 premiers caractères atteint
probablement >95% de précision sans ajouter de dépendances ni de latence significative.

---

## 5. Recommandation

### Ce qui EST recommandé d'implémenter

1. **Classification de type de document** — mais avec regex/mots-clés, pas d'embeddings
2. **Seuils dynamiques par catégorie** — indépendant de la classification
3. **Configuration conditionnelle du NER** — activer/désactiver règles selon type

### Ce qui N'EST PAS recommandé

1. **Ne pas utiliser d'embeddings** pour classer ~5 types de documents juridiques
2. **Ne pas appeler cela "RAG-NER"** — c'est de la classification + configuration conditionnelle
3. **Ne pas ajouter 112-448Mo de modèle** quand la regex atteint le même objectif

### Implémentation suggérée (alternative)

```python
# Element 0: Document Type Classifier (lightweight)
class DocumentTypeClassifier:
    """Classify legal document type from header text."""

    PATTERNS = {
        DocumentType.SENTENCIA: [r"SENTENCIA", r"JUZGADO", r"TRIBUNAL", r"FALLO"],
        DocumentType.ESCRITURA: [r"ESCRITURA", r"NOTARI", r"PROTOCOLO"],
        DocumentType.FACTURA: [r"FACTURA", r"BASE IMPONIBLE", r"IVA"],
        DocumentType.RECURSO: [r"RECURSO", r"APELACI[OÓ]N", r"CASACI[OÓ]N"],
    }

    def classify(self, text: str, max_chars: int = 500) -> DocumentType:
        header = text[:max_chars].upper()
        scores = {}
        for doc_type, patterns in self.PATTERNS.items():
            scores[doc_type] = sum(1 for p in patterns if re.search(p, header))
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return DocumentType.GENERIC
```

**Coût :** 0 octet de modèle, <1ms latence, ~0 complexité supplémentaire.
**Extensible :** Si une plus grande sophistication est nécessaire à l'avenir, on peut passer
à TF-IDF ou aux embeddings. Mais commencer simple.

---

## 6. À propos de l'"Élément 0" dans le pipeline

S'il est décidé d'implémenter la classification de documents (avec la méthode simple recommandée),
l'emplacement correct serait :

```
Document ingéré
    ↓
Element 0: classify_document_type(premiers_500_caractères)  ← NOUVEAU
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=type)
    ↓
[RoBERTa | Presidio | Regex | spaCy] avec seuils ajustés selon doc_type
    ↓
Fusion (vote pondéré actuel, fonctionne déjà bien)
```

Cette étape est cohérente avec l'architecture hexagonale actuelle et ne nécessite aucun changement
aux ports ou adaptateurs existants.

---

## 7. Conclusion

La proposition identifie un besoin réel (NER conscient du type de document)
mais propose une solution sur-ingénierie avec une terminologie incorrecte. Un classificateur
basé sur des regex sur les en-têtes de documents atteindrait le même objectif sans ajouter
120-448Mo de modèle, 200ms de latence supplémentaire, ou de complexité de maintenance.

L'investissement d'effort est beaucoup plus rentable dans le Module B (audit actif et
traçabilité HITL), où ContextSafe a de réelles lacunes de conformité réglementaire.

---

## 8. Littérature Consultée

| Référence | Lieu | Pertinence |
|-----------|------|------------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Modèle proposé |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | Vrai RAG appliqué au NER |
| Shiraishi et al., "RENER" | arXiv:2410.13118 (2024) | Retrieval-enhanced NER |
| arXiv 2406.17305, "RA-IT Open NER" | arXiv (2024) | Instruction tuning + retrieval |
| arXiv 2411.00451, "IF-WRANER" | arXiv (2024) | Few-shot cross-domain NER + RAG |
| arXiv 2508.06504, "RAG-BioNER" | arXiv (2025) | Prompting dynamique + RAG |
| ACL 2020 LT4Gov, "Legal-ES" | ACL Anthology | Embeddings juridiques espagnols |
| IEEE 2024, "Fine-grained NER Spanish legal" | IEEE Xplore | NER juridique espagnol |
| Frontiers AI 2025, "LegNER multilingual" | Frontiers | NER juridique multilingue |

## Documents Associés

| Document | Relation |
|----------|----------|
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline NER actuel (5 éléments) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Évaluation adversariale du pipeline actuel |
| `ml/docs/reports/2026-01-31_mejores_practicas_ml_2026.md` | Meilleures pratiques ML |
| `src/contextsafe/infrastructure/nlp/composite_adapter.py` | Implémentation actuelle du pipeline NER |
