# Recherche : Meilleures Pratiques ML 2025-2026 pour NER-PII Légal

**Date :** 31/01/2026
**Auteur :** AlexAlves87
**Objectif :** Identifier les techniques de pointe applicables au pipeline NER-PII de ContextSafe
**Portée :** Littérature de premier plan (ICLR, EMNLP, NeurIPS, NAACL, Nature) publiée en 2025-2026

---

## 1. Résumé Exécutif

Revue systématique de la littérature récente (2025-2026) en apprentissage automatique appliqué à la Reconnaissance d'Entités Nommées (NER) et à la détection de PII. **8 avancées significatives** sont identifiées par rapport aux pratiques documentées dans notre rapport précédent (2026-01-30_investigacion_finetuning_legal_xlm_r), avec un impact direct sur la stratégie d'entraînement de Legal-XLM-RoBERTa pour ContextSafe.

### Principales Découvertes

| # | Technique | Source | Impact pour ContextSafe |
|---|-----------|--------|-------------------------|
| 1 | LoRA/QLoRA avec rang élevé (128-256) sur toutes les couches | Unsloth, COLING 2025 | Réduit la VRAM de 16GB à ~4GB sans perte de F1 |
| 2 | RandLoRA (full-rank PEFT) | ICLR 2025 | Élimine le plateau de LoRA standard |
| 3 | Knowledge Distillation multi-perspective | IGI Global 2025 | +2.5-5.8% F1 avec données limitées |
| 4 | Génération synthétique LLM pour NER | EMNLP 2025 | Bootstrap pour langues sans corpus annoté |
| 5 | GLiNER zero-shot PII | NAACL 2024 + mises à jour 2025 | Baseline 81% F1 sans entraînement |
| 6 | NER hybride (transformer + règles) | Nature Sci. Reports 2025 | 94.7% précision dans documents financiers |
| 7 | RECAP (regex + LLM contextuel) | NeurIPS 2025 | +82% sur NER fine-tuned, +17% sur zero-shot |
| 8 | DAPT sélectif (non universel) | ICLR 2025 | DAPT n'améliore pas toujours ; nécessite évaluation préalable |

### Diagnostic : État Actuel vs État de l'Art

| Capacité | ContextSafe Actuel | État de l'Art 2026 | Écart |
|----------|--------------------|--------------------|-------|
| Fine-tuning | Full FT planifié | LoRA/RandLoRA (PEFT) | **Élevé** |
| Données d'entraînnement | Gold labels uniquement | Gold + synthétique (LLM) | **Élevé** |
| Pipeline NER | Hybride (regex+ML) | RECAP (regex+LLM contextuel) | Moyen |
| Zero-shot baseline | Non établi | GLiNER ~81% F1 | **Élevé** |
| DAPT | Planifié universel | Sélectif (évaluer avant) | Moyen |
| Inférence | ONNX INT8 planifié | LoRA adapters + quantification | Faible |
| Évaluation | SemEval entity-level | + adversarial + cross-lingual | Moyen |
| Modèle légal espagnol | Pas de baseline | MEL (XLM-R-large, 82% F1) | **Élevé** |

---

## 2. Méthodologie de Revue

### 2.1 Critères d'Inclusion

| Critère | Valeur |
|---------|--------|
| Période | Janvier 2025 - Février 2026 |
| Venues | ICLR, EMNLP, NeurIPS, NAACL, ACL, Nature, ArXiv (pré-print avec citations) |
| Pertinence | NER, PII, PEFT, DAPT, juridique NLP, multilingue |
| Langues | Multilingue (avec accent sur l'espagnol) |

### 2.2 Recherches Effectuées

1. "LoRA QLoRA NER fine-tuning 2025 2026 best practices"
2. "knowledge distillation LLM small model NER 2025"
3. "ICL-APT in-context learning augmented pretraining 2025"
4. "Continual Pre-Training is (not) What You Need 2025 legal"
5. "GLiNER zero-shot NER PII detection 2025 2026"
6. "EMNLP 2025 LLM data generation NER multilingual"
7. "hybrid NER transformer rules PII detection 2025"
8. "RandLoRA ICLR 2025 full rank"
9. "MEL legal Spanish language model 2025"

---

## 3. Résultats par Domaine Thématique

### 3.1 Parameter-Efficient Fine-Tuning (PEFT)

#### 3.1.1 LoRA/QLoRA : Configurations Optimales 2025-2026

La littérature récente consolide les meilleures pratiques pour LoRA appliqué au NER :

| Hyperparamètre | Valeur Recommandée | Source |
|----------------|--------------------|--------|
| Rank (r) | 128-256 | Unsloth Docs, Medical NER studies |
| Alpha (α) | 2×r (256-512) | Heuristique validée empiriquement |
| Target modules | Attention **+ MLP** (toutes les couches) | Databricks, Lightning AI |
| Learning rate | 2e-4 (début), plage 5e-6 à 2e-4 | Unsloth, Medium/QuarkAndCode |
| Epochs | 1-3 (risque overfitting >3) | Consensus multiples sources |
| Dropout | 0.05 (domaines spécialisés) | Medical NER studies |

**Preuve empirique récente :**

| Papier | Modèle | Tâche | F1 | Venue |
|--------|--------|-------|----|-------|
| B2NER | LoRA adapters ≤50MB | NER universel (15 datasets, 6 langues) | +6.8-12.0 F1 vs GPT-4 | COLING 2025 |
| LLaMA-3-8B Financial NER | LoRA r=128 | NER financier | 0.894 micro-F1 | ArXiv Jan 2026 |
| Military IE | GRPO + LoRA | Extraction d'Information | +48.8% F1 absolu | 2025 |

**Décision LoRA vs QLoRA :**
- **LoRA** : Vitesse légèrement supérieure, ~0.5% plus précis, 4× plus de VRAM
- **QLoRA** : Utiliser quand VRAM < 8GB ou modèle > 1B paramètres
- **Pour Legal-XLM-RoBERTa-base (184M)** : LoRA est viable sur RTX 5060 Ti 16GB

#### 3.1.2 RandLoRA : PEFT à Rang Complet

**Papier :** "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models"
**Venue :** ICLR 2025 (ArXiv: 2502.00987)

**Problème résolu :**
LoRA standard produit des mises à jour de faible rang, ce qui limite la capacité de représentation. Augmenter le rang (r) ne comble pas l'écart avec le full fine-tuning : il existe un *plateau* de performance.

**Innovation :**
- Génère des matrices aléatoires de faible rang **non entraînables** (bases linéairement indépendantes)
- Apprend uniquement des **coefficients d'échelle diagonaux**
- La combinaison linéaire produit des mises à jour de **rang complet**
- Même quantité de paramètres entraînables que LoRA, mais sans restriction de rang

**Résultats :**

| Modèle | Tâche | LoRA | RandLoRA | Full FT |
|--------|-------|------|----------|---------|
| DinoV2 | Vision | 85.2 | 87.1 | 87.4 |
| CLIP | Vision-langage | 78.6 | 81.3 | 82.0 |
| Llama3-8B | Raisonnement | 71.2 | 73.8 | 74.1 |

**Implication :** RandLoRA comble >90% de l'écart LoRA→Full FT avec les mêmes paramètres entraînables.

### 3.2 Knowledge Distillation (LLM → Petit Modèle)

#### 3.2.1 Distillation Multi-Perspective pour NER

**Papier :** "Multi-Perspective Knowledge Distillation of LLM for NER"
**Source :** IGI Global Scientific Publishing, 2025

**Pipeline :**
1. **Teacher :** Qwen14B (14B paramètres)
2. **Génération :** Chain-of-Thought (CoT) pour générer un raisonnement intermédiaire sur les entités
3. **Alignement :** Connaissance multi-perspective (type d'entité, contexte, limites)
4. **Student :** Petit modèle NER avec DoRA (variante de LoRA)

**Résultats sur état de l'art :**

| Métrique | Amélioration |
|----------|--------------|
| Précision | +3.46% |
| Rappel | +5.79% |
| F1-score | +2.54% |

**Capacité supplémentaire :** Performance forte en few-shot (données limitées).

#### 3.2.2 Application à ContextSafe

Pipeline proposé :
```
GPT-4 / Llama-3-70B (teacher)
    ↓ Génère annotations PII avec raisonnement CoT
    ↓ Sur textes légaux espagnols non annotés
Legal-XLM-RoBERTa-base (student)
    ↓ Fine-tune avec DoRA/LoRA
    ↓ Utilisant données générées + gold labels
Modèle PII déployable (~400MB ONNX)
```

### 3.3 Génération Synthétique de Données avec LLMs

#### 3.3.1 Évaluation Rigoureuse (EMNLP 2025)

**Papier :** "A Rigorous Evaluation of LLM Data Generation Strategies for NER"
**Venue :** EMNLP 2025 Main Conference (Paper ID: 2025.emnlp-main.418)

**Conception expérimentale :**
- **Langues :** 11 (incluant multilingue)
- **Tâches :** 3 différentes
- **LLMs générateurs :** 4 modèles
- **Modèles downstream :** 10 (fine-tuned XLM-R)
- **Métrique :** F1 moyen gold vs artificiel

**Découvertes clés :**

| Découverte | Preuve |
|------------|--------|
| Qualité > Quantité | Datasets petits, propres et cohérents surpassent datasets grands et bruités |
| Format importe | JSONL cohérent est critique pour la performance |
| Efficace pour low-resource | Données synthétiques viables pour langues sans corpus annoté |
| Comparable au gold | Dans certaines langues/tâches, les données synthétiques atteignent 90-95% de la performance gold |

#### 3.3.2 Cross-lingual NER Zero-shot (EMNLP 2025)

**Papier :** "Zero-shot Cross-lingual NER via Mitigating Language Difference: An Entity-aligned Translation Perspective"
**Venue :** EMNLP 2025

**Technique :** Traduction alignée sur les entités pour le transfert multilingue. Pertinent pour étendre ContextSafe à de nouvelles langues à partir du modèle espagnol.

### 3.4 GLiNER : Zero-Shot NER pour PII

**Papier :** "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer"
**Venue :** NAACL 2024 (modèles PII mis à jour septembre 2025, collaboration Wordcab)

**Architecture :**
- Encodeur bidirectionnel (BiLM)
- Input : prompts de type d'entité + texte
- Output : extraction parallèle d'entités (avantage sur génération séquentielle des LLMs)
- Ne nécessite pas de catégories prédéfinies : entités spécifiées à l'exécution

**Modèles PII disponibles (2025) :**

| Modèle | Taille | F1 |
|--------|--------|----|
| gliner-pii-edge-v1.0 | ~100MB | ~75% |
| gliner-pii-small-v1.0 | ~200MB | ~78% |
| gliner-pii-base-v1.0 | ~440MB | **80.99%** |
| gliner-pii-large-v1.0 | ~1.3GB | ~80% |

**Intégration existante :** GLiNER s'intègre avec Microsoft Presidio (que ContextSafe utilise déjà).

**Pertinence :**
- **Baseline immédiate :** 81% F1 sans entraînement, contre laquelle mesurer notre modèle fine-tuned
- **Ensemble :** Utiliser GLiNER pour catégories PII rares où il n'y a pas de données d'entraînement
- **Validation croisée :** Comparer prédictions GLiNER vs Legal-XLM-R pour détecter erreurs

### 3.5 Approches Hybrides (Transformer + Règles)

#### 3.5.1 Hybrid NER pour PII dans Documents Financiers

**Papier :** "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
**Venue :** Nature Scientific Reports, 2025 (DOI: 10.1038/s41598-025-04971-9)

**Résultats :**

| Métrique | Dataset Synthétique | Documents Réels |
|----------|---------------------|-----------------|
| Précision | **94.7%** | ~93% |
| Rappel | 89.4% | ~93% |
| F1-score | 91.1% | ~93% |

**Architecture :** Règles NLP + ML + NER custom, évolutif.

#### 3.5.2 RECAP : Regex + LLM Contextuel

**Papier :** Présenté à NeurIPS 2025
**Méthodologie :** Regex déterministe + LLMs context-aware pour PII multilingue

**Résultats comparatifs :**

| Comparaison | Amélioration RECAP |
|-------------|--------------------|
| vs NER fine-tuned | **+82% F1 pondéré** |
| vs zero-shot LLMs | **+17% F1 pondéré** |

**Benchmark :** nervaluate (évaluation au niveau entité)

**Implication pour ContextSafe :** Notre pipeline actuel (Regex + Presidio + RoBERTa) suit déjà ce modèle hybride. RECAP valide que cette architecture est la plus efficace selon les preuves 2025.

### 3.6 Domain Adaptive Pre-Training (DAPT) : Revue Critique

#### 3.6.1 DAPT N'est Pas Universel

**Papier :** "Continual Pre-Training is (not) What You Need in Domain Adaptation"
**Venue :** ICLR 2025

**Conclusions clés :**

| Scénario | DAPT Aide ? | Preuve |
|----------|-------------|--------|
| Vocabulaire spécialisé (légal, médical) | **Oui** | Familiarise avec le style légal |
| Raisonnement logique (droit civil) | **Oui** | Améliore compréhension des relations |
| Tâches avec données abondantes | **Pas nécessairement** | Fine-tuning direct peut suffire |
| Sans mitigation de catastrophe | **Préjudiciable** | Catastrophic forgetting dégrade général |

**Mitigation recommandée :**
- Couches adapter / LoRA pendant DAPT (pas de full fine-tuning du backbone)
- Unfreezing progressif
- Évaluer AVANT et APRÈS DAPT sur benchmark NER-PII

#### 3.6.2 ICL-APT : Alternative Efficace

**Concept :** In-Context Learning Augmented Pre-Training

**Pipeline :**
1. Échantillonner textes du corpus cible
2. Récupérer documents similaires du domaine (récupération sémantique)
3. Augmenter contexte avec définitions, abréviations, terminologie
4. Continuer pré-entraînement avec MLM sur contexte augmenté

**Avantage :** Plus efficace avec corpus limité. Ne nécessite pas des millions de documents comme DAPT traditionnel.

**Application :** Pour chaque document légal espagnol, récupérer jugements similaires + ajouter définitions de catégories PII comme contexte de pré-entraînement.

### 3.7 Modèles Légaux Espagnols (Baselines 2025)

#### 3.7.1 MEL (Modelo de Español Legal)

**Papier :** "MEL: Legal Spanish language model"
**Date :** Janvier 2025 (ArXiv: 2501.16011)

| Aspect | Détail |
|--------|--------|
| Base | XLM-RoBERTa-large |
| Données entraînement | BOE (Journal Officiel), textes congrès |
| Tâches | Classification légale, NER |
| F1 macro | ~0.82 (15 labels) |
| Comparaison | Surpasse xlm-roberta-large, legal-xlm-roberta-large, RoBERTalex |

#### 3.7.2 Corpus 3CEL

**Papier :** "3CEL: a Corpus of Legal Spanish Contract Clauses"
**Date :** Janvier 2025 (ArXiv: 2501.15990)

Corpus de clauses contractuelles espagnoles avec annotations. Potentiellement utile comme données d'entraînement ou d'évaluation.

---

## 4. Lectures Préalables Obligatoires

> **IMPORTANT :** Avant d'exécuter toute phase du plan, le modèle doit lire ces documents dans l'ordre indiqué pour comprendre le contexte complet du projet, les décisions prises et l'état actuel.

### 4.1 Niveau 0 : Identité et Règles du Projet

| # | Fichier | Objectif | Obligatoire |
|---|---------|----------|-------------|
| 0.1 | `ml/README.md` | Règles opérationnelles, structure fichiers, workflow | **Oui** |
| 0.2 | `README.md` (racine projet) | Architecture hexagonale, domaine ContextSafe, pipeline NER, niveaux anonymisation | **Oui** |

### 4.2 Niveau 1 : Histoire du Cycle ML (lire dans l'ordre chronologique)

Ces documents racontent l'évolution complète du modèle NER v2, du baseline à l'état actuel. Sans eux, on ne comprend pas pourquoi certaines décisions ont été prises.

| # | Fichier | Contenu Clé |
|---|---------|-------------|
| 1.1 | `docs/reports/2026-01-15_estado_proyecto_ner.md` | État initial projet NER, modèle v1 vs v2 |
| 1.2 | `docs/reports/2026-01-16_investigacion_pipeline_pii.md` | Recherche pipelines PII existants |
| 1.3 | `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Décision architecturale : pipeline hybride (Regex+ML) |
| 1.4 | `docs/reports/2026-01-28_investigacion_estandares_evaluacion_ner.md` | Adoption SemEval 2013 Task 9 (COR/INC/PAR/MIS/SPU) |
| 1.5 | `docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | **ESSENTIEL** - Cycle ML complet : 5 éléments intégrés, métriques finales (F1 0.788), leçons apprises |

### 4.3 Niveau 2 : Les 5 Éléments du Pipeline (détail technique)

Chaque élément documente une amélioration concrète intégrée dans `ner_predictor.py`. Lire si besoin de comprendre ou modifier le pipeline.

| # | Fichier | Élément | Impact |
|---|---------|---------|--------|
| 2.1 | `docs/reports/2026-02-04_text_normalizer_impacto.md` | Elem.1 : Normalisation texte | Bruit OCR → texte propre |
| 2.2 | `docs/reports/2026-02-04_checksum_validators_standalone.md` | Elem.2 : Validation checksums | DNI, IBAN, NSS avec vérification mathématique |
| 2.3 | `docs/reports/2026-02-05_regex_patterns_standalone.md` | Elem.3 : Patterns regex espagnols | Plaques, CP, téléphones |
| 2.4 | `docs/reports/2026-02-05_date_patterns_integration.md` | Elem.4 : Dates textuelles | "12 de enero de 2024" |
| 2.5 | `docs/reports/2026-02-06_boundary_refinement_integration.md` | Elem.5 : Raffinement limites | PAR→COR (16 partiels corrigés) |

### 4.4 Niveau 3 : Investigations pour Phase Suivante

Ces rapports fondent les décisions du plan de fine-tuning de Legal-XLM-RoBERTa.

| # | Fichier | Contenu Clé |
|---|---------|-------------|
| 3.1 | `docs/reports/2026-01-29_investigacion_modelos_legales_multilingues.md` | Survey modèles légaux : Legal-BERT, JuriBERT, Legal-XLM-R. Justification de Legal-XLM-RoBERTa-base |
| 3.2 | `docs/reports/2026-01-30_investigacion_finetuning_legal_xlm_r.md` | Stratégies DAPT, mDAPT, span masking, hyperparamètres. Plan original de fine-tuning |
| 3.3 | **Ce document** (`2026-01-31_mejores_practicas_ml_2026.md`) | Mise à jour 2025-2026 : LoRA, RandLoRA, données synthétiques, GLiNER, DAPT sélectif. **Plan mis à jour** |

### 4.5 Niveau 4 : Conceptions en Attente d'Implémentation

| # | Fichier | Contenu Clé |
|---|---------|-------------|
| 4.1 | `docs/plans/2026-02-04_uncertainty_queue_design.md` | Conception Human-in-the-Loop : zones confiance (HIGH/UNCERTAIN/LOW), file révision, blocage export. **Ne pas implémenter en ML**, transféré au projet principal |

### 4.6 Niveau 5 : Code Actuel (état du pipeline)

| # | Fichier | Objectif |
|---|---------|----------|
| 5.1 | `scripts/inference/ner_predictor.py` | **Pipeline NER complet** - Intègre les 5 éléments, prédicteur principal |
| 5.2 | `scripts/inference/text_normalizer.py` | Normalisation texte (Elem.1) |
| 5.3 | `scripts/inference/entity_validator.py` | Validation checksum (Elem.2) |
| 5.4 | `scripts/preprocess/boundary_refinement.py` | Raffinement limites (Elem.5) |
| 5.5 | `scripts/preprocess/checksum_validators.py` | Validateurs : DNI, IBAN, NSS, cartes |
| 5.6 | `scripts/evaluate/test_ner_predictor_adversarial_v2.py` | Test set adversarial (35 cas, évaluation SemEval) |
| 5.7 | `scripts/download_legal_xlm_roberta.py` | Script téléchargement modèle base |

### 4.7 Niveau 6 : Modèles Disponibles

| # | Chemin | État |
|---|--------|------|
| 6.1 | `models/checkpoints/roberta-base-bne-capitel-ner/` | Modèle actuel (RoBERTa-BNE CAPITEL NER) |
| 6.2 | `models/legal_ner_v1/` | Modèle v1 (déprécié) |
| 6.3 | `models/legal_ner_v2/` | Modèle v2 actuel (F1 0.788 avec pipeline complet) |
| 6.4 | `models/pretrained/legal-xlm-roberta-base/` | **Legal-XLM-RoBERTa-base téléchargé** (184M params, 128K vocab, 1.48GB) |

### 4.8 Ordre de Lecture Recommandé par Tâche

| Si le modèle va... | Lire niveaux |
|--------------------|--------------|
| Continuer le plan de fine-tuning | 0 → 1.5 → 3.1 → 3.2 → 3.3 (ce doc) |
| Modifier le pipeline NER | 0 → 1.5 → 2.x (élément pertinent) → 5.1 |
| Évaluer baselines (GLiNER, MEL) | 0 → 1.5 → 3.3 (section 4.2 Phase 1) → 5.6 |
| Générer données synthétiques | 0 → 1.5 → 3.3 (section 3.3) |
| Implémenter DAPT | 0 → 3.1 → 3.2 → 3.3 (sections 3.6 + 4.2 Phase 4) |
| Implémenter Uncertainty Queue | 0 → 4.1 (transférer au projet principal) |

### 4.9 État Actuel du Projet (Snapshot 04 Fév 2026)

```
Modèle actuel :    legal_ner_v2 (RoBERTa-BNE + 5 éléments pipeline)
F1 strict :        0.788 (SemEval entity-level, test adversarial 35 cas)
Pass rate :        60.0% (lenient 71.4%)
Modèle téléchargé : Legal-XLM-RoBERTa-base (184M params, prêt pour fine-tuning)
Prochaine étape :   Établir baselines (GLiNER + MEL) → LoRA fine-tuning
```

---

## 5. Analyse des Écarts et Recommandations

### 5.1 Ce Qui Nous Manque (Gap Analysis)

| # | Écart Identifié | Priorité | Technique Recommandée | Source |
|---|-----------------|----------|-----------------------|--------|
| **G1** | Pas de baseline zero-shot | **Critique** | Évaluer GLiNER-PII-base sur notre test set | NAACL 2024 |
| **G2** | Fine-tuning planifié comme Full FT | **Élevé** | Migrer vers LoRA r=128, α=256, toutes couches | COLING 2025, ICLR 2025 |
| **G3** | Gold labels uniquement pour entraînement | **Élevé** | Générer données synthétiques avec LLM (EMNLP 2025) | EMNLP 2025 |
| **G4** | Pas de baseline MEL | **Élevé** | Évaluer MEL sur notre test set | ArXiv Jan 2025 |
| **G5** | DAPT planifié sans évaluation pré | **Moyen** | Évaluer NER avant/après DAPT, utiliser LoRA | ICLR 2025 |
| **G6** | RandLoRA non utilisé | **Moyen** | Si plateau LoRA, migrer vers RandLoRA | ICLR 2025 |
| **G7** | Pas de distillation de connaissances | **Moyen** | Pipeline teacher(LLM)→student(XLM-R) avec CoT | IGI Global 2025 |
| **G8** | Pipeline hybride sans validation formelle | **Faible** | Benchmark RECAP pour valider architecture | NeurIPS 2025 |

### 5.2 Recommandations Ordonnées

#### Phase 1 : Établir Baselines (Immédiat)

1. **Évaluer GLiNER-PII-base** sur notre test set adversarial
   - F1 attendu : ~81% (benchmark publié)
   - S'il bat notre modèle actuel (F1 0.788) : prioriser intégration
   - Sinon : confirme que notre pipeline est compétitif

2. **Évaluer MEL** (si disponible) sur notre test set
   - F1 attendu : ~82% (benchmark publié avec 15 labels)
   - Établit benchmark légal espagnol

#### Phase 2 : Fine-tuning avec PEFT (Prochain Cycle)

3. **Migrer de Full FT à LoRA**
   - Config : r=128, α=256, target=all_layers, lr=2e-4, epochs=3, dropout=0.05
   - Hardware : RTX 5060 Ti 16GB VRAM est suffisant
   - Taille adapter : ~50MB (vs ~700MB modèle complet)

4. **Si plateau avec LoRA → RandLoRA**
   - Mêmes paramètres entraînables, rang complet
   - Comble >90% de l'écart LoRA→Full FT

#### Phase 3 : Augmentation de Données (Parallèle à Phase 2)

5. **Générer données synthétiques PII avec LLM**
   - Teacher : GPT-4 ou Llama-3-70B
   - Format : CoNLL/JSONL cohérent
   - Focus : catégories avec peu d'exemples (IBAN, NSS, MATRICULA)
   - Valider : comparer F1 avec gold vs gold+synthétique

6. **Knowledge distillation (optionnel)**
   - Seulement si données limitées persistent après augmentation
   - Pipeline : LLM génère raisonnement CoT → student apprend

#### Phase 4 : DAPT Sélectif (Après Phase 2-3)

7. **Évaluer NER AVANT DAPT** (baseline)
8. **DAPT avec LoRA** (pas full backbone FT) sur corpus BOE
9. **Évaluer NER APRÈS DAPT** (comparer)
10. **Décision basée sur preuve :** si DAPT n'améliore pas >2% F1, écarter

---

## 6. Comparaison : Plan Original vs Plan Mis à Jour

| Aspect | Plan Original (Fév 2026) | Plan Mis à Jour (Post-Revue) |
|--------|--------------------------|------------------------------|
| Fine-tuning | Full FT | **LoRA r=128 / RandLoRA** |
| Données | Gold labels manuels uniquement | **Gold + synthétique LLM** |
| DAPT | Universel, 1-2 époques | **Sélectif, évaluer avant/après** |
| Baseline | Aucun | **GLiNER 81% + MEL 82%** |
| Distillation | Non considérée | **Optionnel (si données limitées)** |
| Évaluation | SemEval entity-level | **+ adversarial + cross-lingual** |
| Taille adapter | ~700MB (modèle complet) | **~50MB (LoRA adapter)** |
| VRAM requise | ~8GB (Full FT petit batch) | **~4GB (LoRA)** |

---

## 7. Tableau de Preuves

| Papier | Venue | Année | Technique | Métrique Clé | URL |
|--------|-------|-------|-----------|--------------|-----|
| B2NER | COLING | 2025 | LoRA NER universel | +6.8-12.0 F1 vs GPT-4 | github.com/UmeanNever/B2NER |
| RandLoRA | ICLR | 2025 | Full-rank PEFT | >90% écart LoRA→FT comblé | arxiv.org/abs/2502.00987 |
| Multi-Perspective KD | IGI Global | 2025 | Distillation NER | +2.54% F1, +5.79% Rappel | igi-global.com/gateway/article/372672 |
| LLM Data Gen for NER | EMNLP | 2025 | Données synthétiques | 90-95% performance gold | aclanthology.org/2025.emnlp-main.418 |
| GLiNER PII | NAACL+updates | 2024-2025 | Zero-shot PII | 80.99% F1 | huggingface.co/knowledgator/gliner-pii-base-v1.0 |
| Hybrid PII Financial | Nature Sci.Rep | 2025 | Règles+ML PII | 94.7% précision | doi.org/10.1038/s41598-025-04971-9 |
| RECAP | NeurIPS | 2025 | Regex+LLM PII | +82% vs NER fine-tuned | neurips.cc/virtual/2025/122402 |
| CPT is (not) WYNG | ICLR | 2025 | DAPT sélectif | N'améliore pas uniformément | openreview.net/pdf?id=rpi9ARgvXc |
| MEL | ArXiv | 2025 | Espagnol légal | 82% F1 macro (15 labels) | arxiv.org/html/2501.16011 |
| 3CEL | ArXiv | 2025 | Corpus Espagnol légal | Benchmark clauses | arxiv.org/html/2501.15990 |
| Financial NER LLaMA-3 | ArXiv | 2026 | LoRA NER Financier | 0.894 micro-F1 | arxiv.org/abs/2601.10043 |

---

## 8. Conclusions

### 8.1 Changements de Paradigme 2025-2026

1. **PEFT remplace Full Fine-Tuning :** LoRA/RandLoRA est maintenant le standard pour modèles ≤1B paramètres. Full FT n'est justifié que si LoRA ne converge pas (rare dans modèles base).

2. **Données Synthétiques LLM sont viables :** EMNLP 2025 démontre que les données générées par LLM peuvent atteindre 90-95% de la performance des données gold pour NER multilingue. Cela résout le goulot d'étranglement de l'annotation manuelle.

3. **DAPT n'est pas un dogme :** ICLR 2025 démontre que DAPT peut ne pas améliorer et même nuire si catastrophic forgetting n'est pas mitigé. Toujours évaluer avant et après.

4. **Hybride > ML Pur :** Nature et NeurIPS 2025 confirment que les approches hybrides (règles + ML) surpassent le ML pur pour les PII. ContextSafe suit déjà cette architecture.

5. **Zero-shot NER est compétitif :** GLiNER atteint 81% F1 sans entraînement. Tout modèle fine-tuned doit battre significativement ce seuil pour justifier l'effort.

### 8.2 Impact sur ContextSafe

Le pipeline actuel de ContextSafe (Regex + Presidio + RoBERTa) est **architecturalement aligné** avec les preuves 2025-2026. Les principaux écarts sont opérationnels :

- **Ne pas utiliser Full FT** → LoRA/RandLoRA
- **Ne pas dépendre uniquement des gold labels** → données synthétiques LLM
- **Établir baselines** → GLiNER + MEL avant fine-tuning
- **DAPT sélectif** → évaluer, ne pas supposer

### 8.3 Travaux Futurs

| Tâche | Priorité | Dépendance |
|-------|----------|------------|
| Évaluer GLiNER-PII sur test set ContextSafe | Critique | Aucune |
| Préparer script LoRA fine-tuning (r=128, α=256) | Haute | Modèle téléchargé (terminé) |
| Générer données synthétiques PII avec LLM | Haute | Définir catégories cibles |
| Évaluer MEL sur test set ContextSafe | Haute | Télécharger modèle MEL |
| DAPT sélectif avec évaluation pré/post | Moyenne | Corpus BOE disponible |
| Implémenter RandLoRA si plateau | Moyenne | Résultats LoRA |
| Pipeline distillation connaissances | Basse | Seulement si données insuffisantes |

---

## 9. Références

1. UmeanNever et al. "B2NER: Beyond Boundaries: Learning Universal Entity Taxonomy across Datasets and Languages for Open Named Entity Recognition." COLING 2025. GitHub: github.com/UmeanNever/B2NER

2. Koo et al. "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models." ICLR 2025. ArXiv: 2502.00987

3. "Multi-Perspective Knowledge Distillation of LLM for Named Entity Recognition." IGI Global Scientific Publishing, 2025. igi-global.com/gateway/article/372672

4. "A Rigorous Evaluation of LLM Data Generation Strategies for NER." EMNLP 2025 Main Conference. Paper ID: 2025.emnlp-main.418

5. Urchade Zaratiana et al. "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer." NAACL 2024. Modèles PII : knowledgator/gliner-pii-base-v1.0 (mis à jour Sep 2025).

6. "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents." Nature Scientific Reports, 2025. DOI: 10.1038/s41598-025-04971-9

7. "RECAP: Deterministic Regex + Context-Aware LLMs for Multilingual PII Detection." NeurIPS 2025. neurips.cc/virtual/2025/122402

8. "Continual Pre-Training is (not) What You Need in Domain Adaptation." ICLR 2025. openreview.net/pdf?id=rpi9ARgvXc

9. "MEL: Legal Spanish language model." ArXiv, Janvier 2025. arxiv.org/html/2501.16011

10. "3CEL: a Corpus of Legal Spanish Contract Clauses." ArXiv, Janvier 2025. arxiv.org/html/2501.15990

11. "Instruction Finetuning LLaMA-3-8B Model Using LoRA for Financial Named Entity Recognition." ArXiv, Janvier 2026. arxiv.org/abs/2601.10043

12. Unsloth Documentation. "LoRA Fine-tuning Hyperparameters Guide." unsloth.ai/docs (2025).

13. Gretel.ai. "GLiNER Models for PII Detection." gretel.ai/blog (2025).

14. Microsoft Presidio. "Using GLiNER with Presidio." microsoft.github.io/presidio (2025).

---

**Généré par :** AlexAlves87
**Date :** 31/01/2026
**Révision :** 1.1 (ajout section 4 : Lectures Préalables Obligatoires)
**Prochaine étape :** Établir baselines (GLiNER + MEL) avant de commencer le fine-tuning
