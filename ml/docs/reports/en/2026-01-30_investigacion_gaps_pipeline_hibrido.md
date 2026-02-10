# Research: Hybrid NER-PII Pipeline Gaps

**Date:** 2026-01-30
**Author:** AlexAlves87
**Objective:** Analyze critical gaps in the hybrid pipeline based on 2024-2026 academic literature
**Version:** 2.0.0 (rewritten with academic foundation)

---

## 1. Executive Summary

Five gaps were identified in ContextSafe's hybrid NER-PII pipeline. For each gap, a review of academic literature was conducted in top-tier sources (ACL, EMNLP, COLING, NAACL, TACL, Nature Scientific Reports, Springer, arXiv). The proposed recommendations are based on published evidence, not intuition.

| Gap | Priority | Reviewed Papers | Main Recommendation |
|-----|----------|-----------------|---------------------|
| Merge Strategy | **HIGH** | 7 | 3-phase pipeline (RECAP) + priority by type |
| Confidence Calibration | **HIGH** | 5 | Conformal Prediction + BRB for regex |
| Comparative Benchmark | **MEDIUM** | 3 | nervaluate (SemEval'13) with partial matching |
| Latency/Memory | **MEDIUM** | 4 | ONNX Runtime + INT8 quantization |
| Gazetteers | **LOW** | 5 | GAIN-style integration as post-filter |

---

## 2. Reviewed Literature

| Paper/System | Venue/Source | Year | Relevant Finding |
|--------------|--------------|------|------------------|
| RECAP: Hybrid PII Detection | arXiv 2510.07551 | 2025 | 3-phase pipeline: detection → multi-label disambiguation → span consolidation |
| Hybrid rule-based NLP + ML for PII (Mishra et al.) | Nature Scientific Reports | 2025 | F1 0.911 on financial docs, merge overlaps by min(start)/max(end) |
| Conformal Prediction for NER | arXiv 2601.16999 | 2026 | Prediction sets with coverage guarantees ≥95%, stratified calibration |
| JCLB: Contrastive Learning + BRB | Springer Cybersecurity | 2024 | Belief Rule Base assigns learned confidence to regex, D-CMA-ES optimizes params |
| CMiNER | Expert Systems with Applications | 2025 | Entity-level confidence estimators for noisy data |
| B2NER | COLING 2025 | 2025 | Unified NER benchmark, 54 datasets, LoRA adapters ≤50MB, outperforms GPT-4 |
| nervaluate (SemEval'13 Task 9) | GitHub/MantisAI | 2024 | COR/INC/PAR/MIS/SPU metrics with partial matching |
| T2-NER | TACL | 2023 | 2-stage span-based framework for overlapped and discontinuous entities |
| GNNer | ACL SRW 2022 | 2022 | Graph Neural Networks to reduce overlapping spans |
| GAIN: Gazetteer-Adapted Integration | SemEval-2022 | 2022 | KL divergence to adapt gazetteer network to language model, 1st in 3 tracks |
| Presidio | Microsoft Open Source | 2025 | `_remove_duplicates`: highest confidence wins, containment → larger span |
| Soft Gazetteers | ACL 2020 | 2020 | Cross-lingual entity linking for gazetteers in low-resource |
| SPLR (span-based nested NER) | J. Supercomputing | 2025 | F1 87.5 on ACE2005 with Prior Knowledge Function |
| HuggingFace Optimum + ONNX | MarkTechPost/HuggingFace | 2025 | Benchmark PyTorch vs ONNX Runtime vs quantized INT8 |
| PyDeID | PHI De-identification | 2025 | regex + spaCy NER, F1 87.9% on clinical notes, 0.48s/note |

---

## 3. Gap 1: Merge Strategy (HIGH)

### 3.1 Problem

When transformer NER and Regex detect the same entity with different boundaries or types, which one to prefer?

```
Text: "Don José García with DNI 12 345 678 Z"

NER detects:   "José García with DNI 12 345 678" (PERSON extended, partial)
Regex detects: "12 345 678 Z" (DNI_NIE, complete)
```

### 3.2 State of the Art

#### 3.2.1 RECAP Framework (arXiv 2510.07551, 2025)

The most recent and complete framework for hybrid PII merge implements **three phases**:

1.  **Phase I - Base Detection:** Regex for structured PII (IDs, phones) + LLM for unstructured (names, addresses). Produces multi-labels, overlaps, and false positives.

2.  **Phase II - Multi-label Disambiguation:** For entities with multiple labels, the text, span, and candidate labels are passed to an LLM with a contextual prompt that selects the correct label.

3.  **Phase III - Consolidation:** Two filters:
    *   **Deterministic overlap resolution:** Lower priority entities completely contained in longer spans are removed.
    *   **Contextual false positive filtering:** Short numeric sequences are verified with surrounding sentence context.

**Result:** Average F1 0.657 across 13 locales, outperforming pure NER (0.360) by 82% and zero-shot LLM (0.558) by 17%.

#### 3.2.2 Microsoft Presidio (2025)

Presidio implements `__remove_duplicates()` with simple rules:
*   **Highest confidence score wins** among overlapping detections
*   **Containment:** If a PII is contained in another, the **longest text** one is used
*   **Partial intersection:** Both are returned concatenated
*   No priority by type, only by score

#### 3.2.3 Mishra et al. (Nature Scientific Reports, 2025)

For financial documents, overlap merging:
*   `start = min(start1, start2)`
*   `end = max(end1, end2)`
*   Overlap is merged into a single consolidated entity

**Limitation:** Does not distinguish types — useless when NER detects PERSON and Regex detects DNI in the same span.

#### 3.2.4 T2-NER (TACL, 2023)

2-stage span-based framework:
1.  Extract all entity spans (overlapped and flat)
2.  Classify pairs of spans to resolve discontinuities

**Applicable Insight:** Separating span detection from their classification allows handling overlaps in a modular way.

#### 3.2.5 GNNer (ACL Student Research Workshop, 2022)

Uses Graph Neural Networks to reduce overlapping spans in span-based NER. Candidate spans are nodes in a graph, and GNN learns to remove overlapped ones.

**Applicable Insight:** Overlap is not always an error — nested entities (name inside address) are legitimate.

### 3.3 ContextSafe Current Implementation

File: `scripts/inference/ner_predictor.py`, method `_merge_regex_detections()`

```python
# Current strategy (lines 430-443):
for ner_ent in ner_entities:
    replaced = False
    for match in regex_matches:
        if overlaps(match, ner_ent):
            if regex_len > ner_len * 1.2:  # Regex 20% longer
                replaced = True
                break
    if not replaced:
        ner_to_keep.append(ner_ent)
```

**Current Rule:** If regex is ≥20% longer than NER and there is overlap → prefer regex.

### 3.4 Comparative Analysis

| System | Strategy | Handles Nested | Uses Type | Uses Confidence |
|--------|----------|----------------|-----------|-----------------|
| RECAP | 3 phases + LLM | ✅ | ✅ | Implicit |
| Presidio | Highest score | ❌ | ❌ | ✅ |
| Mishra et al. | min/max merge | ❌ | ❌ | ❌ |
| Current ContextSafe | Longer regex wins | ❌ | ❌ | ❌ |
| **Proposed** | **Type priority + validation** | **✅** | **✅** | **✅** |

### 3.5 Evidence-Based Recommendation

Inspired by RECAP (3 phases) but without relying on LLM (our requirement is CPU inference without LLM), we propose:

**Phase 1: Independent Detection**
*   Transformer NER detects semantic entities (PERSON, ORGANIZATION, LOCATION)
*   Regex detects structural entities (DNI, IBAN, PHONE, DATE)

**Phase 2: Overlap Resolution by Type Priority**

Based on RECAP evidence (regex excels in structured PII, NER in semantic):

```python
MERGE_PRIORITY = {
    # Type → (priority, preferred_source)
    # Regex with checksum = maximum confidence (evidence: Mishra et al. 2025)
    "DNI_NIE": (10, "regex"),      # Verifiable checksum
    "IBAN": (10, "regex"),         # Verifiable checksum
    "NSS": (10, "regex"),          # Verifiable checksum
    "PHONE": (8, "regex"),         # Well-defined format
    "POSTAL_CODE": (8, "regex"),   # Exact 5 digits
    "LICENSE_PLATE": (8, "regex"), # Well-defined format
    # NER excels in semantic entities (RECAP, PyDeID)
    "DATE": (6, "any"),            # Both valid
    "PERSON": (4, "ner"),          # NER better with context
    "ORGANIZATION": (4, "ner"),    # NER better with context
    "LOCATION": (4, "ner"),        # NER better with context
    "ADDRESS": (4, "ner"),         # NER better with context
}
```

**Phase 3: Consolidation**
*   **Contained** entities of different types: keep both (legitimate nested, as in GNNer)
*   **Contained** entities of same type: prefer the most specific (preferred source)
*   **Partial** overlap: prefer higher priority type
*   No overlap: keep both
*   **Contained** mixed types: keep both (GNNer inspired)

| Situation | Rule | Evidence |
|-----------|------|----------|
| No overlap | Keep both | Standard |
| Overlap, different types | Higher priority wins | RECAP Phase III |
| Containment, different types | Keep both (nested) | GNNer, T2-NER |
| Containment, same type | Preferred source per table | Presidio (larger span) |
| Partial overlap, same type | Higher confidence wins | Presidio |

---

## 4. Gap 2: Confidence Calibration (HIGH)

### 4.1 Problem

Regex returns fixed confidence (0.95), NER returns softmax probability. They are not directly comparable.

### 4.2 State of the Art

#### 4.2.1 Conformal Prediction for NER (arXiv 2601.16999, January 2026)

**Most recent and relevant paper.** Introduces framework to produce **prediction sets** with coverage guarantees:

*   Given confidence level `1-α`, generates prediction sets guaranteed to contain the correct label
*   Uses **non-conformity scores**:
    *   `nc1`: `1 - P̂(y|x)` — based on probability, penalizes low confidence
    *   `nc2`: cumulative probability in ranked sequences
    *   `nc3`: based on rank, produces fixed-size sets

**Key Findings:**
*   `nc1` substantially outperforms `nc2` (which produces "extremely large" sets)
*   **Length-stratified calibration** corrects systematic miscalibration in long sequences
*   **Language calibration** improves coverage (English: 93.82% → 96.24% after stratification)
*   Šidák correction for multiple entities: per-entity confidence = `(1-α)^(1/s)` for `s` entities

**Applicability to ContextSafe:** Length-stratified calibration is directly applicable. Long texts (contracts) may have systematically different scores than short texts.

#### 4.2.2 JCLB: Belief Rule Base (Springer Cybersecurity, 2024)

Introduces an approach to **assign confidence to regex rules** in a learned manner:

*   Regex rules are formalized as a **Belief Rule Base (BRB)**
*   Each rule has **belief degrees** optimized by D-CMA-ES
*   The BRB filters entity categories and evaluates their correctness simultaneously
*   BRB parameters are optimized against training data

**Key Insight:** Regex rules should NOT have fixed confidence. Their confidence must be learned/calibrated against real data.

#### 4.2.3 CMiNER (Expert Systems with Applications, 2025)

Designs **entity-level confidence estimators** that:
*   Evaluate initial quality of noisy datasets
*   Assist during training by adjusting weights

**Applicable Insight:** Entity-level confidence (not token) is more useful for merge decisions.

#### 4.2.4 Conf-MPU (Zhou et al., 2022)

Token-level binary classification to predict probability of each token being an entity, then uses confidence scores for risk estimation.

**Applicable Insight:** Separating "is this an entity?" from "what type?" allows calibrating in two stages.

### 4.3 ContextSafe Current Implementation

```python
# Regex patterns (spanish_id_patterns.py):
RegexMatch(..., confidence=0.95)  # Hardcoded fixed value

# NER model:
confidence = softmax(logits).max()  # Real probability [0.5-0.99]

# Checksum adjustment (ner_predictor.py, lines 473-485):
if is_valid:
    final_confidence = min(match.confidence * 1.1, 0.99)
elif checksum_conf < 0.5:
    final_confidence = match.confidence * 0.5
```

### 4.4 Problem Analysis

| Source | Confidence | Calibrated | Problem |
|--------|------------|------------|---------|
| NER softmax | 0.50-0.99 | ✅ | May be miscalibrated for long texts (CP 2026) |
| Regex without checksum | 0.95 fixed | ❌ | Overconfidence in ambiguous matches |
| Regex with valid checksum | 0.99 | ⚠️ | Appropriate for IDs with checksum |
| Regex with invalid checksum | 0.475 | ✅ | Appropriate penalty |

### 4.5 Evidence-Based Recommendation

#### Level 1: Base confidence differentiated by type (inspired by JCLB/BRB)

Do not use fixed confidence. Assign **base confidence** according to available validation level:

```python
REGEX_BASE_CONFIDENCE = {
    # With verifiable checksum (maximum confidence, Mishra et al. 2025)
    "DNI_NIE":  {"checksum_valid": 0.98, "checksum_invalid": 0.35, "format_only": 0.70},
    "IBAN":     {"checksum_valid": 0.99, "checksum_invalid": 0.30, "format_only": 0.65},
    "NSS":      {"checksum_valid": 0.95, "checksum_invalid": 0.35, "format_only": 0.65},

    # Without checksum, with well-defined format
    "PHONE":         {"with_prefix": 0.90, "without_prefix": 0.75},
    "POSTAL_CODE":   {"valid_province": 0.85, "format_only": 0.70},
    "LICENSE_PLATE": {"modern_format": 0.90, "old_format": 0.80},

    # Ambiguous
    "DATE":  {"full_textual": 0.85, "partial": 0.60, "ambiguous": 0.50},
    "EMAIL": {"standard": 0.95},
}
```

**Justification:** JCLB showed that rule confidence should be learned/differentiated, not fixed. Without access to training data to optimize BRB (like D-CMA-ES in JCLB), we use heuristics based on available validation level (checksum > format > simple match).

#### Level 2: Stratified calibration (inspired by CP 2026)

For Transformer NER, consider text length calibration:
*   Short texts (1-10 tokens): minimum confidence threshold 0.60
*   Medium texts (11-50 tokens): threshold 0.50
*   Long texts (51+ tokens): threshold 0.45

**Justification:** Conformal Prediction paper (2026) showed that long texts have systematically different coverage. Stratifying by length corrects this miscalibration.

#### Level 3: Operational confidence threshold

Based on RECAP and PyDeID:
*   **≥0.80:** Automatic anonymization
*   **0.50-0.79:** Anonymization with "review" flag
*   **<0.50:** Do not anonymize, report as "doubtful"

---

## 5. Gap 3: Comparative Benchmark (MEDIUM)

### 5.1 State of the Art in NER Evaluation

#### 5.1.1 Metrics: seqeval vs nervaluate

| Framework | Type | Partial Match | Level | Standard |
|-----------|------|---------------|-------|----------|
| **seqeval** | Strict entity-level | ❌ | Full entity | CoNLL eval |
| **nervaluate** | Multi-scenario | ✅ | COR/INC/PAR/MIS/SPU | SemEval'13 Task 9 |

**seqeval** (CoNLL standard):
*   Precision, Recall, F1 at full entity level
*   Only exact match: correct type AND full span
*   Micro/macro average per type

**nervaluate** (SemEval'13 Task 9):
*   4 scenarios: strict, exact, partial, type
*   5 categories: COR (correct), INC (incorrect type), PAR (partial span), MIS (missed), SPU (spurious)
*   Partial matching: `Precision = (COR + 0.5 × PAR) / ACT`

**Recommendation:** Use **both** metrics. seqeval for comparability with literature (CoNLL), nervaluate for finer error analysis.

#### 5.1.2 B2NER Benchmark (COLING 2025)

*   54 datasets, 400+ entity types, 6 languages
*   Unified benchmark for Open NER
*   LoRA adapters ≤50MB outperform GPT-4 by 6.8-12.0 F1

**Applicability:** B2NER confirms that LoRA is viable for specialized NER, but requires quality data (54 refined datasets).

### 5.2 Available ContextSafe Data

| Configuration | F1 Strict | Pass Rate | Source |
|---------------|-----------|-----------|--------|
| NER only (legal_ner_v2 base) | 0.464 | 28.6% | Baseline |
| NER + Normalizer | 0.492 | 34.3% | ML Cycle |
| NER + Regex | 0.543 | 45.7% | ML Cycle |
| **Full Pipeline (5 elem)** | **0.788** | **60.0%** | ML Cycle |
| LoRA fine-tuning pure | 0.016 | 5.7% | Exp. 2026-02-04 |
| GLiNER zero-shot | 0.325 | 11.4% | Exp. 2026-02-04 |

### 5.3 Pending Benchmark

| Test | Metric | Status |
|------|--------|--------|
| Evaluate with nervaluate (partial matching) | COR/INC/PAR/MIS/SPU | Pending |
| Only Regex (without NER) | F1 strict + partial | Pending |
| NER + Checksum (without regex patterns) | F1 strict + partial | Pending |
| Entity-type breakdown comparison | Per-type F1 | Pending |

### 5.4 Recommendation

Create script `scripts/evaluate/benchmark_nervaluate.py` that:
1.  Runs full pipeline against adversarial test set
2.  Reports seqeval metrics (strict, for comparability)
3.  Reports nervaluate metrics (4 scenarios, for error analysis)
4.  Breaks down by entity type
5.  Compares ablations (NER only, Regex only, Hybrid)

---

## 6. Gap 4: Latency/Memory (MEDIUM)

### 6.1 Objective

| Metric | Target | Justification |
|--------|--------|---------------|
| Latency | <500ms per A4 page (~600 tokens) | Responsive UX |
| Memory | <2GB model in RAM | Deployment on 16GB |
| Throughput | >10 pages/second (batch) | Bulk processing |

### 6.2 State of the Art in Inference Optimization

#### 6.2.1 ONNX Runtime + Quantization (HuggingFace Optimum, 2025)

HuggingFace Optimum allows:
*   Export to ONNX
*   Graph optimization (operator fusion, redundant node elimination)
*   INT8 quantization (dynamic or static)
*   Integrated benchmarking: PyTorch vs torch.compile vs ONNX vs ONNX quantized

**Reported Results:**
*   TensorRT-Optimized: up to 432 inferences/second (ResNet-50, not NER)
*   ONNX Runtime: typical 2-4x speedup over vanilla PyTorch on CPU

#### 6.2.2 PyDeID (2025)

Hybrid regex + spaCy NER system for de-identification:
*   **0.48 seconds/note** vs 6.38 seconds/note of base system
*   13x speedup factor with optimized regex + NER
*   F1 87.9% with the fast pipeline

**Direct Applicability:** PyDeID demonstrates that a hybrid regex+NER pipeline can process 1 document in <0.5s.

#### 6.2.3 Transformer Optimization Pipeline

```
PyTorch FP32 → ONNX Export → Graph Optimization → INT8 Quantization
    baseline        2x             2-3x                  3-4x
```

### 6.3 Theoretical Estimation for ContextSafe

| Component | CPU (PyTorch) | CPU (ONNX INT8) | Memory |
|-----------|---------------|-----------------|--------|
| TextNormalizer | <1ms | <1ms | ~0 |
| NER (RoBERTa-BNE ~125M) | ~200-400ms | ~50-100ms | ~500MB → ~200MB |
| Checksum validators | <1ms | <1ms | ~0 |
| Regex patterns | <5ms | <5ms | ~0 |
| Date patterns | <2ms | <2ms | ~0 |
| Boundary refinement | <1ms | <1ms | ~0 |
| **Total** | **~210-410ms** | **~60-110ms** | **~500MB → ~200MB** |

**Conclusion:** With ONNX INT8 it should meet <500ms/page with wide margin.

### 6.4 Recommendation

1.  **First measure** current latency with PyTorch (script `benchmark_latency.py`)
2.  **If it meets** <500ms on CPU: document and defer ONNX optimization
3.  **If it fails**: export ONNX + INT8 quantization (prioritize)
4.  **Document** process for replicability in other languages

---

## 7. Gap 5: Gazetteers (LOW)

### 7.1 State of the Art

#### 7.1.1 GAIN: Gazetteer-Adapted Integration Network (SemEval-2022)

*   **KL divergence adaptation:** Gazetteer network adapts to language model minimizing KL divergence
*   **2 stages:** First adapt gazetteer to model, then train supervised NER
*   **Result:** 1st in 3 tracks (Chinese, Code-mixed, Bangla), 2nd in 10 tracks
*   **Insight:** Gazetteers are most useful when integrated as an additional feature, not as a direct lookup

#### 7.1.2 Gazetteer-Enhanced Attentive Neural Networks (EMNLP 2019)

*   Auxiliary network encoding "name regularity" using only gazetteers
*   Incorporated into main NER for better recognition
*   **Reduces training data requirements** significantly

#### 7.1.3 Soft Gazetteers for Low-Resource NER (ACL 2020)

*   In languages without exhaustive gazetteers, use cross-lingual entity linking
*   Wikipedia as knowledge source
*   Experimented in 4 low-resource languages

#### 7.1.4 Spurious Matching Reduction

*   Raw gazetteers generate **many false positives** (spurious matching)
*   Filtering by "entity popularity" improves F1 by +3.70%
*   **Clean Gazetteers > Full Gazetteers**

### 7.2 Available Gazetteers in ContextSafe

| Gazetteer | Records | Source | In Pipeline |
|-----------|---------|--------|-------------|
| Surnames | 27,251 | INE | ❌ |
| Male names | 550 | INE | ❌ |
| Female names | 550 | INE | ❌ |
| Archaic names | 6,010 | Generated | ❌ |
| Municipalities | 8,115 | INE | ❌ |
| Postal codes | 11,051 | INE | ❌ |

### 7.3 Evidence-Based Recommendation

**Do not integrate gazetteers into the core pipeline** for the following literature-based reasons:

1.  **Spurious matching** (EMNLP 2019): Without popularity filtering, gazetteers generate false positives
2.  **Pipeline already works** (F1 0.788): Marginal benefit of gazetteers is low
3.  **Replicability complexity:** Gazetteers are language-specific, each language needs different sources

**Recommended usage as post-filter:**
*   **Name validation:** If NER detects PERSON, verify if name/surname is in gazetteer → boost confidence +0.05
*   **Postal Code validation:** If regex detects POSTAL_CODE 28001, verify if it corresponds to real municipality → boost confidence +0.10
*   **DO NOT use for detection:** Do not search gazetteer names directly in text (risk of spurious matching)

---

## 8. Action Plan

### 8.1 Immediate Actions (High Priority)

| Action | Academic Basis | File |
|--------|----------------|------|
| Implement 3-phase merge strategy | RECAP (2025) | `ner_predictor.py` |
| Remove fixed 0.95 confidence in regex | JCLB/BRB (2024) | `spanish_id_patterns.py` |
| Add priority table by type | RECAP, Presidio | `ner_predictor.py` |

### 8.2 Improvement Actions (Medium Priority)

| Action | Academic Basis | File |
|--------|----------------|------|
| Evaluate with nervaluate (partial matching) | SemEval'13 Task 9 | `benchmark_nervaluate.py` |
| Create latency benchmark | PyDeID (2025) | `benchmark_latency.py` |
| Document length calibration | CP NER (2026) | Replicability guide |

### 8.3 Deferred Actions (Low Priority)

| Action | Academic Basis | File |
|--------|----------------|------|
| Gazetteers as post-filter | GAIN (2022) | `ner_predictor.py` |
| Export ONNX + INT8 | HuggingFace Optimum | `scripts/export/` |

---

## 9. Conclusions

### 9.1 Main Research Findings

1.  **Hybrid pipeline is SOTA for PII** — RECAP (2025), PyDeID (2025), and Mishra et al. (2025) confirm that regex + NER outperforms each component separately.

2.  **Regex confidence should not be fixed** — JCLB (2024) demonstrated that assigning learned confidence to rules significantly improves performance.

3.  **Text length calibration is important** — Conformal Prediction (2026) demonstrated systematic miscalibration in long sequences.

4.  **nervaluate complements seqeval** — SemEval'13 Task 9 offers partial matching metrics that capture boundary errors that seqeval ignores.

5.  **ONNX INT8 is viable for <500ms latency** — PyDeID demonstrated <0.5s/document with optimized hybrid pipeline.

### 9.2 Status of Evaluated Models

| Model | Evaluation | Adversarial F1 | Status |
|-------|------------|----------------|--------|
| **RoBERTa-BNE CAPITEL NER** (`legal_ner_v2`) | Full 5-element pipeline | **0.788** | **ACTIVE** |
| GLiNER-PII (zero-shot) | Evaluated on 35 adversarial tests | 0.325 | Discarded (inferior) |
| LoRA Legal-XLM-R-base (`lora_ner_v1`) | Evaluated on 35 adversarial tests | 0.016 | Discarded (overfitting) |
| MEL (Spanish Legal Model) | Investigated | N/A (no NER version) | Discarded |
| Legal-XLM-R-base (joelniklaus) | Investigated for multilingual | N/A | Pending future expansion |

> **Note:** The pipeline's base model is `roberta-base-bne-capitel-ner` (RoBERTa-BNE, ~125M params, vocab 50,262),
> fine-tuned with synthetic data v3 (30% noise injection). It is **NOT** XLM-RoBERTa.

### 9.3 Recommendations for Replicability

To replicate in other languages, adapters are:

| Component | Spain (ES) | France (FR) | Italy (IT) | Adaptation |
|-----------|------------|-------------|------------|------------|
| NER Model | RoBERTa-BNE CAPITEL | JuriBERT/CamemBERT | Legal-BERT-IT | Fine-tune NER per language |
| Multilingual NER (alternative) | Legal-XLM-R | Legal-XLM-R | Legal-XLM-R | Single multilingual model |
| Regex patterns | DNI/NIE, IBAN ES | CNI, IBAN FR | CF, IBAN IT | New regex file |
| Checksum validators | mod-23 (DNI) | mod-97 (IBAN) | Codice Fiscale | New validator |
| Merge priorities | Table 3.5 | Same structure | Same structure | Adjust types |
| Confidence calibration | Table 4.5 | Same structure | Same structure | Calibrate by local type |
| Gazetteers | INE | INSEE | ISTAT | National sources |

---

**Date:** 2026-01-30
**Version:** 2.0.0 — Rewritten with academic research (v1.0 lacked foundation)
