# Critical Evaluation: Embeddings Proposal (RAG-NER) for ContextSafe

**Date:** 2026-02-07
**Objective:** Evaluate the technical validity and necessity of Module A of the proposal
"Architectural Improvements v2.1" — use of `intfloat/multilingual-e5-small` for
document pre-classification and dynamic NER configuration.

---

## 1. Executive Summary

The proposal suggests using embeddings (`intfloat/multilingual-e5-small`, ~120MB) as
"Element 0" of the NER pipeline to classify document types and dynamically adjust detection
thresholds. After investigating academic literature, verifying model specifications,
and contrasting with the current state of the ContextSafe pipeline,
**the conclusion is that the core idea has partial merit, but the proposed implementation
is over-engineered and the term "RAG-NER" is technically incorrect**.

### Verdict

| Aspect | Evaluation |
|--------|------------|
| Concept (Document-type aware NER) | Valid and useful |
| Term "RAG-NER" | Incorrect: it is not RAG |
| Proposed model (`multilingual-e5-small`) | Oversized for the task |
| Real necessity in ContextSafe | Medium: simpler alternatives available |
| Priority vs. other improvements | Low compared to HITL and audit improvements |

---

## 2. Analysis of the Term "RAG-NER"

### What is RAG in the literature

RAG (Retrieval-Augmented Generation) was introduced by Lewis et al. (NeurIPS 2020)
and specifically refers to the **retrieval of documents/passages from a knowledge base
to augment the generation** of a language model.

The actual RAG+NER papers (2024-2025) are:

| Paper | Venue | What it actually does |
|-------|-------|-----------------------|
| **RA-NER** (Dai et al.) | ICLR 2024 Tiny Papers | Retrieves similar entities from an external KB to aid NER |
| **RENER** (Shiraishi et al.) | arXiv 2410.13118 | Retrieves similar annotated examples as in-context learning for NER |
| **RA-IT Open NER** | arXiv 2406.17305 | Instruction tuning with retrieved examples for open NER |
| **IF-WRANER** | arXiv 2411.00451 | Word-level retrieval for few-shot cross-domain NER |
| **RAG-BioNER** | arXiv 2508.06504 | Dynamic prompting with RAG for biomedical NER |

### What document v2.1 proposes

What is described is NOT RAG. It is **document type classification + conditional NER
configuration**. There is no retrieval of documents/examples from a knowledge base.
There is no generation augmentation. It is a classifier followed by a switch.

**Actual diagram of the proposal:**
```
Document → Embedding (e5-small) → Cosine Similarity → Detected Type → Config Switch → NER
```

**Actual diagram of RAG-NER (RA-NER, Amazon):**
```
Input text → Retrieve similar entities from KB → Inject as context to NER → Prediction
```

They are fundamentally different architectures. Labeling the proposal as "RAG-NER"
is incorrect and could mislead in technical documentation or publications.

---

## 3. Verification of the Proposed Model

### Real specifications of `intfloat/multilingual-e5-small`

| Specification | Claim v2.1 | Real Value | Source |
|---------------|------------|------------|--------|
| Weight | ~120 MB | **448 MB (FP32), 112 MB (INT8 ONNX)** | HuggingFace |
| Parameters | Not stated | 117.65M | HuggingFace |
| Embedding dimension | Not stated | 384 | Paper arXiv:2402.05672 |
| Max tokens | 512 | 512 (correct) | HuggingFace |
| Latency | <200ms on CPU | Plausible for 512 tokens INT8 | - |
| Languages | Not stated | 94-100 languages | HuggingFace |
| License | Not stated | MIT | HuggingFace |

**Identified problems:**
- The claim of "~120 MB" is only true with INT8 ONNX quantization. The FP32 model weighs
  448 MB. The document does not clarify that quantization is required.
- In memory (runtime), the FP32 model consumes ~500MB RAM. With INT8, ~200MB.
- On the target hardware of 16GB RAM (already with RoBERTa + Presidio + spaCy loaded),
  the available margin is limited.

### Reference benchmark

| Benchmark | Result | Context |
|-----------|--------|---------|
| Mr. TyDi (retrieval MRR@10) | 64.4 avg | Good for multilingual retrieval |
| MTEB Classification (Amazon) | 88.7% accuracy | Acceptable for classification |

The model is competent for embedding tasks. The question is whether a 117M parameter
model is needed to classify ~5 types of legal documents.

---

## 4. Needs Analysis: Current State vs. Proposal

### Current ContextSafe pipeline

The `CompositeNerAdapter` already implements sophisticated contextualization mechanisms:

| Existing Mechanism | Description |
|--------------------|-------------|
| **Contextual Anchors** (Phase 1) | Forces categories according to Spanish legal context |
| **Weighted Voting** (Phase 2) | Regex=5, RoBERTa=2, Presidio=1.5, spaCy=1 |
| **GDPR Risk Tiebreaker** (Phase 3) | Priority: PERSON_NAME=100 → POSTAL_CODE=20 |
| **30+ False Positive Patterns** | Blocks legal references, DOI, ORCID, ISBN |
| **Spanish Stopwords Filter** | Avoids detection of articles/pronouns |
| **Generic Terms Whitelist** | Terms never anonymized (State, GDPR, etc.) |
| **Matrioshka (nested entities)** | Handling of nested entities |

The current pipeline does NOT have:
- Document type classification
- Per-category dynamic thresholds
- Per-document-type dynamic thresholds

### Does ContextSafe need document classification?

**Partially yes**, but not as proposed. The real benefits would be:
- Adjust IBAN threshold in invoices (stricter) vs. judgments (more relaxed)
- Enable/disable categories by context (e.g., date of birth relevant
  in criminal judgments, not in invoices)
- Reduce false positives of proper names in documents with many company names

### Simpler and more effective alternatives

| Method | Size | Latency | Estimated Accuracy | Complexity |
|--------|------|---------|--------------------|------------|
| **Regex on headers** | 0 KB (code) | <1ms | ~95%+ | Trivial |
| **TF-IDF + LogisticRegression** | ~50 KB | <5ms | ~97%+ | Low |
| **e5-small (INT8 ONNX)** | 112 MB | ~200ms | ~99% | High |
| **e5-small (FP32)** | 448 MB | ~400ms | ~99% | High |

For Spanish legal documents, headers are extremely distinctive:
- `"SENTENCIA"`, `"JUZGADO"`, `"TRIBUNAL"` → Judgment
- `"ESCRITURA"`, `"NOTARIO"`, `"PROTOCOLO"` → Notarial Deed
- `"FACTURA"`, `"BASE IMPONIBLE"`, `"IVA"` → Invoice
- `"RECURSO"`, `"APELACIÓN"`, `"CASACIÓN"` → Appeal

A classifier based on regex/keywords in the first 200 characters likely
achieves >95% accuracy without adding dependencies or significant latency.

---

## 5. Recommendation

### What IS recommended to implement

1. **Document type classification** — but with regex/keywords, not embeddings
2. **Per-category dynamic thresholds** — independent of classification
3. **Conditional NER configuration** — enable/disable rules by type

### What is NOT recommended

1. **Do not use embeddings** to classify ~5 types of legal documents
2. **Do not call this "RAG-NER"** — it is classification + conditional configuration
3. **Do not add 112-448MB of model** when regex achieves the same goal

### Suggested implementation (alternative)

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

**Cost:** 0 bytes of model, <1ms latency, ~0 additional complexity.
**Extensible:** If greater sophistication is needed in the future, it can scale
to TF-IDF or embeddings. But start simple.

---

## 6. About "Element 0" in the pipeline

If document classification is decided to be implemented (with the simple recommended method),
the correct location would be:

```
Ingested Document
    ↓
Element 0: classify_document_type(first_500_chars)  ← NEW
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=type)
    ↓
[RoBERTa | Presidio | Regex | spaCy] with thresholds adjusted according to doc_type
    ↓
Merge (current weighted voting, already works well)
```

This step is consistent with the current hexagonal architecture and requires no changes
to existing ports or adapters.

---

## 7. Conclusion

The proposal identifies a real need (document-type aware NER)
but proposes an over-engineered solution with incorrect terminology. A classifier
based on regex on document headers would achieve the same goal without adding
120-448MB of model, 200ms of additional latency, or maintenance complexity.

The investment of effort pays off much more in Module B (active audit and
HITL traceability), where ContextSafe has real regulatory compliance gaps.

---

## 8. Consulted Literature

| Reference | Venue | Relevance |
|-----------|-------|-----------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Proposed model |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | Real RAG applied to NER |
| Shiraishi et al., "RENER" | arXiv:2410.13118 (2024) | Retrieval-enhanced NER |
| arXiv 2406.17305, "RA-IT Open NER" | arXiv (2024) | Instruction tuning + retrieval |
| arXiv 2411.00451, "IF-WRANER" | arXiv (2024) | Few-shot cross-domain NER + RAG |
| arXiv 2508.06504, "RAG-BioNER" | arXiv (2025) | Dynamic prompting + RAG |
| ACL 2020 LT4Gov, "Legal-ES" | ACL Anthology | Spanish legal embeddings |
| IEEE 2024, "Fine-grained NER Spanish legal" | IEEE Xplore | Spanish legal NER |
| Frontiers AI 2025, "LegNER multilingual" | Frontiers | Multilingual legal NER |

## Related Documents

| Document | Relationship |
|----------|--------------|
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Current NER pipeline (5 elements) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Adversarial evaluation of current pipeline |
| `ml/docs/reports/2026-01-31_mejores_practicas_ml_2026.md` | ML best practices |
| `src/contextsafe/infrastructure/nlp/composite_adapter.py` | Current implementation of NER pipeline |
