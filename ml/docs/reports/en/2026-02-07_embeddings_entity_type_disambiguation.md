# Research: Embeddings for Entity Type Disambiguation in NER

**Date:** 2026-02-07
**Objective:** Solve entity type classification errors in the ContextSafe NER system (e.g., "Alejandro Alvarez" classified as ORGANIZATION instead of PERSON_NAME)

---

## 1. Executive Summary

1. **Problem identified**: The current NER model confuses entity types, classifying person names as organizations, dates as organizations, and common capitalized words as PII.

2. **Proposed solution**: Embeddings-based post-NER validator that compares each detection against semantic centroids by entity type.

3. **Recommended model**: `intfloat/multilingual-e5-large` (1.1GB) with possible upgrade to `Legal-Embed` for legal domain.

4. **Main technique**: Centroid-based classification with reclassification threshold (threshold 0.75, margin 0.1).

5. **Expected error reduction**: ~4.5% according to literature (WNUT17 benchmark).

---

## 2. Literature Reviewed

| Paper | Venue | Year | Relevant Finding |
|-------|-------|------|------------------|
| NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings | arXiv (2509.04011) | 2025 | Intermediate layers (layer 17) capture better type information than final outputs. MLP with contrastive loss achieves zero-shot to unseen types. |
| CEPTNER: Contrastive Learning Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems (ScienceDirect) | 2024 | Prototypical networks with contrastive learning effectively separate entity types with few examples (50-100). |
| Recent Advances in Named Entity Recognition: A Comprehensive Survey | arXiv (2401.10825) | 2024 | Hybrid approaches (rules + ML + embeddings) consistently outperform single models. |
| Redundancy-Enhanced Framework for Error Correction in NER | OpenReview | 2025 | Post-processor with Transformer refiner + entity-tag embeddings achieves 4.48% error reduction in WNUT17. |
| Multilingual E5 Text Embeddings: A Technical Report | arXiv (2402.05672) | 2024 | Model multilingual-e5-large supports 100 languages with excellent performance in Spanish. Requires "query:" prefix for search embeddings. |

---

## 3. Identified Best Practices

1. **Include context**: Embedding the entity WITH its surrounding context (10-15 words) significantly improves disambiguation.

2. **Use intermediate layers**: Representations from middle layers (layer 15-17) contain more type information than final outputs.

3. **Contrastive learning**: Training with contrastive loss better separates types in the embedding space.

4. **Threshold with margin**: Do not reclassify just by higher similarity; require minimum margin (>0.1) to avoid false positives.

5. **Examples per type**: 50-100 confirmed examples per category are sufficient to build robust centroids.

6. **Specific domain**: Models fine-tuned for the domain (legal in our case) improve performance.

7. **Flagging for HITL**: When similarities are close (<0.05 difference), mark for human review instead of automatically reclassifying.

---

## 4. Recommendation for ContextSafe

### 4.1 Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Current NER Pipeline                         │
│  (RoBERTa + SpaCy + Regex → Intelligent Merge)                  │
60 └─────────────────────┬───────────────────────────────────────────┘
                      │ Detections with assigned type
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Entity Type Validator (NEW)                         │
│                                                                  │
│  1. Extract entity + context (±15 tokens)                       │
│  2. Generate embedding with multilingual-e5-large               │
│  3. Calculate cosine similarity with centroids per type         │
│  4. Decision:                                                   │
│     - If best_type ≠ NER_type AND similarity > 0.75             │
│       AND margin > 0.1 → RECLASSIFY                             │
│     - If margin < 0.05 → MARK FOR HITL                          │
│     - Else → KEEP NER type                                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Validated/corrected detections
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Glossary & Anonymization                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Selected Model

**Main**: `intfloat/multilingual-e5-large`
- Size: 1.1GB
- Languages: 100 (excellent Spanish)
- Latency: ~50-100ms per embedding
- Requires "query:" prefix for embeddings

**Alternative (evaluate)**: `Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct`
- Fine-tuned for legal domain
- Same base size
- Potentially better for Spanish legal documents

### 4.3 Centroid Construction

Priority categories (frequent confusion):

| Category | Examples Needed | Source |
|----------|-----------------|--------|
| PERSON_NAME | 100 | Names from auditoria.md + gazetteers |
| ORGANIZATION | 100 | Companies, institutions from legal documents |
| DATE | 50 | Dates in DD/MM/YYYY, DD-MM-YYYY formats |
| LOCATION | 50 | Cities, Spanish provinces |

**Example format** (with context):
```
"query: The lawyer Alejandro Alvarez appeared as a witness in the trial"
"query: The company Telefónica S.A. filed an appeal in cassation"
"query: On date 10/10/2025 sentence was passed"
```

### 4.4 Integration with Existing Pipeline

Proposed location: `src/contextsafe/infrastructure/nlp/validators/entity_type_validator.py`

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

### 4.5 Success Metrics

| Metric | Goal | Measurement |
|--------|------|-------------|
| Type error reduction | ≥4% | Compare before/after on validation set |
| Additional latency | <100ms/entity | Benchmark on 16GB CPU |
| Reclassification false positives | <2% | Manual review of reclassifications |
| HITL coverage | <10% flagged | Percentage marked for human review |

---

## 5. References

1. **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011

2. **CEPTNER**: Wang et al. (2024). "CEPTNER: Contrastive learning Enhanced Prototypical network for Two-stage Few-shot Named Entity Recognition." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512

3. **NER Survey**: Li et al. (2024). "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study." arXiv:2401.10825. https://arxiv.org/abs/2401.10825

4. **Error Correction Framework**: Chen et al. (2025). "A Redundancy-Enhanced Framework for Error Correction in Named Entity Recognition." OpenReview. https://openreview.net/forum?id=2jFWhxJE5pQ

5. **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings: A Technical Report." arXiv:2402.05672. https://arxiv.org/abs/2402.05672

6. **Legal-Embed**: Wasserstoff-AI. (2024). "Legal-Embed-intfloat-multilingual-e5-large-instruct." HuggingFace. https://huggingface.co/Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct

---

## 6. Classification Errors Identified (Audit)

Analysis of file `auditoria.md` from document STSJ ICAN 3407/2025:

| Entity | Assigned Type | Correct Type | Pattern |
|--------|---------------|--------------|---------|
| `"10/10/2025"` | ORGANIZATION (Org_038) | DATE | Date confused with code |
| `"05-11-2024"` | ORGANIZATION | DATE | Date in DD-MM-YYYY format |
| `"Pura"` | LOCATION (Lugar_001) | PERSON_NAME | Short name without honorific |
| `"Finalmente"` | ORGANIZATION (Org_012) | NOT PII | Capitalized adverb |
| `"Terminaba"` | ORGANIZATION (Org_017) | NOT PII | Capitalized verb |
| `"Quien"` | ORGANIZATION | NOT PII | Capitalized pronoun |
| `"Whatsapp"` | PERSON | ORGANIZATION/PLATFORM | Platform name |

**Main pattern identified**: The RoBERTa model classifies as ORGANIZATION any capitalized word at the beginning of a sentence that it does not clearly recognize as another type.

---

## Related Documents

| Document | Relationship |
|----------|--------------|
| `auditoria.md` | Source of analyzed classification errors |
| `docs/PLAN_CORRECCION_AUDITORIA.md` | Previous correction plan (7 issues identified) |
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Previous embedding evaluation (document classification) |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Embeddings roadmap for classification |
| `ml/README.md` | ML instructions (report format) |

---

## Next Steps

1. [ ] Download model `intfloat/multilingual-e5-large` (~1.1GB)
2. [ ] Build dataset of examples per type (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
3. [ ] Implement `EntityTypeValidator` in `infrastructure/nlp/validators/`
4. [ ] Calculate and persist centroids per type
5. [ ] Integrate validator into existing NER pipeline
6. [ ] Evaluate error reduction on validation set
7. [ ] (Optional) Evaluate `Legal-Embed` vs `multilingual-e5-large`

---

```
Version: 1.0.0
Author: AlexAlves87
```
