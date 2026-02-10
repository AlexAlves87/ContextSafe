# Recherche : Meilleures Pratiques pour le Pipeline de Détection de PII

**Date :** 2026-01-16
**Type :** Revue de Littérature
**État :** Terminé

---

## Résumé Exécutif

Cette recherche analyse l'état de l'art en matière de détection de PII (Personally Identifiable Information) en mettant l'accent sur les documents juridiques espagnols. Des articles académiques récents (2024-2025) et des frameworks de production ont été examinés pour identifier les meilleures pratiques en matière de prétraitement, d'architecture de pipeline et de post-traitement.

**Principale Conclusion :** L'architecture optimale est **hybride** (Regex → NER → Validation), et non NER pur avec post-traitement. De plus, l'injection de bruit OCR (30%) pendant l'entraînement améliore considérablement la robustesse.

---

## Méthodologie

### Sources Consultées

| Source | Type | Année | Pertinence |
|--------|------|-----|------------|
| PMC12214779 | Article Académique | 2025 | Hybride NLP-ML pour PII financier |
| arXiv 2401.10825v3 | Enquête | 2024 | État de l'art NER |
| Microsoft Presidio | Framework | 2024 | Meilleures pratiques de l'industrie |
| Presidio Research | Boîte à outils | 2024 | Évaluation des reconnaisseurs |

### Critères de Recherche

- "NER preprocessing postprocessing best practices 2024"
- "Spanish legal documents PII detection"
- "Hybrid rule-based NLP machine learning PII"
- "Presidio pipeline architecture"

---

## Résultats

### 1. Architecture de Pipeline Optimale

#### 1.1 Ordre de Traitement (Presidio)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Texte    │ → │   Regex     │ → │   NLP NER   │ → │  Checksum   │ → │  Seuil      │
│    (OCR)    │    │  Matchers   │    │   Modèle    │    │ Validation  │    │   Filtre    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Source :** Documentation Microsoft Presidio

**Justification :**
> "Presidio utilise initialement son matcher regex pour identifier les entités correspondantes. Ensuite, le modèle NER basé sur le Traitement du Langage Naturel est utilisé pour détecter les PII de manière autonome. Lorsque cela est possible, un checksum est utilisé pour valider les PII identifiés."

#### 1.2 Composants du Pipeline

| Composant | Fonction | Implémentation |
|------------|---------|----------------|
| **Regex Matchers** | Détecter des modèles structurés (DNI, IBAN, téléphone) | Exécuter AVANT le NER |
| **NLP NER** | Détecter des entités contextuelles (noms, adresses) | Modèle Transformer |
| **Checksum Validation** | Valider l'intégrité des identifiants | DNI mod-23, IBAN mod-97 |
| **Context Enhancement** | Améliorer la confiance avec le contexte lexical | LemmaContextAwareEnhancer |
| **Threshold Filter** | Filtrer par score de confiance | Configurable (ex : 0,7) |

### 2. Prétraitement

#### 2.1 Normalisation du Texte

**Source :** PMC12214779 (Hybride NLP-ML)

| Technique | Description | Applicabilité |
|---------|-------------|---------------|
| Tokenisation | Division en unités discrètes | Universelle |
| Marquage de position | Marquage de position au niveau des caractères | Pour la récupération de span |
| Normalisation Unicode | Fullwidth → ASCII, suppression de largeur nulle | Élevée pour OCR |
| Normalisation des abréviations | D.N.I. → DNI | Élevée pour l'espagnol |

#### 2.2 Injection de Bruit (CRITIQUE)

**Source :** PMC12214779

> "Pour mieux simuler les anomalies des documents du monde réel, le prétraitement des données ajoute un bruit aléatoire mineur comme la suppression de la ponctuation et la normalisation du texte."

**Implémentation recommandée :**
```python
# 30% de probabilité de bruit par échantillon
noise_probability = 0.30

# Types de bruit :
# - Suppression aléatoire de ponctuation
# - Substitution de caractères OCR (l↔I, 0↔O)
# - Réduction/expansion d'espaces
# - Perte d'accents
```

**Impact :** Améliore la robustesse face aux documents scannés réels.

### 3. Architecture du Modèle

#### 3.1 État de l'Art NER (2024)

**Source :** arXiv 2401.10825v3

| Architecture | Caractéristiques | Benchmark F1 |
|--------------|-----------------|--------------|
| DeBERTa | Attention désenchevêtrée + décodeur de masque amélioré | SOTA |
| RoBERTa + CRF | Transformer + cohérence de séquence | +4-13% vs base |
| BERT + BiLSTM | Modélisation contextuelle + séquentielle | Robuste |
| GLiNER | Attention globale pour entités distantes | Innovant |

#### 3.2 Couche CRF

**Source :** Enquête arXiv

> "L'application de CRF fournit une méthode robuste pour la reconnaissance d'entités nommées (NER) en assurant des séquences d'étiquettes cohérentes et en modélisant les dépendances entre les étiquettes adjacentes."

**Avantage :** Empêche les séquences invalides comme `B-PERSON I-LOCATION`.

### 4. Post-traitement

#### 4.1 Validation par Checksum

**Source :** Meilleures Pratiques Presidio

| Type | Algorithme | Exemple |
|------|-----------|---------|
| DNI espagnol | lettre = "TRWAGMYFPDXBNJZSQVHLCKE"[num % 23] | 12345678Z |
| NIE espagnol | Préfixe X=0, Y=1, Z=2 + algorithme DNI | X1234567L |
| IBAN | ISO 7064 Mod 97-10 | ES9121000418450200051332 |
| NSS espagnol | Mod 97 sur les 10 premiers chiffres | 281234567890 |
| Carte de crédit | Algorithme de Luhn | 4111111111111111 |

#### 4.2 Amélioration Contextuelle

**Source :** Presidio LemmaContextAwareEnhancer

> "Le ContextAwareEnhancer est un module qui améliore la détection des entités en utilisant le contexte du texte. Il peut améliorer la détection des entités qui dépendent du contexte."

**Implémentation :**
- Rechercher des mots-clés dans une fenêtre de ±N tokens
- Augmenter/diminuer le score selon le contexte
- Exemple : "DNI" près d'un numéro augmente la confiance DNI_NIE

#### 4.3 Filtrage par Seuil

**Source :** Guide de Réglage Presidio

> "Ajustez les seuils de confiance sur les reconnaisseurs ML pour équilibrer les cas manqués par rapport au sur-masquage."

**Recommandation :**
- Seuil élevé (0,8+) : Moins de faux positifs, plus de faux négatifs
- Seuil bas (0,5-0,6) : Plus de couverture, plus de bruit
- Pilote initial pour calibrer

### 5. Résultats de Benchmark

#### 5.1 Hybride NLP-ML (PMC12214779)

| Métrique | Valeur |
|---------|-------|
| Précision | 94,7% |
| Rappel | 89,4% |
| F1-score | 91,1% |
| Exactitude (monde réel) | 93,0% |

**Facteurs de succès :**
1. Données d'entraînement diverses (modèles variés)
2. Framework léger (spaCy vs transformers lourds)
3. Métriques équilibrées (précision ≈ rappel)
4. Anonymisation préservant le contexte

#### 5.2 Réglage Presidio

**Source :** Notebook de Recherche Presidio 5

> "Le Notebook 5 dans presidio-research montre comment on peut configurer Presidio pour détecter les PII beaucoup plus précisément, et augmenter le F-score de ~30%."

---

## Analyse des Écarts

### Comparaison : Implémentation Actuelle vs Meilleures Pratiques

| Aspect | Meilleure Pratique | Implémentation Actuelle | Écart |
|---------|---------------|----------------------|-----|
| Ordre du pipeline | Regex → NER → Validation | NER → Post-traitement | **CRITIQUE** |
| Injection de bruit | 30% en entraînement | 0% | **CRITIQUE** |
| Couche CRF | Ajouter sur transformer | Non implémenté | MOYEN |
| Seuil de confiance | Filtrer par score | Non implémenté | MOYEN |
| Amélioration contextuelle | Basée sur le lemme | Partielle (regex) | FAIBLE |
| Validation checksum | DNI, IBAN, NSS | Implémenté | ✓ OK |
| Validation format | Modèles Regex | Implémenté | ✓ OK |

### Impact Estimé des Corrections

| Correction | Effort | Impact F1 Estimé |
|------------|----------|---------------------|
| Injection de bruit dans dataset | Faible | +10-15% sur OCR |
| Pipeline Regex-first | Moyen | +5-10% précision |
| Couche CRF | Élevé | +4-13% (littérature) |
| Seuil de confiance | Faible | Réduit FP 20-30% |

---

## Conclusions

### Principales Découvertes

1. **L'architecture hybride est supérieure** : Combiner regex (modèles structurés) avec NER (contextuel) surpasse les approches pures.

2. **L'ordre compte** : Regex AVANT NER, pas après. Presidio utilise cet ordre par conception.

3. **Le bruit à l'entraînement est critique** : 30% d'injection d'erreurs OCR améliore significativement la robustesse.

4. **La validation par checksum est standard** : Valider les identifiants structurés (DNI, IBAN) est une pratique universelle.

5. **CRF améliore la cohérence** : Ajouter une couche CRF sur le transformer empêche les séquences invalides.

### Recommandations

#### Priorité HAUTE (Implémenter Immédiatement)

1. **Injecter du bruit OCR dans le dataset v3**
   - 30% des échantillons avec erreurs simulées
   - Types : l↔I, 0↔O, espaces, accents manquants
   - Ré-entraîner le modèle

2. **Restructurer le pipeline**
   ```
   AVANT : Texte → NER → Post-traitement
   APRÈS : Texte → Prétraitement → Regex → NER → Validation → Filtre
   ```

#### Priorité MOYENNE

3. **Ajouter un seuil de confiance**
   - Filtrer les entités avec un score < 0,7
   - Calibrer avec l'ensemble de validation

4. **Évaluer la couche CRF**
   - Investiguer `transformers` + `pytorch-crf`
   - Benchmark contre le modèle actuel

#### Priorité FAIBLE

5. **Amélioration contextuelle avancée**
   - Implémenter LemmaContextAwareEnhancer
   - Gazetteers de contexte par type d'entité

---

## Références

1. **PMC12214779** - "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
   - URL : https://pmc.ncbi.nlm.nih.gov/articles/PMC12214779/
   - Année : 2025

2. **arXiv 2401.10825v3** - "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study"
   - URL : https://arxiv.org/html/2401.10825v3
   - Année : 2024 (mis à jour 2025)

3. **Microsoft Presidio** - Best Practices for Developing Recognizers
   - URL : https://microsoft.github.io/presidio/analyzer/developing_recognizers/
   - Année : 2024

4. **Presidio Research** - Evaluation Toolbox
   - URL : https://github.com/microsoft/presidio-research
   - Année : 2024

5. **Nature Scientific Reports** - "A hybrid rule-based NLP and machine learning approach"
   - URL : https://www.nature.com/articles/s41598-025-04971-9
   - Année : 2025

---

**Date :** 2026-01-16
**Version :** 1.0
