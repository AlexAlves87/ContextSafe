# Research: Best Practices for Adversarial NER Evaluation

**Date:** 2026-01-17
**Objective:** Substantiate adversarial evaluation methodology before implementing scripts

---

## 1. Executive Summary

Recent academic literature (2024-2025) establishes that adversarial evaluation of NER models must consider:

1. **Real vs. Simulated Noise** - Real noise is significantly harder than simulated noise.
2. **Entity-level Evaluation** - Not token-level.
3. **Multiple Perturbation Categories** - OCR, Unicode, context, format.
4. **Standard Metrics** - seqeval with F1, Precision, Recall per entity type.

---

## 2. Consulted Sources

### 2.1 NoiseBench (May 2024)

**Source:** [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609)

**Key Findings:**
- Real noise (human errors, crowdsourcing, LLM) is **significantly harder** than simulated noise.
- State-of-the-art models "fall far short of their theoretically achievable upper bound".
- 6 types of real noise should be evaluated: expert errors, crowdsourcing errors, automatic annotation errors, LLM errors.

**Application to our project:**
- Our tests include real OCR noise (l/I, 0/O confusion) ✓
- We should add tests with automatic annotation errors.

### 2.2 Context-Aware Adversarial Training for NER (MIT TACL)

**Source:** [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846)

**Key Findings:**
- NER models show "Name Regularity Bias" - relying too much on the name and not context.
- Fine-tuned BERT significantly outperforms LSTM-CRF in bias tests.
- Adversarial training with learnable noise vectors improves contextual capability.

**Application to our project:**
- Our tests `negation_dni`, `example_dni`, `fictional_person` evaluate contextual capability ✓
- The v2 model (trained with noise) should be more robust.

### 2.3 OCR Impact on NER (HAL Science)

**Source:** [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document)

**Key Findings:**
- OCR noise causes a loss of ~10 F1 points (72% vs 82% on clean text).
- Should be evaluated with "various levels and types of OCR noise".
- First systematic study of OCR impact on multilingual NER.

**Application to our project:**
- Our OCR tests (5 cases) are insufficient - literature recommends more levels.
- Realistic goal: accept ~10 points of degradation with OCR.

### 2.4 seqeval - Standard Metrics

**Source:** [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval)

**Key Findings:**
- Evaluation at **entity** level, not token.
- Metrics: Precision, Recall, F1 by type and macro/micro average.
- Strict vs lenient mode for matching.

**Application to our project:**
- Our script uses fuzzy matching with ±5 chars tolerance (suitable).
- We must report metrics by entity type, not just pass/fail.

### 2.5 Enterprise Robustness Benchmark (2025)

**Source:** [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341)

**Key Findings:**
- Minor perturbations can reduce performance by up to **40 percentage points**.
- Must evaluate: text edits, formatting changes, multilingual inputs, positional variations.
- Models 4B-120B parameters all show vulnerabilities.

**Application to our project:**
- Our tests cover text edits and formatting ✓
- We must consider multilingual tests (foreign names).

---

## 3. Adversarial Test Taxonomy (Literature)

| Category | Subcategory | Example | Our Coverage |
|-----------|--------------|---------|------------------|
| **Label Noise** | Expert errors | Incorrect annotation | ❌ N/A (inference) |
| | Crowdsourcing | Inconsistencies | ❌ N/A (inference) |
| | LLM errors | Hallucinations | ❌ N/A (inference) |
| **Input Noise** | OCR corruption | l/I, 0/O, spaces | ✅ 5 tests |
| | Unicode evasion | Cyrillic, fullwidth | ✅ 3 tests |
| | Format variation | D.N.I. vs DNI | ✅ Included |
| **Context** | Negation | "NOT have DNI" | ✅ 1 test |
| | Example/illustrative | "example: 12345678X" | ✅ 1 test |
| | Fictional | Don Quijote | ✅ 1 test |
| | Legal references | Law 15/2022 | ✅ 1 test |
| **Edge Cases** | Long entities | Noble names | ✅ 1 test |
| | Short entities | J. García | ✅ 1 test |
| | Spaced entities | IBAN with spaces | ✅ 2 tests |
| **Real World** | Document patterns | Notarial, judicial | ✅ 10 tests |

---

## 4. Recommended Metrics

### 4.1 Primary Metrics (seqeval)

| Metric | Description | Usage |
|---------|-------------|-----|
| **F1 Macro** | Average F1 per entity type | Primary metric |
| **F1 Micro** | Global F1 (all entities) | Secondary metric |
| **Precision** | TP / (TP + FP) | Evaluate false positives |
| **Recall** | TP / (TP + FN) | Evaluate missed entities |

### 4.2 Adversarial Metrics

| Metric | Description | Target |
|---------|-------------|----------|
| **Pass Rate** | Tests passed / Total | ≥70% |
| **OCR Degradation** | F1_clean - F1_ocr | ≤10 points |
| **Context Sensitivity** | % correct contextual tests | ≥80% |
| **FP Rate** | False positives / Detections | ≤15% |

---

## 5. Identified Gaps in Our Script

| Gap | Severity | Action |
|-----|-----------|--------|
| No report of F1/Precision/Recall by type | Medium | Add seqeval metrics |
| Few OCR tests (5) vs recommended (10+) | Medium | Expand in next iteration |
| Does not evaluate degradation vs baseline | High | Compare with clean tests |
| No multilingual tests | Low | Add foreign names |

---

## 6. Recommendations for Our Script

### 6.1 Immediate Improvements

1. **Add seqeval metrics** - Precision, Recall, F1 per entity type.
2. **Calculate degradation** - Compare with clean version of each test.
3. **Report FP rate** - False positives as separate metric.

### 6.2 Future Improvements

1. Expand OCR tests to 10+ cases with different corruption levels.
2. Add tests with foreign names (John Smith, Mohammed Ali).
3. Implement NoiseBench-style evaluation with graded noise.

---

## 7. Conclusion

The current script covers the main categories of adversarial evaluation according to literature, but must:

1. **Improve metrics** - Use seqeval for F1/P/R by type.
2. **Expand OCR** - More corruption levels.
3. **Calculate degradation** - vs clean baseline.

**The current script is VALID for initial evaluation**, but must be iterated to fully comply with academic best practices.

---

## References

1. [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609) - ICLR 2024
2. [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846) - MIT TACL
3. [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document) - HAL Science
4. [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval) - GitHub
5. [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341) - arXiv 2025
6. [nervaluate - Entity-level NER Evaluation](https://github.com/MantisAI/nervaluate) - Based on SemEval'13

---

**Author:** AlexAlves87
**Date:** 2026-01-17
