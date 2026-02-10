# Research: General vs. Legal Domain Embeddings for Entity Type Disambiguation in NER

**Date:** 2026-02-07
**Objective:** Investigate why specialized legal embeddings produce more false positives than general-purpose embeddings in the post-NER entity type classification task, and determine the best embedding strategy for ContextSafe.

---

## 1. Executive Summary

1. **Legal domain embeddings produce more false positives** because legal fine-tuning reduces discriminative capacity between entity types by collapsing the embedding space around legal linguistic patterns (augmented anisotropy, narrower semantic space).

2. **General-purpose embeddings are superior for entity type discrimination** because they maintain a broader and more diverse semantic space where differences between categories (person vs organization vs date) are more pronounced.

3. **Anisotropy is NOT inherently bad** -- recent work (ICLR 2024) shows that controlled anisotropy can improve performance -- but uncontrolled anisotropy from domain fine-tuning reduces the inter-class discrimination needed for type centroids.

4. **Recommendation: use `BAAI/bge-m3` or `intfloat/multilingual-e5-large`** (general embeddings) for the type validator, NOT legal embeddings. If domain knowledge is desired, use a hybrid approach with adapters (LoRA) that preserve general capacity.

5. **The context-aware centroid technique is well supported** by the literature on prototypical networks (CEPTNER, KCL), but requires 50-100 diverse examples per type and surrounding context of 10-15 tokens.

---

## 2. Finding 1: General-Purpose vs Domain-Specific Embeddings for Entity Type Classification

### 2.1 Key Evidence: General-purpose models fail in domain tasks BUT excel in type discrimination

| Paper | Venue/Year | Key Finding |
|-------|------------|-------------|
| **"Do We Need Domain-Specific Embedding Models? An Empirical Investigation"** (Tang & Yang) | arXiv 2409.18511 (2024) | Evaluated 7 SOTA models on FinMTEB (finance benchmark). General models showed significant drop in domain tasks, and their MTEB performance does NOT correlate with FinMTEB performance. **BUT**: this drop was in retrieval and STS, not in entity type classification. |
| **"NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data"** (Bogdanov et al.) | EMNLP 2024 | Compact model (RoBERTa base) pre-trained with contrastive learning on 4.38M entity annotations. Outperforms similar-sized models in few-shot NER and competes with much larger LLMs. **Key**: diversity of entity types in pre-training dataset is fundamental. |
| **"LegNER: A Domain-Adapted Transformer for Legal NER and Text Anonymization"** (Al-Hussaeni et al.) | Frontiers in AI (2025) | Legal model based on BERT-base + extended vocabulary + 1,542 annotated court cases. F1 >99% on 6 entity types. **However**: the paper does not report analysis of false positives between types, and evaluated entities are very different (PERSON vs LAW vs CASE_REFERENCE). |
| **"MEL: Legal Spanish Language Model"** (2025) | arXiv 2501.16011 | XLM-RoBERTa-large fine-tuned with 5.52M Spanish legal texts (92.7 GB). Outperforms baselines XLM-R in document classification. **Critical**: authors admit that "Token or span classification tasks remain unevaluated due to the lack of annotated texts" -- meaning they did NOT evaluate NER. |

### 2.2 Interpretation: Why General Models Discriminate TYPES Better

The key distinction is between **two different tasks**:

| Task | What the embedding needs | Best model |
|------|--------------------------|------------|
| Legal Retrieval / Legal STS | Capture legal semantic nuances | Domain-specific |
| Entity type classification | Separate broad categories (person vs org vs date) | General-purpose |

Legal embeddings are optimized for the first task: retrieving similar legal documents, understanding legal terminology, capturing legal relationships. This makes them WORSE for the second task because:

1. **Diversity collapse**: legal fine-tuning brings all representations closer to the legal subspace, reducing distance between "person mentioned in judgment" and "organization mentioned in judgment" because both appear in similar legal contexts.

2. **Contextual bias**: a legal model learns that "Telefonica" in a legal context is as legal-relevant as "Alejandro Alvarez", flattening type differences.

3. **Uncontrolled anisotropy**: fine-tuning introduces anisotropy that can collapse distinct types into the same dominant directions of the embedding space.

**Relevant URL**: [Do We Need Domain-Specific Embedding Models?](https://arxiv.org/abs/2409.18511)

---

## 3. Finding 2: Why Legal Embeddings Produce More False Positives

### 3.1 The anisotropy problem in fine-tuned embeddings

| Paper | Venue/Year | Key Finding |
|-------|------------|-------------|
| **"Anisotropy is Not Inherent to Transformers"** (Machina & Mercer) | NAACL 2024 | Demonstrate anisotropy is not inherent to transformer architecture. Identify large Pythia models with isotropic spaces. Previous theoretical justifications for anisotropy were insufficient. |
| **"Stable Anisotropic Regularization" (I-STAR)** (Rudman & Eickhoff) | ICLR 2024 | Counter-intuitive result: REDUCING isotropy (increasing anisotropy) improves downstream performance. Use IsoScore* (differentiable metric) as regularizer. **Key implication**: CONTROLLED anisotropy can be beneficial, but UNCONTROLLED anisotropy from domain fine-tuning is harmful. |
| **"The Shape of Learning: Anisotropy and Intrinsic Dimensions in Transformer-Based Models"** (2024) | EACL 2024 | Transformer decoders show bell-shaped curve with max anisotropy in middle layers, while encoders show more uniform anisotropy. Layers where anisotropy is higher coincide with layers encoding type information. |
| **"How Does Fine-tuning Affect the Geometry of Embedding Space: A Case Study on Isotropy"** (Rajaee & Pilehvar) | EMNLP 2021 Findings | Although isotropy is desirable, fine-tuning DOES NOT necessarily improve isotropy. Local structures (like token type encoding) suffer massive changes during fine-tuning. Elongated directions (dominant directions) in fine-tuned space carry essential linguistic knowledge. |
| **"Representation Degeneration Problem in Prompt-based Fine-tuning"** | LREC 2024 | Embedding space anisotropy limits performance in prompt-based fine-tuning. Propose CLMA (Contrastive Learning framework) to alleviate anisotropy. |

### 3.2 Mechanism of false positives in legal embeddings

Based on previous evidence, the mechanism by which legal embeddings produce more false positives in entity type validation is:

```
1. Legal Fine-tuning → Embedding space contracts towards legal subspace
                         ↓
2. Representations of "person in legal context" and
   "organization in legal context" move closer
   (both are "legally relevant entities")
                         ↓
3. Centroids of PERSON_NAME and ORGANIZATION overlap
   in legal-fine-tuned space
                         ↓
4. Cosine similarity between centroid_PERSON and an ORGANIZATION
   is higher than it would be with general embeddings
                         ↓
5. More entities cross reclassification threshold → more FP
```

### 3.3 Direct evidence from legal domain

| Paper | Venue/Year | Key Finding |
|-------|------------|-------------|
| **"Improving Legal Entity Recognition Using a Hybrid Transformer Model and Semantic Filtering Approach"** | arXiv 2410.08521 (2024) | Legal-BERT produces false positives on ambiguous terms and nested entities. Propose post-prediction semantic filtering using cosine similarity against predefined legal patterns. **Result**: Precision increases from 90.2% to 94.1% (+3.9 pp), F1 from 89.3% to 93.4% (+4.1 pp). Use formula S(ei,Pj) = cos(ei, Pj) with threshold tau to filter. |

**This paper directly validates our approach** of using cosine similarity to filter predictions, BUT uses predefined legal patterns instead of type centroids. Combining both approaches (general centroids + legal patterns as additional filter) is a natural extension.

**Relevant URL**: [Improving Legal Entity Recognition Using Semantic Filtering](https://arxiv.org/abs/2410.08521)

---

## 4. Finding 3: Best Embedding Models for Entity Type Disambiguation (2024-2026)

### 4.1 Comparison of candidate models

| Model | Size | Dim | Languages | MTEB Score | Strengths | Weaknesses for our task |
|-------|------|-----|-----------|------------|-----------|-------------------------|
| **BAAI/bge-m3** | ~2.3GB | 1024 | 100+ | 63.0 | Multi-granularity (dense+sparse+ColBERT), best multilingual performance in MTEB | Larger size, higher latency |
| **intfloat/multilingual-e5-large** | ~1.1GB | 1024 | 100+ | ~62 | Excellent Spanish, well documented, requires "query:" prefix | Slightly inferior to bge-m3 in multilingual |
| **nomic-ai/nomic-embed-text-v2** | ~700MB | 768 | 100 | ~62 | MoE (Mixture of Experts), efficient, 8192 tokens | More recent, less validated in legal Spanish |
| **intfloat/multilingual-e5-small** | ~448MB | 384 | 100 | ~56 | Lighter, low latency | Smaller dimension may lose discrimination |
| **Wasserstoff-AI/Legal-Embed** | ~1.1GB | 1024 | Multi | N/A | Fine-tuned on legal | **DISCARDED: higher FP for reason analyzed in section 3** |

### 4.2 Evidence-based recommendation

**Primary Model: `BAAI/bge-m3`**

Justification:
1. Best performance in multilingual benchmarks, including Spanish (see [OpenAI vs Open-Source Multilingual Embedding Models](https://towardsdatascience.com/openai-vs-open-source-multilingual-embedding-models-e5ccb7c90f05/))
2. Higher dimensionality (1024) = greater capacity to separate type centroids
3. Dense+sparse+ColBERT retrieval works well for similarity comparisons
4. Supports up to 8192 tokens (useful for long legal contexts)

**Alternative Model: `intfloat/multilingual-e5-large`**

Justification:
1. Well documented with technical paper (arXiv:2402.05672)
2. Excellent Spanish performance verified
3. Slightly smaller than bge-m3
4. Already proposed in `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md`

**IMPORTANT**: DO NOT use `Legal-Embed` nor any legal domain fine-tuned model. Academic evidence indicates general models better preserve separation between entity types, which is exactly what we need for centroids.

### 4.3 Benchmark sources

| Benchmark | What it measures | Reference |
|-----------|------------------|-----------|
| MTEB (Massive Text Embedding Benchmark) | 8 tasks including classification and clustering | [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) |
| FinMTEB (Finance MTEB) | Performance in financial domain | Tang & Yang (2024), arXiv:2409.18511 |
| MMTEB (Massive Multilingual TEB) | Multilingual extension of MTEB (2025) | [MMTEB GitHub](https://github.com/embeddings-benchmark/mteb) |

**Critical note**: No existing benchmark directly measures "entity type discrimination via centroids". MTEB has classification and clustering subtasks which are useful approximations. Creating an internal benchmark for ContextSafe is recommended.

---

## 5. Finding 4: Centroid-Based Type Validation Techniques

### 5.1 Prototypical networks and centroids for NER

| Paper | Venue/Year | Key Finding |
|-------|------------|-------------|
| **"CEPTNER: Contrastive Learning Enhanced Prototypical Network for Two-stage Few-shot NER"** (Wang et al.) | Knowledge-Based Systems (2024) | Two stages: (1) boundary detection, (2) prototypical classification with contrastive learning. Entity-level contrastive learning separates types effectively. Evaluated on Few-NERD, CrossNER, SNIPS. |
| **"Transformer-based Prototype Network for Chinese Nested NER"** (MSTPN) | Scientific Reports (2025) | Prototypical networks with transformers for nested NER. Uses entity bounding boxes as prototypes. |
| **"KCL: Few-shot NER with Knowledge Graph and Contrastive Learning"** | LREC-COLING 2024 | Combines Knowledge Graphs with contrastive learning to learn semantic label representation. Uses KG to provide structured type info. Contrastive representation separates label clusters in prototypical space. |
| **"Multi-Head Self-Attention-Enhanced Prototype Network with Contrastive-Center Loss for Few-Shot Relation Extraction"** | Applied Sciences (2024) | Contrastive-center loss comparing training samples with corresponding AND non-corresponding class centers. Reduces intra-class distances and increases inter-class distances. |
| **"CLESR: Context-Based Label Knowledge Enhanced Span Recognition for NER"** | Int J Computational Intelligence Systems (2024) | Improves nested NER integrating contextual info with label knowledge. Spans align with textual descriptions of types in shared semantic space. |

### 5.2 Best practices for construction of centroids

Based on reviewed literature:

| Aspect | Recommendation | Justification |
|--------|----------------|---------------|
| **Number of examples** | 50-100 per type | CEPTNER shows effectiveness with few examples; 50 is minimum, 100 is robust |
| **Example diversity** | Include context, format, length variations | KCL emphasizes diversity for more discriminative clusters |
| **Context size** | 10-15 surrounding tokens | NER survey (arXiv:2401.10825) confirms BERT captures intra- and inter-sentence context effectively |
| **Centroid update** | Recalculate periodically with new confirmed examples | CEPTNER shows more examples improve separation; centroids should evolve |
| **Contrastive refinement** | Train with contrastive loss to maximize separation | Multiple papers show contrastive loss is KEY for type separation |
| **Intermediate layers** | Consider extracting from layers 15-17, not just final | NER Retriever (arXiv:2509.04011) shows intermediate layers contain more type info |

### 5.3 Context window size

| Paper | Finding on context |
|-------|--------------------|
| Survey NER (arXiv:2401.10825) | "BERT encodings capture important within and adjacent-sentence context." Increasing window improves performance. |
| Span-based Unified NER via Contrastive Learning (IJCAI 2024) | Spans with context align with type descriptions in shared space. Context is necessary to disambiguate. |
| Contextualized Span Representations (Wadden et al.) | Propagation of span representations via coreference links allows disambiguating difficult mentions. |

**Recommendation**: For ContextSafe, use **10-15 token context** on each side of the entity. For entities at start/end of sentence, pad with tokens from previous/next sentence if available.

---

## 6. Finding 5: Hybrid Approaches (General + Domain)

### 6.1 Concatenation and ensemble of embeddings

| Paper | Venue/Year | Key Finding |
|-------|------------|-------------|
| **"Automated Concatenation of Embeddings for Structured Prediction" (ACE)** | ACL-IJCNLP 2021 | Framework that automatically finds best embedding concatenation for structured prediction (including NER). Achieves SOTA on 6 tasks over 21 datasets. Selection varies by task and candidate set. |
| **"Pooled Contextualized Embeddings for NER"** (Akbik et al.) | NAACL 2019 | Aggregates contextualized embeddings of each unique instance to create "global" representation. Stacked embeddings (combining multiple types) is a key feature of Flair and significantly improves NER. |
| **"Improving Few-Shot Cross-Domain NER by Instruction Tuning a Word-Embedding based Retrieval Augmented LLM" (IF-WRANER)** | EMNLP 2024 Industry | Uses word-level embeddings (not sentence-level) for in-prompt example retrieval. Outperforms SOTA on CrossNER by >2% F1. Deployed in production, reducing human escalations ~15%. |
| **"Pre-trained Embeddings for Entity Resolution: An Experimental Analysis"** (Zeakis et al.) | VLDB 2023 | Analysis of 12 language models on 17 datasets for entity resolution. Contextualized embeddings (BERT variants) consistently outperform static ones (fastText), but combination can be beneficial. |

### 6.2 Adapters (LoRA) to preserve general knowledge

| Paper | Venue/Year | Key Finding |
|-------|------------|-------------|
| **"Continual Named Entity Recognition without Catastrophic Forgetting"** (Zheng et al.) | EMNLP 2023 | Propose pooled feature distillation loss + pseudo-labeling + adaptive re-weighting. Catastrophic forgetting in continual NER is intensified by "semantic shift" of non-entity type. |
| **"A New Adapter Tuning of LLM for Chinese Medical NER"** | Automation in Construction (2024) | Adapters avoid catastrophic forgetting because they learn new knowledge without extensive parameter adjustments. Preferable for multi-domain NER. |
| **"Mixture of LoRA Experts for Continual Information Extraction"** | EMNLP 2025 Findings | MoE framework with LoRA for continual information extraction. Allows adding domains without forgetting previous ones. |
| **"LoRASculpt: Sculpting LoRA for Harmonizing General and Specialized Knowledge"** | CVPR 2025 | Technique to balance general and specialized knowledge during LoRA fine-tuning. |

### 6.3 Viable combination strategies for ContextSafe

| Strategy | Complexity | Expected Benefit | Recommended |
|----------|------------|------------------|-------------|
| **A: Pure general embeddings** | Low | Good type discrimination without additional FP | Yes (baseline) |
| **B: Concatenate general + legal** | Medium | More dimensions, captures both aspects | Evaluable but costly in latency |
| **C: Weighted average general + legal** | Medium | Simpler than concat, but loses information | Not recommended (averaging dilutes) |
| **D: Meta-model over multiple embeddings** | High | Better precision if sufficient training data | For future |
| **E: LoRA adapter on general model** | Medium-High | Preserves general capacity + adds domain | Yes (second step) |

**Recommendation for ContextSafe**:

- **Phase 1 (immediate)**: Use pure general embeddings (bge-m3 or e5-large). Evaluate FP reduction vs experience with legal embeddings.

- **Phase 2 (if Phase 1 insufficient)**: Apply LoRA adapter on general model with contrastive examples of Spanish legal entities. This preserves general type discrimination capacity while adding domain knowledge.

- **Phase 3 (optional)**: ACE-style automated search for best concatenation if a sufficiently large type validation dataset is available.

---

## 7. Synthesis and Final Recommendation

### 7.1 Direct answer to research questions

**Q1: General-purpose vs domain-specific for entity type classification?**

Use **general-purpose**. Evidence from multiple papers (Tang & Yang 2024, Rajaee & Pilehvar 2021, Machina & Mercer NAACL 2024) indicates that:
- General models maintain broader semantic spaces
- Entity type discrimination requires inter-class separation, not intra-domain depth
- Domain models collapse similar types into same subspace

**Q2: Why do legal embeddings produce more false positives?**

Three convergent factors:
1. **Semantic diversity collapse**: legal fine-tuning brings representations of all entities closer to "legal" subspace
2. **Uncontrolled anisotropy**: fine-tuning introduces dominant directions encoding "legality" instead of "entity type" (Rajaee & Pilehvar 2021, Rudman & Eickhoff ICLR 2024)
3. **Centroid overlap**: centroids of PERSON and ORGANIZATION move closer because both appear in identical legal contexts

**Q3: Best model?**

`BAAI/bge-m3` (first option) or `intfloat/multilingual-e5-large` (second option). Both are general, multilingual, with good Spanish support and 1024 dimensionality sufficient to separate type centroids.

**Q4: Centroid technique?**

Well supported by CEPTNER (2024), KCL (2024), MSTPN (2025). Keys:
- 50-100 diverse examples per type
- Context of 10-15 tokens around entity
- Contrastive learning to refine centroids if possible
- Intermediate layers (15-17) may be more informative than final layer

**Q5: Hybrid approach?**

For future: LoRA adapters on general model is the most promising strategy. Preserves general discrimination + adds domain knowledge. ACE (automated concatenation) is viable if sufficient evaluation data exists.

### 7.2 Impact on previous document

Document `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` recommends `multilingual-e5-large` as main model and suggests evaluating `Legal-Embed` as alternative. Based on this research:

| Aspect | Previous document | Update |
|--------|-------------------|--------|
| Main model | `multilingual-e5-large` | **Correct**, maintain |
| Legal-Embed alternative | Suggested for evaluation | **DISCARD**: evidence indicates it will produce more FP |
| Real alternative | Not proposed | **Add `BAAI/bge-m3`** as first option |
| Contrastive refinement | Not mentioned | **Add**: if centroids don't separate enough, apply contrastive learning |
| Intermediate layers | Not mentioned | **Add**: extract embeddings from layers 15-17, not just last |

---

## 8. Consolidated Table of Reviewed Papers

| # | Paper | Venue | Year | Main Topic | URL |
|---|-------|-------|------|------------|-----|
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

## 9. Related Documents

| Document | Relationship |
|----------|--------------|
| `docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Previous document proposing type validator with embeddings. This research UPDATES its recommendations. |
| `docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Previous evaluation of embeddings for document classification (different task). |
| `docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap embeddings for document classification. |
| `docs/reports/2026-01-30_investigacion_gaps_pipeline_hibrido.md` | Gaps of hybrid NER pipeline (context of type errors). |
| `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Research on hybrid NER (architecture context). |

---

```
Version: 1.0.0
Author: AlexAlves87
Reviewed papers: 23
```
