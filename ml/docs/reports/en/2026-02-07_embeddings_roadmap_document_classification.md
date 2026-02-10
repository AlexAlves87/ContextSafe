# Embeddings for ContextSafe: Roadmap and Activation Criteria

**Date:** 2026-02-07
**Objective:** Document the evaluated embeddings approach, the implemented alternatives,
and the criteria under which scaling to embeddings would be justifiable in the future.

---

## 1. Executive Summary

Two proposals involving embeddings were evaluated:

| Proposal | Source | Model | Decision |
|----------|--------|-------|----------|
| Document classification with embeddings | Architectural Improvements v2.1, Module A | `intfloat/multilingual-e5-small` | **Deferred** — Regex implemented |
| Gap Scanning with embeddings | Safety Net Strategy A | `intfloat/multilingual-e5-small` | **Discarded** — Cosine similarity inadequate |

**Current status:** A regex/keyword-based classifier (`DocumentTypeClassifier`) was implemented
that covers immediate requirements with 0 bytes of model, <1ms latency, and ~95% estimated accuracy
for Spanish legal documents.

Embeddings are documented as a **future scaling option** when specific criteria are met (Section 5).

---

## 2. Evaluated Proposal: Document Classification with Embeddings

### 2.1 Proposed Model

| Specification | Value |
|---------------|-------|
| Model | `intfloat/multilingual-e5-small` (Wang et al., arXiv:2402.05672) |
| Parameters | 117.65M |
| FP32 Size | 448 MB |
| INT8 ONNX Size | 112 MB |
| Embedding Dimension | 384 |
| Max tokens | 512 |
| Estimated Latency (CPU INT8) | ~200ms |
| Supported Languages | 94-100 |
| License | MIT |
| Runtime RAM (FP32) | ~500 MB |
| Runtime RAM (INT8) | ~200 MB |

**Verification source:** HuggingFace model card `intfloat/multilingual-e5-small`.

### 2.2 Proposed Architecture

```
Document → Embedding (e5-small) → Cosine Similarity vs centroids → Type → NER Config
```

This is NOT RAG-NER (the term used in proposal v2.1 is incorrect).
It is **document classification + conditional configuration**
(see `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md`, Section 2).

### 2.3 Why It Was Deferred

| Factor | Embeddings | Regex (implemented) |
|--------|------------|---------------------|
| Size | 112-448 MB | 0 bytes |
| Latency | ~200ms | <1ms |
| Estimated Accuracy | ~99% | ~95%+ |
| Complexity | High (ONNX runtime, quantization) | Trivial |
| Additional RAM | 200-500 MB | 0 |
| Maintenance | Versioned model, updates | Editable patterns |

For ~7 types of legal documents with highly distinctive headers, regex is sufficient.
The additional 4% accuracy does not justify 200MB of model nor the maintenance complexity.

---

## 3. Evaluated Proposal: Gap Scanning with Embeddings

### 3.1 Concept

Using embeddings to detect "suspicious" fragments not identified by NER:

```
Full text → Segment into chunks → Embedding of each chunk
    → Compare vs "PII risk centroid" → Alert if high similarity
```

### 3.2 Why It Was Discarded

1. **Cosine similarity does not detect PII**: Semantic similarity measures thematic closeness,
   not presence of personal data. "Juan García lives in Madrid" and "The company operates
   in Madrid" have high semantic similarity but only one contains nominal PII.

2. **A "PII risk centroid" does not exist**: Personal data (names, DNIs, IBANs, addresses)
   occupy completely disjoint semantic regions. There is no point in the embedding space
   that represents "this contains PII"
   (see Ethayarajh, EMNLP 2019, on embedding anisotropy).

3. **Reference paper**: Netflix/Cornell 2024 documents limitations of cosine similarity
   for detection of discrete vs continuous features. PII is inherently discrete (present or absent).

4. **Implemented alternative**: Deterministic Sanity Checks (`ExportValidator`,
   `src/contextsafe/domain/document_processing/services/export_validator.py`) cover
   the case of false negatives by document type more reliably and without additional dependencies.

---

## 4. Implemented Alternative: Regex Classifier

### 4.1 Implementation

```
src/contextsafe/domain/document_processing/services/document_classifier.py
```

| Feature | Detail |
|---------|--------|
| Supported Types | SENTENCIA, ESCRITURA, FACTURA, RECURSO, DENUNCIA, CONTRATO, GENERIC |
| Method | Regex over first 500 characters (uppercased) |
| Patterns per Type | 4-8 distinctive keywords |
| Fallback | Filename if text does not classify |
| Confidence | Ratio of found patterns / total per type |
| Latency | <1ms |
| Dependencies | 0 (only `re` from stdlib) |

### 4.2 Key Patterns

| Type | Main Patterns |
|------|---------------|
| SENTENCIA | `SENTENCIA`, `JUZGADO`, `TRIBUNAL`, `FALLO`, `MAGISTRAD[OA]` |
| ESCRITURA | `ESCRITURA`, `NOTAR[IÍ]`, `PROTOCOLO`, `OTORGAMIENTO` |
| FACTURA | `FACTURA`, `BASE IMPONIBLE`, `IVA`, `TOTAL FACTURA` |
| RECURSO | `RECURSO`, `APELACI[OÓ]N`, `CASACI[OÓ]N` |
| DENUNCIA | `DENUNCIA`, `ATESTADO`, `DILIGENCIAS PREVIAS` |
| CONTRATO | `CONTRATO`, `CL[AÁ]USULA`, `ESTIPULACIONES` |

### 4.3 Integration with Sanity Checks

The classifier feeds the export validation rules:

```
Document → DocumentTypeClassifier → type
                                       ↓
ExportValidator.validate(type, ...) → Applies rules SC-001..SC-004
```

| Rule | Type | Minimum Categories | Severity |
|------|------|--------------------|----------|
| SC-001 | ESCRITURA | PERSON_NAME ≥1, DNI_NIE ≥1 | CRITICAL |
| SC-002 | SENTENCIA | DATE ≥1 | WARNING |
| SC-003 | FACTURA | ORGANIZATION ≥1 | WARNING |
| SC-004 | DENUNCIA | PERSON_NAME ≥1 | WARNING |

---

## 5. Activation Criteria for Scaling to Embeddings

Embeddings should be reconsidered ONLY if **at least 2** of these criteria are met:

### 5.1 Functional Criteria

| # | Criterion | Threshold |
|---|-----------|-----------|
| CF-1 | Regex accuracy falls below 90% | Measure with validation corpus |
| CF-2 | >15 document types added | Regex becomes unmanageable |
| CF-3 | Documents without standardized header | Degraded OCR, varied scanners |
| CF-4 | Multilingual classification requirement | Documents in Catalan, Basque, Galician |

### 5.2 Infrastructure Criteria

| # | Criterion | Threshold |
|---|-----------|-----------|
| CI-1 | Available RAM in production | ≥32 GB (currently target is 16 GB) |
| CI-2 | Pipeline already uses ONNX Runtime | Avoid adding new dependency |
| CI-3 | Current pipeline latency | <2s total (margin for +200ms) |

### 5.3 Implementation Path (if activated)

```
Step 1: Collect validation corpus (50+ docs per type)
Step 2: Evaluate current regex accuracy with corpus
Step 3: If accuracy < 90%, evaluate TF-IDF + LogReg first (~50KB, <5ms)
Step 4: Only if TF-IDF < 95%, scale to e5-small INT8 ONNX
Step 5: Generate centroids per type with labeled corpus
Step 6: Validate with adversarial tests (mixed documents, degraded OCR)
```

### 5.4 Recommended Model (if scaling)

| Option | Size | Latency | Use Case |
|--------|------|---------|----------|
| TF-IDF + LogReg | ~50 KB | <5ms | First scaling step |
| `intfloat/multilingual-e5-small` INT8 | 112 MB | ~200ms | Multilingual classification |
| `BAAI/bge-small-en-v1.5` INT8 | 66 MB | ~150ms | Only English/Spanish |

**Note:** `intfloat/multilingual-e5-small` remains the best option for multilingual if needed.
But TF-IDF is the correct intermediate step before neural embeddings.

---

## 6. Impact on NER Pipeline

### 6.1 Current State (implemented)

```
Ingested Document
    ↓
DocumentTypeClassifier.classify(first_500_chars)        ← REGEX
    ↓
ConfidenceZone.classify(score, category, checksum)      ← TRIAGE
    ↓
CompositeNerAdapter.detect_entities(text)               ← NER
    ↓
ExportValidator.validate(type, entities, reviews)       ← SAFETY LATCH
    ↓
[Export allowed or blocked]
```

### 6.2 Future State (if embeddings activated)

```
Ingested Document
    ↓
DocumentTypeClassifier.classify(first_500_chars)        ← REGEX (fallback)
    ↓
EmbeddingClassifier.classify(first_512_tokens)          ← EMBEDDINGS
    ↓
merge_classifications(regex_result, embedding_result)   ← FUSION
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=type) ← CONTEXTUAL NER
    ↓
ExportValidator.validate(type, entities, reviews)       ← SAFETY LATCH
```

The classifier interface (`DocumentClassification` dataclass) is already designed to be
replaceable without changes to the rest of the pipeline.

---

## 7. Conclusion

The current approach (regex) is the correct decision for the present state of the project.
Embeddings represent an incremental improvement that is only justified in the face of
significant growth in document types or measurable degradation of accuracy.

The hexagonal architecture allows scaling without refactoring: the `DocumentTypeClassifier`
can be replaced by an `EmbeddingClassifier` implementing the same interface
(`DocumentClassification`), without impact on the rest of the pipeline.

---

## Related Documents

| Document | Relationship |
|----------|--------------|
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Critical evaluation of RAG-NER proposal |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Current NER pipeline (5 elements) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Adversarial evaluation of pipeline |
| `src/contextsafe/domain/document_processing/services/document_classifier.py` | Implemented regex classifier |
| `src/contextsafe/domain/document_processing/services/export_validator.py` | Safety Latch + Sanity Checks |
| `src/contextsafe/domain/entity_detection/services/confidence_zone.py` | Triage by confidence zones |

## References

| Reference | Venue | Relevance |
|-----------|-------|-----------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Evaluated model |
| Ethayarajh, "How Contextual are Contextualized Word Representations?" | EMNLP 2019 | Embedding anisotropy |
| Netflix/Cornell, "Limitations of Cosine Similarity" | arXiv (2024) | Limitations for discrete detection |
| Lewis et al., "Retrieval-Augmented Generation" | NeurIPS 2020 | Correct definition of RAG |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | Real RAG applied to NER |
