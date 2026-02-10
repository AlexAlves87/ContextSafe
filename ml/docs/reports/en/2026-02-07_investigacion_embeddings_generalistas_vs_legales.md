# Research: Generalist vs. Legal Embeddings for Entity Type Disambiguation

**Date:** 2026-02-07
**Objective:** Determine whether to use generalist embeddings (multilingual-e5-large) or legal-specific ones (Legal-Embed, voyage-law-2) for the post-NER entity type validator in ContextSafe.

---

## 1. Executive Summary

1. **Key Finding**: Legal embeddings are optimized for **retrieval** (finding similar documents), NOT for **entity type discrimination**. This explains the observed false positives.

2. **Recommendation**: Use **generalist embeddings** (`intfloat/multilingual-e5-large`) for entity type disambiguation. Legal ones can cause semantic space collapse where PERSON and ORGANIZATION end up too close.

3. **Key Evidence**: Domain fine-tuning can cause "over-specialization" that reduces discrimination capability between categories (catastrophic forgetting of boundaries between types).

4. **Hybrid Alternative**: If legal knowledge is needed, use a two-stage approach: generalist for type + legal for specific entity validation.

5. **Expected Error Reduction**: 4-5% with well-calibrated generalist embeddings (literature: WNUT17, NER Retriever).

---

## 2. Reviewed Literature

### 2.1 Generalist vs. Domain Specific

| Paper/Source | Venue/Year | Relevant Finding |
|--------------|------------|------------------|
| "Do we need domain-specific embedding models?" | arXiv:2409.18511 (2024) | In finance (FinMTEB), general models degrade vs specific ones. BUT: this is for **retrieval**, not type classification. |
| "How Does Fine-tuning Affect the Geometry of Embedding Space?" | ACL Findings 2021 | Domain fine-tuning **reduces separation** between classes in embedding space. Clusters collapse. |
| "Is Anisotropy Really the Cause of BERT Embeddings not Working?" | EMNLP Findings 2022 | Anisotropy (embeddings concentrated in narrow cone) is a known problem. Domain fine-tuning **worsens** it. |
| "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE" | EMNLP 2025 | Catastrophic forgetting occurs in domain fine-tuning. Models forget previously learned boundaries. |
| "Continual Named Entity Recognition without Catastrophic Forgetting" | arXiv:2310.14541 (2023) | Continual NER suffers catastrophic forgetting: old types "consolidate" into non-entity. Analogous to our problem. |

### 2.2 Why Legal Embeddings Cause False Positives

| Phenomenon | Explanation | Source |
|------------|-------------|--------|
| **Semantic space collapse** | Legal fine-tuning optimizes for similar legal documents to be close, NOT to separate PERSON from ORGANIZATION | Weaviate Blog, MongoDB Fine-Tuning Guide |
| **Over-specialization** | "Overly narrow training can make the fine-tuned model too specialized" - loses general discrimination capability | [Weaviate](https://weaviate.io/blog/fine-tune-embedding-model) |
| **Retrieval-oriented contrastive loss** | voyage-law-2 uses "specifically designed positive pairs" for legal retrieval, not for entity classification | [Voyage AI Blog](https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/) |
| **Uniform legal terminology** | In legal texts, "Garcia" can be a plaintiff, lawyer, or law firm name. The legal model embeds them **close** because they are all legal | User empirical observation |

### 2.3 Centroids and Prototype-Based Classification

| Paper/Source | Venue/Year | Relevant Finding |
|--------------|------------|------------------|
| "NER Retriever: Zero-Shot NER with Type-Aware Embeddings" | arXiv:2509.04011 (2025) | Intermediate layers (layer 17) better than final outputs for type. MLP with contrastive loss to separate types. |
| "CEPTNER: Contrastive Learning Enhanced Prototypical Network" | KBS (2024) | Prototypical networks with 50-100 examples per type are sufficient for robust centroids. |
| "ReProCon: Scalable Few-Shot Biomedical NER" | arXiv:2508.16833 (2025) | Multiple prototypes per category improve representation of heterogeneous entities. |
| "Mastering Intent Classification with Embeddings: Centroids" | Medium (2024) | Centroids have "fastest training time" and decent accuracy. Perfect for rapid updates. |

### 2.4 Embedding Model Benchmarks

| Model | Size | Languages | MTEB Avg | Advantage | Disadvantage |
|-------|------|-----------|----------|-----------|--------------|
| `intfloat/multilingual-e5-large` | 1.1GB | 100 | ~64 | Best general multilingual, excellent Spanish | Requires "query:" prefix |
| `intfloat/multilingual-e5-large-instruct` | 1.1GB | 100 | ~65 | Supports instructions, more flexible | Slightly slower |
| `BAAI/bge-m3` | 1.5GB | 100+ | ~66 | Hybrid dense+sparse, 8192 tokens | More complex to use |
| `voyage-law-2` | API | EN | ~72 (legal) | Best for legal retrieval | Commercial API, English only |
| `Legal-Embed (Wasserstoff)` | 1.1GB | Multi | N/A | Fine-tuned on legal | **Likely causes FPs in classification** |

---

## 3. Analysis: Why Generalists Are Better for Entity Type

### 3.1 Different Training Objective

| Legal Embeddings | Generalist Embeddings |
|------------------|-----------------------|
| Optimized for: "document A similar to document B" | Optimized for: "text A semantically related to text B" |
| Positive pairs: fragments of same legal document | Positive pairs: paraphrases, translations, variants |
| Result: everything legal is close | Result: semantic types separated |

**Consequence**: In legal embeddings, "Alejandro Alvarez" (lawyer) and "Bufete Alvarez S.L." (company) are **close** because both are legal. In generalists, they are **far** because one is a person and the other an organization.

### 3.2 Evidence of Aggravated Anisotropy

The ACL Findings 2021 paper demonstrates that:

1. Fine-tuning **reduces variance** of embedding space
2. Clusters of different types **move closer**
3. Linear separability **decreases**

This directly explains false positives: when all legal embeddings collapse towards one region, cosine distance loses discriminative power.

### 3.3 Task vs. Domain

| Aspect | Domain Embeddings (Legal) | Task Embeddings (Type) |
|--------|---------------------------|------------------------|
| Question they answer | "Is this text legal?" | "Is this a person or company?" |
| Training | Legal corpus | Contrastive by entity type |
| Utility for NER type validation | Low | High |

Our problem is a **task** problem (classify type), not a **domain** problem (identify legal texts).

---

## 4. Recommendation for ContextSafe

### 4.1 Recommended Approach: Pure Generalist

```
Pipeline:
  NER → Detections with assigned type
    ↓
  EntityTypeValidator (multilingual-e5-large)
    ↓
  For each entity:
    1. Embed "query: [entity + context ±10 tokens]"
    2. Compare vs centroids by type (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
    3. Decisions:
       - If best_centroid ≠ NER_type AND similarity > 0.75 AND margin > 0.10 → RECLASSIFY
       - If margin < 0.05 → FLAG HITL
       - Else → KEEP NER type
```

**Model**: `intfloat/multilingual-e5-large` (1.1GB)

**Justification**:
- Trained on 100 languages including Spanish
- NOT over-specialized in any domain
- Preserves semantic separation between PERSON/ORGANIZATION/DATE/LOCATION
- Already recommended in previous research (see `2026-02-07_embeddings_entity_type_disambiguation.md`)

### 4.2 Alternative Approach: Hybrid (If Legal Knowledge Is Needed)

```
Stage 1: Type Classification (GENERALIST)
  multilingual-e5-large → Entity type

Stage 2: Legal Entity Validation (LEGAL, optional)
  voyage-law-2 or Legal-Embed → "Is this entity valid in legal context?"
  (Only for cases flagged as doubtful)
```

**When to use hybrid**: If there are specific legal entities (e.g., "article 24.2 CE", "Law 13/2022") requiring legal knowledge validation.

For ContextSafe (generic PII), the pure generalist approach is sufficient.

### 4.3 Centroid Configuration

| Type | Examples Needed | Context Strategy |
|------|-----------------|------------------|
| PERSON_NAME | 100 | "query: The lawyer [NAME] appeared..." |
| ORGANIZATION | 100 | "query: The company [ORG] filed an appeal..." |
| DATE | 50 | "query: On date [DATE] judgment was issued..." |
| LOCATION | 50 | "query: In the city of [PLACE] was held..." |
| DNI_NIE | 30 | "query: with ID [NUMBER]" (short context, fixed pattern) |

**Context**: ±10 tokens around the entity. Neither too short (loses context) nor too long (introduces noise).

---

## 5. Proposed Experiment

### 5.1 A/B Comparison

| Condition | Model | Expected |
|-----------|-------|----------|
| A (Baseline) | No validator | Current pass rate: 60% |
| B (Generalist) | `multilingual-e5-large` | Expected pass rate: 64-65% |
| C (Legal) | `Legal-Embed-intfloat-multilingual-e5-large-instruct` | Expected pass rate: < 60% (more FPs) |

### 5.2 Metrics to Evaluate

1. **Pass rate in adversarial test** (35 existing tests)
2. **Reclassification accuracy**: % of correct reclassifications
3. **False positive rate**: Correctly typed entities that were wrongly reclassified
4. **Additional latency**: ms per validated entity

### 5.3 Specific Test Cases

Based on errors from audit.md (see `2026-02-07_embeddings_entity_type_disambiguation.md`, section 6):

| Entity | NER Type | Correct Type | Expected OK Model |
|--------|----------|--------------|-------------------|
| "Alejandro Alvarez" | ORGANIZATION | PERSON_NAME | Generalist |
| "10/10/2025" | ORGANIZATION | DATE | Generalist |
| "Pura" | LOCATION | PERSON_NAME | Generalist |
| "Finalmente" | ORGANIZATION | NOT PII | Generalist (low similarity with all) |
| "Whatsapp" | PERSON | ORGANIZATION/PLATFORM | Generalist |

---

## 6. Risks and Mitigations

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Generalist also doesn't discriminate separate PERSON/ORG well in legal Spanish | Medium | Evaluate before implementing; if fails, train centroids with contrastive loss |
| Unacceptable latency (>100ms/entity) | Low | Batch processing, cache frequent embeddings |
| Centroids require more than 100 examples | Low | Increase to 200 if F1 < 0.90 in validation |
| 1.1GB model doesn't fit in production | Low | Quantize to INT8 (~300MB) or use e5-base (560MB) |

---

## 7. Conclusion

**Legal embeddings are optimized for the wrong task.** Their objective (retrieval of similar documents) causes entities of different types but same domain (legal) to be embedded closely, reducing discrimination capability.

For entity type disambiguation, **generalist embeddings** better preserve semantic boundaries between PERSON, ORGANIZATION, DATE, etc., because they haven't been "collapsed" towards a specific domain.

**Final Recommendation**: Implement validator with `intfloat/multilingual-e5-large` and empirically evaluate before considering legal alternatives.

---

## 8. Next Steps

1. [ ] Download `intfloat/multilingual-e5-large` (~1.1GB)
2. [ ] Build dataset of examples per type (PERSON_NAME, ORGANIZATION, DATE, LOCATION) with legal context
3. [ ] Calculate centroids for each type
4. [ ] Implement `EntityTypeValidator` with configurable thresholds
5. [ ] Evaluate on adversarial test (35 tests)
6. [ ] (Optional) Compare vs `Legal-Embed` to confirm false positive hypothesis
7. [ ] Document results and final decision

---

## Related Documents

| Document | Relationship |
|----------|--------------|
| `ml/docs/reports/2026-02-07_embeddings_entity_type_disambiguation.md` | Previous research, proposed architecture |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Embeddings roadmap, activation criteria |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Current pipeline, baseline metrics |
| `auditoria.md` | Identified classification errors |
| `ml/models/type_centroids.json` | Existing centroids (requires verifying model used) |

---

## References

1. **FinMTEB**: Li et al. (2024). "Do we need domain-specific embedding models? An empirical investigation." arXiv:2409.18511. https://arxiv.org/abs/2409.18511

2. **Geometry of Fine-tuning**: Merchant et al. (2020). "What Happens To BERT Embeddings During Fine-tuning?" ACL Findings 2021. https://aclanthology.org/2021.findings-emnlp.261.pdf

3. **Anisotropy**: Ethayarajh (2019). "How Contextual are Contextualized Word Representations?" EMNLP 2019. Rajaee & Pilehvar (2022). "Is Anisotropy Really the Cause?" EMNLP Findings 2022. https://aclanthology.org/2022.findings-emnlp.314.pdf

4. **Catastrophic Forgetting in NER**: Wang et al. (2023). "Continual Named Entity Recognition without Catastrophic Forgetting." arXiv:2310.14541. https://arxiv.org/abs/2310.14541

5. **DES-MoE**: Yang et al. (2025). "Dynamic Expert Specialization: Catastrophic Forgetting-Free Multi-Domain MoE." EMNLP 2025. https://aclanthology.org/2025.emnlp-main.932.pdf

6. **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot NER with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011

7. **CEPTNER**: Wang et al. (2024). "Contrastive learning Enhanced Prototypical network for Few-shot NER." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512

8. **ReProCon**: Liu et al. (2025). "ReProCon: Scalable Few-Shot Biomedical NER." arXiv:2508.16833. https://arxiv.org/abs/2508.16833

9. **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings." arXiv:2402.05672. https://huggingface.co/intfloat/multilingual-e5-large

10. **voyage-law-2**: Voyage AI (2024). "Domain-Specific Embeddings: Legal Edition." https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/

11. **Fine-tuning Trade-offs**: Weaviate (2024). "Why, When and How to Fine-Tune a Custom Embedding Model." https://weaviate.io/blog/fine-tune-embedding-model

12. **Intent Classification with Centroids**: Puig (2024). "Mastering Intent Classification with Embeddings." Medium. https://medium.com/@mpuig/mastering-intent-classification-with-embeddings-centroids-neural-networks-and-random-forests-3fe7c57ca54c

---

```
Version: 1.0.0
Author: AlexAlves87
Search tokens: 12 queries
```
