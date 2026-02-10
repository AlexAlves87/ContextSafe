# Research: Best Practices for PII Detection Pipeline

**Date:** 2026-01-16
**Author:** AlexAlves87
**Type:** Literature Review
**Status:** Completed

---

## Executive Summary

This research analyzes the state of the art in PII (Personally Identifiable Information) detection with a focus on Spanish legal documents. Recent academic papers (2024-2025) and production frameworks were reviewed to identify best practices in preprocessing, pipeline architecture, and post-processing.

**Main Finding:** The optimal architecture is **hybrid** (Regex → NER → Validation), not pure NER with post-processing. Additionally, OCR noise injection (30%) during training significantly improves robustness.

---

## Methodology

### Consulted Sources

| Source | Type | Year | Relevance |
|--------|------|-----|------------|
| PMC12214779 | Academic Paper | 2025 | Hybrid NLP-ML for financial PII |
| arXiv 2401.10825v3 | Survey | 2024 | NER State of the Art |
| Microsoft Presidio | Framework | 2024 | Industry Best Practices |
| Presidio Research | Toolbox | 2024 | Recognizer Evaluation |

### Search Criteria

- "NER preprocessing postprocessing best practices 2024"
- "Spanish legal documents PII detection"
- "Hybrid rule-based NLP machine learning PII"
- "Presidio pipeline architecture"

---

## Results

### 1. Optimal Pipeline Architecture

#### 1.1 Processing Order (Presidio)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Text     │ → │   Regex     │ → │   NLP NER   │ → │  Checksum   │ → │  Threshold  │
│    (OCR)    │    │  Matchers   │    │   Model     │    │ Validation  │    │   Filter    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Source:** Microsoft Presidio Documentation

**Justification:**
> "Presidio initially uses its regex matcher to identify matching entities. Then Natural Language Processing based NER model is used to detect PII autonomously. When possible, a checksum is used to validate the identified PIIs."

#### 1.2 Pipeline Components

| Component | Function | Implementation |
|------------|---------|----------------|
| **Regex Matchers** | Detect structured patterns (DNI, IBAN, phone) | Run BEFORE NER |
| **NLP NER** | Detect contextual entities (names, addresses) | Transformer model |
| **Checksum Validation** | Validate identifier integrity | DNI mod-23, IBAN mod-97 |
| **Context Enhancement** | Improve confidence with lexical context | LemmaContextAwareEnhancer |
| **Threshold Filter** | Filter by confidence score | Configurable (e.g., 0.7) |

### 2. Preprocessing

#### 2.1 Text Normalization

**Source:** PMC12214779 (Hybrid NLP-ML)

| Technique | Description | Applicability |
|---------|-------------|---------------|
| Tokenization | Division into discrete units | Universal |
| Position Marking | Character-level position marking | For span recovery |
| Unicode Normalization | Fullwidth → ASCII, zero-width removal | High for OCR |
| Abbreviation Normalization | D.N.I. → DNI | High for Spanish |

#### 2.2 Noise Injection (CRITICAL)

**Source:** PMC12214779

> "To better simulate real-world document anomalies, data preprocessing adds minor random noise like punctuation removal and text normalization."

**Recommended Implementation:**
```python
# 30% noise probability per sample
noise_probability = 0.30

# Noise types:
# - Random punctuation removal
# - OCR character substitution (l↔I, 0↔O)
# - Space collapse/expansion
# - Accent loss
```

**Impact:** Improves robustness against real scanned documents.

### 3. Model Architecture

#### 3.1 NER State of the Art (2024)

**Source:** arXiv 2401.10825v3

| Architecture | Characteristics | F1 Benchmark |
|--------------|-----------------|--------------|
| DeBERTa | Disentangled attention + enhanced mask decoder | SOTA |
| RoBERTa + CRF | Transformer + sequence coherence | +4-13% vs base |
| BERT + BiLSTM | Contextual + sequential modeling | Robust |
| GLiNER | Global attention for distant entities | Innovative |

#### 3.2 CRF Layer

**Source:** arXiv Survey

> "Applying CRF provides a robust method for NER by ensuring coherent label sequences and modeling dependencies between adjacent labels."

**Benefit:** Prevents invalid sequences like `B-PERSON I-LOCATION`.

### 4. Post-processing

#### 4.1 Checksum Validation

**Source:** Presidio Best Practices

| Type | Algorithm | Example |
|------|-----------|---------|
| Spanish DNI | letter = "TRWAGMYFPDXBNJZSQVHLCKE"[num % 23] | 12345678Z |
| Spanish NIE | Prefix X=0, Y=1, Z=2 + DNI algorithm | X1234567L |
| IBAN | ISO 7064 Mod 97-10 | ES9121000418450200051332 |
| Spanish NSS | Mod 97 on first 10 digits | 281234567890 |
| Credit Card | Luhn algorithm | 4111111111111111 |

#### 4.2 Context-Aware Enhancement

**Source:** Presidio LemmaContextAwareEnhancer

> "The ContextAwareEnhancer is a module that enhances the detection of entities by using the context of the text. It can improve detection of entities that are dependent on context."

**Implementation:**
- Search for keywords within ±N token window
- Increase/decrease score based on context
- Example: "DNI" near a number increases DNI_NIE confidence

#### 4.3 Threshold Filtering

**Source:** Presidio Tuning Guide

> "Adjust confidence thresholds on ML recognizers to balance missed cases versus over-masking."

**Recommendation:**
- High threshold (0.8+): Fewer false positives, more false negatives
- Low threshold (0.5-0.6): More coverage, more noise
- Initial pilot to calibrate

### 5. Benchmark Results

#### 5.1 Hybrid NLP-ML (PMC12214779)

| Metric | Value |
|---------|-------|
| Precision | 94.7% |
| Recall | 89.4% |
| F1-score | 91.1% |
| Accuracy (real-world) | 93.0% |

**Success Factors:**
1. Diverse training data (varied templates)
2. Lightweight framework (spaCy vs heavy transformers)
3. Balanced metrics (precision ≈ recall)
4. Context-preserving anonymization

#### 5.2 Presidio Tuning

**Source:** Presidio Research Notebook 5

> "Notebook 5 in presidio-research shows how one can configure Presidio to detect PII much more accurately, and boost the F-score by ~30%."

---

## Gap Analysis

### Comparison: Current Implementation vs Best Practices

| Aspect | Best Practice | Current Implementation | Gap |
|---------|---------------|----------------------|-----|
| Pipeline order | Regex → NER → Validation | NER → Postprocess | **CRITICAL** |
| Noise injection | 30% in training | 0% | **CRITICAL** |
| CRF layer | Add over transformer | Not implemented | MEDIUM |
| Confidence threshold | Filter by score | Not implemented | MEDIUM |
| Context enhancement | Lemma-based | Partial (regex) | LOW |
| Checksum validation | DNI, IBAN, NSS | Implemented | ✓ OK |
| Format validation | Regex patterns | Implemented | ✓ OK |

### Estimated Impact of Corrections

| Correction | Effort | Estimated F1 Impact |
|------------|----------|---------------------|
| Noise injection in dataset | Low | +10-15% on OCR |
| Regex-first pipeline | Medium | +5-10% precision |
| CRF layer | High | +4-13% (literature) |
| Confidence threshold | Low | Reduces FP 20-30% |

---

## Conclusions

### Key Findings

1. **Hybrid architecture is superior**: Combining regex (structured patterns) with NER (contextual) outperforms pure approaches.

2. **Order matters**: Regex BEFORE NER, not after. Presidio uses this order by design.

3. **Noise in training is critical**: 30% injection of OCR errors significantly improves robustness.

4. **Checksum validation is standard**: Validating structured identifiers (DNI, IBAN) is universal practice.

5. **CRF improves coherence**: Adding CRF layer over transformer prevents invalid sequences.

### Recommendations

#### HIGH Priority (Implement Immediately)

1. **Inject OCR noise in dataset v3**
   - 30% of samples with simulated errors
   - Types: l↔I, 0↔O, spaces, missing accents
   - Retrain model

2. **Restructure pipeline**
   ```
   BEFORE: Text → NER → Postprocess
   AFTER:  Text → Preprocess → Regex → NER → Validate → Filter
   ```

#### MEDIUM Priority

3. **Add confidence threshold**
   - Filter entities with score < 0.7
   - Calibrate with validation set

4. **Evaluate CRF layer**
   - Investigate `transformers` + `pytorch-crf`
   - Benchmark against current model

#### LOW Priority

5. **Advanced context enhancement**
   - Implement LemmaContextAwareEnhancer
   - Context gazetteers per entity type

---

## References

1. **PMC12214779** - "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
   - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC12214779/
   - Year: 2025

2. **arXiv 2401.10825v3** - "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study"
   - URL: https://arxiv.org/html/2401.10825v3
   - Year: 2024 (updated 2025)

3. **Microsoft Presidio** - Best Practices for Developing Recognizers
   - URL: https://microsoft.github.io/presidio/analyzer/developing_recognizers/
   - Year: 2024

4. **Presidio Research** - Evaluation Toolbox
   - URL: https://github.com/microsoft/presidio-research
   - Year: 2024

5. **Nature Scientific Reports** - "A hybrid rule-based NLP and machine learning approach"
   - URL: https://www.nature.com/articles/s41598-025-04971-9
   - Year: 2025

---

**Date:** 2026-01-16
**Version:** 1.0
