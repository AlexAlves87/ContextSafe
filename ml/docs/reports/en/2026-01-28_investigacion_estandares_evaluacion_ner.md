# Research: Academic Standards for NER Evaluation

**Date:** 2026-01-28
**Author:** AlexAlves87
**Type:** Academic Literature Review
**Status:** Completed

---

## 1. Executive Summary

This research documents academic standards for evaluating NER systems, with emphasis on:
1. Entity-level metrics (SemEval 2013 Task 9)
2. Adversarial evaluation (RockNER, NoiseBench)
3. Evaluation frameworks (seqeval, nervaluate)
4. Best practices for robustness testing

### Key Findings

| Finding | Source | Impact |
|---------|--------|--------|
| 4 evaluation modes: strict, exact, partial, type | SemEval 2013 | **CRITICAL** |
| seqeval is the de facto standard for entity-level F1 | CoNLL, HuggingFace | High |
| RockNER: entity-level + context-level perturbations | EMNLP 2021 | High |
| NoiseBench: real noise >> simulated noise in difficulty | EMNLP 2024 | High |
| nervaluate provides more granular metrics than seqeval | MantisAI | Medium |

---

## 2. Methodology

### 2.1 Sources Consulted

| Source | Type | Year | Relevance |
|--------|------|------|-----------|
| SemEval 2013 Task 9 | Shared Task | 2013 | Metrics definition |
| RockNER (EMNLP 2021) | ACL Paper | 2021 | Adversarial evaluation |
| NoiseBench (EMNLP 2024) | ACL Paper | 2024 | Realistic noise |
| seqeval | Library | 2018+ | Standard implementation |
| nervaluate | Library | 2020+ | Extended metrics |
| David Batista Blog | Tutorial | 2018 | Detailed explanation |

### 2.2 Search Criteria

- "adversarial NER evaluation benchmark methodology"
- "NER robustness testing framework seqeval entity level"
- "SemEval 2013 task 9 entity level metrics"
- "RockNER adversarial NER EMNLP methodology"
- "NoiseBench NER evaluation realistic noise"

---

## 3. Entity-Level Evaluation Standards

### 3.1 SemEval 2013 Task 9: The 4 Evaluation Modes

**Source:** [Named-Entity evaluation metrics based on entity-level](https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/)

The SemEval 2013 standard defines **4 modes** of evaluation:

| Mode | Boundary | Type | Description |
|------|----------|------|-------------|
| **Strict** | Exact | Exact | Boundary AND type must match |
| **Exact** | Exact | Ignored | Only exact boundary |
| **Partial** | Overlap | Ignored | Partial overlap suffices |
| **Type** | Overlap | Exact | Overlap + correct type |

#### 3.1.1 Base Metrics Definition

| Metric | Definition |
|--------|------------|
| **COR** (Correct) | System and gold are identical |
| **INC** (Incorrect) | System and gold do not match |
| **PAR** (Partial) | System and gold have partial overlap |
| **MIS** (Missing) | Gold not captured by system (FN) |
| **SPU** (Spurious) | System produces something not in gold (FP) |
| **POS** (Possible) | COR + INC + PAR + MIS = total gold |
| **ACT** (Actual) | COR + INC + PAR + SPU = total system |

#### 3.1.2 Calculation Formulas

**For exact modes (strict, exact):**
```
Precision = COR / ACT
Recall = COR / POS
F1 = 2 * (P * R) / (P + R)
```

**For partial modes (partial, type):**
```
Precision = (COR + 0.5 × PAR) / ACT
Recall = (COR + 0.5 × PAR) / POS
F1 = 2 * (P * R) / (P + R)
```

### 3.2 seqeval: Standard Implementation

**Source:** [seqeval GitHub](https://github.com/chakki-works/seqeval)

seqeval is the standard framework for sequence labeling evaluation, validated against the CoNLL-2000 `conlleval` Perl script.

#### Features

| Feature | Description |
|---------|-------------|
| Format | CoNLL (BIO/BIOES tags) |
| Metrics | Precision, Recall, F1 per type and overall |
| Default mode | Simulates conlleval (lenient with B/I) |
| Strict mode | Only exact matches |

#### Correct Usage

```python
from seqeval.metrics import classification_report, f1_score
from seqeval.scheme import IOB2

# Strict mode (recommended for rigorous evaluation)
f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
report = classification_report(y_true, y_pred, mode='strict', scheme=IOB2)
```

**IMPORTANT:** The default mode of seqeval is lenient. For rigorous evaluation, use `mode='strict'`.

### 3.3 nervaluate: Extended Metrics

**Source:** [nervaluate GitHub](https://github.com/MantisAI/nervaluate)

nervaluate fully implements all 4 modes of SemEval 2013.

#### Advantages over seqeval

| Aspect | seqeval | nervaluate |
|--------|---------|------------|
| Modes | 2 (default, strict) | 4 (strict, exact, partial, type) |
| Granularity | Per entity type | Per type + per scenario |
| Metrics | P/R/F1 | P/R/F1 + COR/INC/PAR/MIS/SPU |

#### Usage

```python
from nervaluate import Evaluator

evaluator = Evaluator(true_labels, pred_labels, tags=['PER', 'ORG', 'LOC'])
results, results_per_tag = evaluator.evaluate()

# Access strict mode
strict_f1 = results['strict']['f1']

# Access detailed metrics
cor = results['strict']['correct']
inc = results['strict']['incorrect']
par = results['partial']['partial']
```

---

## 4. Adversarial Evaluation: Academic Standards

### 4.1 RockNER (EMNLP 2021)

**Source:** [RockNER - ACL Anthology](https://aclanthology.org/2021.emnlp-main.302/)

RockNER creates a systematic framework for creating natural adversarial examples.

#### Perturbation Taxonomy

| Level | Method | Description |
|-------|--------|-------------|
| **Entity-level** | Wikidata replacement | Substitute entities with others of the same semantic class |
| **Context-level** | BERT MLM | Generate word substitutions with LM |
| **Combined** | Both | Apply both for maximum adversariality |

#### OntoRock Benchmark

- Derived from OntoNotes
- Applies systematic perturbations
- Measures F1 degradation

#### Key Finding

> "Even the best model has a significant performance drop... models seem to memorize in-domain entity patterns instead of reasoning from the context."

### 4.2 NoiseBench (EMNLP 2024)

**Source:** [NoiseBench - ACL Anthology](https://aclanthology.org/2024.emnlp-main.1011/)

NoiseBench demonstrates that simulated noise is **significantly easier** than real noise.

#### Types of Real Noise

| Type | Source | Description |
|------|--------|-------------|
| Expert errors | Expert annotators | Fatigue errors, interpretation |
| Crowdsourcing | Amazon Turk, etc. | Non-expert errors |
| Automatic annotation | Regex, heuristics | Systematic errors |
| LLM errors | GPT, etc. | Hallucinations, inconsistencies |

#### Key Finding

> "Real noise is significantly more challenging than simulated noise, and current state-of-the-art models for noise-robust learning fall far short of their theoretically achievable upper bound."

### 4.3 Taxonomy of Perturbations for NER

Based on literature, adversarial perturbations are classified into:

| Category | Examples | Papers |
|----------|----------|--------|
| **Character-level** | Typos, OCR errors, homoglyphs | RockNER, NoiseBench |
| **Token-level** | Synonyms, inflections | RockNER |
| **Entity-level** | Replacement with similar entities | RockNER |
| **Context-level** | Modify surrounding context | RockNER |
| **Format-level** | Spaces, punctuation, casing | NoiseBench |
| **Semantic-level** | Negations, fictitious examples | Custom |

---

## 5. Review of Current Tests vs Standards

### 5.1 Current Adversarial Tests

Our script `test_ner_predictor_adversarial.py` has:

| Category | Tests | Coverage |
|----------|-------|----------|
| edge_case | 9 | Boundary conditions |
| adversarial | 8 | Semantic confusion |
| ocr_corruption | 5 | OCR errors |
| unicode_evasion | 3 | Unicode evasion |
| real_world | 10 | Real documents |

### 5.2 Identified Gaps

| Gap | Standard | Current State | Severity |
|-----|----------|---------------|----------|
| Strict vs default mode | seqeval strict | Not specified | **CRITICAL** |
| 4 SemEval modes | nervaluate | Only 1 mode | HIGH |
| Entity-level perturbations | RockNER | Not systematic | HIGH |
| Metrics COR/INC/PAR/MIS/SPU | SemEval 2013 | Not reported | MEDIUM |
| Real vs simulated noise | NoiseBench | Simulated only | MEDIUM |
| Context-level perturbations | RockNER | Partial | MEDIUM |

### 5.3 Current vs Required Metrics

| Metric | Current | Required | Gap |
|--------|---------|----------|-----|
| F1 overall | ✅ | ✅ | OK |
| Precision/Recall | ✅ | ✅ | OK |
| F1 per entity type | ❌ | ✅ | **MISSING** |
| Strict mode | ❓ | ✅ | **VERIFY** |
| COR/INC/PAR/MIS/SPU | ❌ | ✅ | **MISSING** |
| 4 SemEval modes | ❌ | ✅ | **MISSING** |

---

## 6. Recommendations for Improvement

### 6.1 CRITICAL Priority

1. **Verify strict mode in seqeval**
   ```python
   # Change from:
   f1 = f1_score(y_true, y_pred)
   # To:
   f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
   ```

2. **Report metrics per entity type**
   ```python
   report = classification_report(y_true, y_pred, mode='strict')
   ```

### 6.2 HIGH Priority

3. **Implement the 4 SemEval modes**
   - Use nervaluate instead of (or in addition to) seqeval
   - Report strict, exact, partial, type

4. **Add entity-level perturbations (RockNER style)**
   - Replace names with other Spanish names
   - Replace IDs with other valid IDs
   - Keep context, change entity

### 6.3 MEDIUM Priority

5. **Report COR/INC/PAR/MIS/SPU**
   - Allows finer error analysis
   - Distinguishes between boundary errors and type errors

6. **Add context-level perturbations**
   - Modify surrounding verbs/adjectives
   - Use BERT/spaCy for natural substitutions

---

## 7. Academic Evaluation Checklist

### 7.1 Before Reporting Results

- [ ] Specify evaluation mode (strict/default)
- [ ] Use standard CoNLL format (BIO/BIOES)
- [ ] Report F1, Precision, Recall
- [ ] Report metrics per entity type
- [ ] Document version of seqeval/nervaluate used
- [ ] Include confidence intervals if there is variance

### 7.2 For Adversarial Evaluation

- [ ] Categorize perturbations (character, token, entity, context)
- [ ] Measure relative degradation (F1_clean - F1_adversarial)
- [ ] Report pass rate by difficulty category
- [ ] Include error analysis with examples
- [ ] Compare with baseline (unmodified model)

### 7.3 For Publication/Documentation

- [ ] Describe reproducible methodology
- [ ] Publish test dataset (or generator)
- [ ] Include statistical analysis if applicable

---

## 8. Conclusions

### 8.1 Immediate Actions

1. **Review adversarial script** to verify strict mode
2. **Add nervaluate** for complete metrics
3. **Reorganize tests** according to RockNER taxonomy

### 8.2 Impact on Current Results

Current results (F1=0.784, 54.3% pass rate) could change if:
- The mode was not strict (results would be lower in strict)
- Metrics per type reveal specific weaknesses
- The 4 modes show different behavior in boundary vs type

---

## 9. References

### Academic Papers

1. **RockNER: A Simple Method to Create Adversarial Examples for Evaluating the Robustness of Named Entity Recognition Models**
   - Lin et al., EMNLP 2021
   - URL: https://aclanthology.org/2021.emnlp-main.302/

2. **NoiseBench: Benchmarking the Impact of Real Label Noise on Named Entity Recognition**
   - Merdjanovska et al., EMNLP 2024
   - URL: https://aclanthology.org/2024.emnlp-main.1011/

3. **SemEval-2013 Task 9: Extraction of Drug-Drug Interactions from Biomedical Texts**
   - Segura-Bedmar et al., SemEval 2013
   - Definition of entity-level metrics

### Tools and Libraries

4. **seqeval**
   - URL: https://github.com/chakki-works/seqeval

5. **nervaluate**
   - URL: https://github.com/MantisAI/nervaluate

6. **Named-Entity Evaluation Metrics Based on Entity-Level**
   - David Batista, 2018
   - URL: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Date:** 2026-01-28
