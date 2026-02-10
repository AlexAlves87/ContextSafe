# Recherche : Modèles BERT Légaux Multilingues

**Date :** 2026-01-29
**Auteur :** AlexAlves87
**Objectif :** Évaluer les modèles BERT légaux pour l'expansion multilingue de ContextSafe
**Langues Cibles :** Anglais, Français, Italien, Portugais, Allemand

---

## 1. Résumé Exécutif

Analyse des modèles BERT pré-entraînés dans des domaines juridiques pour déterminer la faisabilité de l'expansion multilingue du système NER-PII de ContextSafe.

### Modèles Évalués

| Modèle | Langue | Corpus | Taille | HuggingFace |
|--------|--------|--------|--------|-------------|
| Legal-BERT | Anglais | 12Go textes légaux | 110M params | `nlpaueb/legal-bert-base-uncased` |
| JuriBERT | Français | 6.3Go Légifrance | 110M params | `dascim/juribert-base` |
| Italian-Legal-BERT | Italien | 3.7Go droit civil | 110M params | `dlicari/Italian-Legal-BERT` |
| Legal-BERTimbau | Portugais | 30K docs légaux | 110M params | `rufimelo/Legal-BERTimbau-base` |
| Legal-XLM-R | Multilingue | 689Go (24 langues) | 355M params | `joelniklaus/legal-xlm-roberta-large` |

### Conclusion Principale

> **Legal-XLM-R est l'option la plus viable** pour une expansion multilingue immédiate.
> Il couvre 24 langues dont l'espagnol, avec un seul modèle.
> Pour une performance maximale par langue, envisager le fine-tuning de modèles monolingues.

---

## 2. Analyse par Modèle

### 2.1 Legal-BERT (Anglais)

**Source :** [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

| Aspect | Détail |
|--------|--------|
| **Architecture** | BERT-base (12 couches, 768 cachés, 110M params) |
| **Corpus** | 12Go textes légaux anglais |
| **Sources** | Législation, jurisprudence, contrats |
| **Variantes** | Général, CONTRACTS-, EURLEX-, ECHR- |
| **Licence** | CC BY-SA 4.0 |

**Points Forts :**
- Multiples variantes spécialisées (contrats, CEDH, EUR-Lex)
- Bien documenté et cité (~500 citations)
- Surpasse BERT vanilla dans les tâches légales

**Limitations :**
- Anglais seulement
- Pas de fine-tuning pour NER prêt à l'emploi

**Variantes Disponibles :**
```
nlpaueb/legal-bert-base-uncased      # Général
nlpaueb/legal-bert-small-uncased     # Plus rapide
casehold/legalbert                   # Corpus Harvard Law (37Go)
pile-of-law/legalbert-large-1.7M-2   # Pile of Law (256Go)
```

**Pertinence pour ContextSafe :** Moyenne. Utile si expansion vers des documents légaux en anglais (contrats internationaux, arbitrage).

---

### 2.2 JuriBERT (Français)

**Source :** [dascim/juribert-base](https://huggingface.co/dascim/juribert-base)

| Aspect | Détail |
|--------|--------|
| **Architecture** | BERT (tiny, mini, small, base) |
| **Corpus** | 6.3Go textes légaux français |
| **Sources** | Légifrance + Cour de Cassation |
| **Institution** | École Polytechnique + HEC Paris |
| **Papier** | [NLLP Workshop 2021](https://aclanthology.org/2021.nllp-1.9/) |

**Points Forts :**
- Entraîné à partir de zéro en français juridique (pas de fine-tuning)
- Inclut des documents de la Cour de Cassation (100K+ docs)
- Multiples tailles disponibles (tiny→base)

**Limitations :**
- Français seulement
- Pas de modèle NER pré-entraîné

**Variantes Disponibles :**
```
dascim/juribert-base    # 110M params
dascim/juribert-small   # Plus léger
dascim/juribert-mini    # Encore plus léger
dascim/juribert-tiny    # Minimal (pour edge)
```

**Pertinence pour ContextSafe :** Élevée pour le marché français. La France a des réglementations strictes en matière de confidentialité (CNIL + RGPD).

---

### 2.3 Italian-Legal-BERT (Italien)

**Source :** [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT)

| Aspect | Détail |
|--------|--------|
| **Architecture** | BERT-base italien + pré-entraînement additionnel |
| **Corpus** | 3.7Go Archivio Giurisprudenziale Nazionale |
| **Base** | bert-base-italian-xxl-cased |
| **Papier** | [KM4Law 2022](https://ceur-ws.org/Vol-3256/km4law3.pdf) |
| **Entraînement** | 4 époques, 8.4M étapes, V100 16Go |

**Points Forts :**
- Variante pour documents longs (LSG 16K tokens)
- Version distillée disponible (3x plus rapide)
- Évalué sur NER légal italien

**Limitations :**
- Corpus principalement droit civil
- Italien seulement

**Variantes Disponibles :**
```
dlicari/Italian-Legal-BERT          # Base
dlicari/Italian-Legal-BERT-SC       # À partir de zéro (6.6Go)
dlicari/lsg16k-Italian-Legal-BERT   # Contexte long (16K tokens)
```

**Pertinence pour ContextSafe :** Moyenne-élevée. L'Italie a un marché notarial significatif et des réglementations strictes en matière de confidentialité.

---

### 2.4 Legal-BERTimbau (Portugais)

**Source :** [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base)

| Aspect | Détail |
|--------|--------|
| **Architecture** | BERTimbau + fine-tuning légal |
| **Corpus** | 30K documents légaux portugais |
| **Base** | neuralmind/bert-base-portuguese-cased |
| **Variante TSDAE** | 400K docs, technique TSDAE |

**Points Forts :**
- Base solide (BERTimbau est SotA en portugais)
- Variante large disponible
- Version pour similarité de phrases (TSDAE)

**Limitations :**
- Corpus relativement petit (30K docs vs 6Go+ pour les autres)
- Principalement droit brésilien

**Variantes Disponibles :**
```
rufimelo/Legal-BERTimbau-base       # Base
rufimelo/Legal-BERTimbau-large      # Large
rufimelo/Legal-BERTimbau-large-TSDAE-v5  # Similarité de phrases
dominguesm/legal-bert-base-cased-ptbr    # Alternative (STF)
dominguesm/legal-bert-ner-base-cased-ptbr # AVEC fine-tuning NER
```

**Modèle NER Disponible :** `dominguesm/legal-bert-ner-base-cased-ptbr` a déjà un fine-tuning pour NER légal en portugais.

**Pertinence pour ContextSafe :** Élevée pour le marché lusophone (Brésil + Portugal). Le Brésil a la LGPD similaire au RGPD.

---

### 2.5 Legal-XLM-R / MultiLegalPile (Multilingue)

**Source :** [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large)

| Aspect | Détail |
|--------|--------|
| **Architecture** | XLM-RoBERTa large (355M params) |
| **Corpus** | MultiLegalPile : 689Go en 24 langues |
| **Langues** | DE, EN, ES, FR, IT, PT, NL, PL, RO, + 15 de plus |
| **Benchmark** | LEXTREME (11 datasets, 24 langues) |
| **Papier** | [ACL 2024](https://aclanthology.org/2024.acl-long.805/) |

**Langues Couvertes :**
```
Germanique : DE (allemand), EN (anglais), NL (néerlandais)
Roman :      ES (espagnol), FR (français), IT (italien), PT (portugais), RO (roumain)
Slave :      PL (polonais), BG (bulgare), CS (tchèque), SK (slovaque), SL (slovène), HR (croate)
Autres :     EL (grec), HU (hongrois), FI (finnois), LT (lituanien), LV (letton), GA (irlandais), MT (maltais)
```

**Points Forts :**
- **UN SEUL MODÈLE pour 24 langues**
- Inclut l'espagnol natif
- Tokenizer 128K BPE optimisé pour le juridique
- Variante Longformer pour documents longs
- État de l'art sur le benchmark LEXTREME

**Limitations :**
- Grand modèle (355M params vs 110M pour modèles de base)
- Performance légèrement inférieure au monolingue dans certains cas

**Variantes Disponibles :**
```
joelniklaus/legal-xlm-roberta-base   # Base (110M)
joelniklaus/legal-xlm-roberta-large  # Large (355M) - RECOMMANDÉ
joelniklaus/legal-longformer-base    # Contexte long
```

**Pertinence pour ContextSafe :** **TRÈS ÉLEVÉE**. Permet une expansion immédiate vers plusieurs langues européennes avec un seul modèle.

---

## 3. Comparatif

### 3.1 Performance Relative

| Modèle | NER Légal | Classification | Docs Longs | Multilingue |
|--------|-----------|----------------|------------|-------------|
| Legal-BERT (EN) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| JuriBERT (FR) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| Italian-Legal-BERT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| Legal-BERTimbau (PT) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ |
| **Legal-XLM-R** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 3.2 Ressources Informatiques

| Modèle | Paramètres | VRAM (inférence) | Latence* |
|--------|------------|------------------|----------|
| Legal-BERT base | 110M | ~2Go | ~50ms |
| JuriBERT base | 110M | ~2Go | ~50ms |
| Italian-Legal-BERT | 110M | ~2Go | ~50ms |
| Legal-BERTimbau base | 110M | ~2Go | ~50ms |
| **Legal-XLM-R base** | 110M | ~2Go | ~60ms |
| **Legal-XLM-R large** | 355M | ~4Go | ~120ms |

*Par document de 512 tokens sur GPU

### 3.3 Disponibilité NER Pré-entraîné

| Modèle | NER Fine-tuned Disponible |
|--------|---------------------------|
| Legal-BERT | ❌ Nécessite fine-tuning |
| JuriBERT | ❌ Nécessite fine-tuning |
| Italian-Legal-BERT | ❌ Nécessite fine-tuning |
| Legal-BERTimbau | ✅ `dominguesm/legal-bert-ner-base-cased-ptbr` |
| Legal-XLM-R | ❌ Nécessite fine-tuning |

---

## 4. Stratégie Recommandée pour ContextSafe

### 4.1 Option A : Modèle Unique Multilingue (Recommandé)

```
Legal-XLM-R large → Fine-tune NER avec données multilingues → Déploiement unique
```

**Avantages :**
- Un seul modèle pour toutes les langues
- Maintenance simplifiée
- Transfer learning entre les langues

**Inconvénients :**
- Performance ~5-10% inférieure au monolingue
- Modèle plus grand (355M vs 110M)

**Effort :** Moyen (1 fine-tuning, 1 déploiement)

### 4.2 Option B : Modèles Monolingues par Marché

```
ES: RoBERTalex (actuel)
EN: Legal-BERT → Fine-tune NER
FR: JuriBERT → Fine-tune NER
IT: Italian-Legal-BERT → Fine-tune NER
PT: legal-bert-ner-base-cased-ptbr (existe déjà)
DE: Legal-XLM-R (Allemand) → Fine-tune NER
```

**Avantages :**
- Performance maximale par langue
- Modèles plus petits

**Inconvénients :**
- 6 modèles à maintenir
- 6 datasets NER nécessaires
- Complexité de déploiement

**Effort :** Élevé (6 fine-tunings, 6 déploiements)

### 4.3 Option C : Hybride (Recommandé pour Échelle)

```
Phase 1 : Legal-XLM-R pour toutes les nouvelles langues
Phase 2 : Fine-tune monolingue pour marchés à haut volume
```

**Feuille de route :**
1. Déployer Legal-XLM-R pour EN, FR, IT, PT, DE
2. Surveiller les métriques par langue
3. Si langue X a >1000 utilisateurs/mois → fine-tune monolingue
4. Garder XLM-R comme secours

---

## 5. Datasets NER Légaux Multilingues

### 5.1 Disponibles

| Dataset | Langues | Entités | Taille | Source |
|---------|---------|---------|--------|--------|
| MAPA | 24 | PER, ORG, LOC, DATE | 50K+ | [LEXTREME](https://huggingface.co/datasets/joelito/lextreme) |
| LegalNER-BR | PT | 14 types | 10K+ | [HuggingFace](https://huggingface.co/dominguesm) |
| EUR-Lex NER | EN, 23 | ORG, LOC | 100K+ | EUR-Lex |

### 5.2 À Créer (si fine-tuning nécessaire)

Pour le fine-tuning monolingue, des datasets NER avec les 13 catégories PII de ContextSafe seraient nécessaires :

| Catégorie | Priorité | Difficulté |
|-----------|----------|------------|
| PERSON_NAME | Haute | Moyenne |
| DNI/ID_NACIONAL | Haute | Varie par pays |
| PHONE | Haute | Facile (regex + NER) |
| EMAIL | Haute | Facile (regex) |
| ADDRESS | Haute | Moyenne |
| ORGANIZATION | Haute | Moyenne |
| DATE | Moyenne | Facile |
| IBAN | Moyenne | Facile (regex) |
| LOCATION | Moyenne | Moyenne |

---

## 6. Conclusions

### 6.1 Découvertes Clés

1. **Legal-XLM-R est la meilleure option** pour l'expansion multilingue immédiate
   - 24 langues avec un seul modèle
   - Inclut l'espagnol (valide la compatibilité avec ContextSafe actuel)
   - État de l'art sur le benchmark LEXTREME

2. **Les modèles monolingues surpassent les multilingues** de ~5-10%
   - À considérer pour les marchés à haut volume
   - Le portugais a déjà un NER pré-entraîné

3. **Le corpus d'entraînement compte**
   - Italian-Legal-BERT a une version contexte long (16K tokens)
   - Legal-BERTimbau a une variante TSDAE pour la similarité

4. **Tous nécessitent un fine-tuning** pour les 13 catégories PII
   - Sauf `legal-bert-ner-base-cased-ptbr` (Portugais)

### 6.2 Recommandation Finale

| Scénario | Recommandation |
|----------|----------------|
| MVP multilingue rapide | Legal-XLM-R large |
| Max performance EN | Legal-BERT + Fine-tune |
| Max performance FR | JuriBERT + Fine-tune |
| Max performance IT | Italian-Legal-BERT + Fine-tune |
| Max performance PT | `legal-bert-ner-base-cased-ptbr` (prêt) |
| Max performance DE | Legal-XLM-R (Allemand) + Fine-tune |

### 6.3 Prochaines Étapes

| Priorité | Tâche | Effort |
|----------|-------|--------|
| 1 | Évaluer Legal-XLM-R sur dataset espagnol actuel | 2-4h |
| 2 | Créer benchmark multilingue (EN, FR, IT, PT, DE) | 8-16h |
| 3 | Fine-tune Legal-XLM-R pour 13 catégories PII | 16-24h |
| 4 | Comparer vs modèles monolingues | 8-16h |

---

## 7. Références

### 7.1 Papiers

1. Chalkidis et al. (2020). "LEGAL-BERT: The Muppets straight out of Law School". [arXiv:2010.02559](https://arxiv.org/abs/2010.02559)
2. Douka et al. (2021). "JuriBERT: A Masked-Language Model Adaptation for French Legal Text". [ACL Anthology](https://aclanthology.org/2021.nllp-1.9/)
3. Licari & Comandè (2022). "ITALIAN-LEGAL-BERT: A Pre-trained Transformer Language Model for Italian Law". [CEUR-WS](https://ceur-ws.org/Vol-3256/km4law3.pdf)
4. Niklaus et al. (2023). "MultiLegalPile: A 689GB Multilingual Legal Corpus". [ACL 2024](https://aclanthology.org/2024.acl-long.805/)
5. Niklaus et al. (2023). "LEXTREME: A Multi-Lingual and Multi-Task Benchmark for the Legal Domain". [arXiv:2301.13126](https://arxiv.org/abs/2301.13126)

### 7.2 Modèles HuggingFace

| Modèle | URL |
|--------|-----|
| Legal-BERT | [nlpaueb/legal-bert-base-uncased](https://huggingface.co/nlpaueb/legal-bert-base-uncased) |
| JuriBERT | [dascim/juribert-base](https://huggingface.co/dascim/juribert-base) |
| Italian-Legal-BERT | [dlicari/Italian-Legal-BERT](https://huggingface.co/dlicari/Italian-Legal-BERT) |
| Legal-BERTimbau | [rufimelo/Legal-BERTimbau-base](https://huggingface.co/rufimelo/Legal-BERTimbau-base) |
| Legal-XLM-R | [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large) |
| Legal-BERT NER PT | [dominguesm/legal-bert-ner-base-cased-ptbr](https://huggingface.co/dominguesm/legal-bert-ner-base-cased-ptbr) |

### 7.3 Datasets

| Dataset | URL |
|---------|-----|
| LEXTREME | [joelito/lextreme](https://huggingface.co/datasets/joelito/lextreme) |
| MultiLegalPile | [joelito/Multi_Legal_Pile](https://huggingface.co/datasets/joelito/Multi_Legal_Pile) |

---

**Temps de recherche :** ~45 min
**Généré par :** AlexAlves87
**Date :** 2026-01-29
