# Research: ML Best Practices 2025-2026 for Legal NER-PII

**Date:** 2026-01-31
**Author:** AlexAlves87
**Objective:** Identify state-of-the-art techniques applicable to the ContextSafe NER-PII pipeline
**Scope:** Top-tier literature (ICLR, EMNLP, NeurIPS, NAACL, Nature) published 2025-2026

---

## 1. Executive Summary

Systematic review of recent literature (2025-2026) in machine learning applied to Named Entity Recognition (NER) and PII detection. **8 significant advancements** are identified compared to the practices documented in our previous report (2026-01-30_investigacion_finetuning_legal_xlm_r), with direct impact on the Legal-XLM-RoBERTa training strategy for ContextSafe.

### Key Findings

| # | Technique | Source | Impact for ContextSafe |
|---|-----------|--------|------------------------|
| 1 | LoRA/QLoRA with high rank (128-256) on all layers | Unsloth, COLING 2025 | Reduces VRAM from 16GB to ~4GB without F1 loss |
| 2 | RandLoRA (full-rank PEFT) | ICLR 2025 | Eliminates standard LoRA plateau |
| 3 | Multi-perspective Knowledge Distillation | IGI Global 2025 | +2.5-5.8% F1 with limited data |
| 4 | LLM synthetic generation for NER | EMNLP 2025 | Bootstrap for languages without annotated corpus |
| 5 | GLiNER zero-shot PII | NAACL 2024 + updates 2025 | Baseline 81% F1 without training |
| 6 | Hybrid NER (transformer + rules) | Nature Sci. Reports 2025 | 94.7% precision in financial documents |
| 7 | RECAP (regex + contextual LLM) | NeurIPS 2025 | +82% over fine-tuned NER, +17% over zero-shot |
| 8 | Selective DAPT (not universal) | ICLR 2025 | DAPT does not always improve; requires prior evaluation |

### Diagnosis: Current State vs. State of the Art

| Capability | Current ContextSafe | State of the Art 2026 | Gap |
|------------|---------------------|-----------------------|-----|
| Fine-tuning | Full FT planned | LoRA/RandLoRA (PEFT) | **High** |
| Training data | Gold labels only | Gold + synthetic (LLM) | **High** |
| NER Pipeline | Hybrid (regex+ML) | RECAP (regex+contextual LLM) | Medium |
| Zero-shot baseline | Not established | GLiNER ~81% F1 | **High** |
| DAPT | Planned universal | Selective (evaluate first) | Medium |
| Inference | ONNX INT8 planned | LoRA adapters + quantization | Low |
| Evaluation | SemEval entity-level | + adversarial + cross-lingual | Medium |
| Spanish legal model | No baseline | MEL (XLM-R-large, 82% F1) | **High** |

---

## 2. Review Methodology

### 2.1 Inclusion Criteria

| Criteria | Value |
|----------|-------|
| Period | January 2025 - February 2026 |
| Venues | ICLR, EMNLP, NeurIPS, NAACL, ACL, Nature, ArXiv (pre-print with citations) |
| Relevance | NER, PII, PEFT, DAPT, legal NLP, multilingual |
| Languages | Multilingual (with emphasis on Spanish) |

### 2.2 Searches Performed

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

## 3. Results by Thematic Area

### 3.1 Parameter-Efficient Fine-Tuning (PEFT)

#### 3.1.1 LoRA/QLoRA: Optimal Configurations 2025-2026

Recent literature consolidates best practices for LoRA applied to NER:

| Hyperparameter | Recommended Value | Source |
|----------------|-------------------|--------|
| Rank (r) | 128-256 | Unsloth Docs, Medical NER studies |
| Alpha (α) | 2×r (256-512) | Heuristic validated empirically |
| Target modules | Attention **+ MLP** (all layers) | Databricks, Lightning AI |
| Learning rate | 2e-4 (start), range 5e-6 to 2e-4 | Unsloth, Medium/QuarkAndCode |
| Epochs | 1-3 (overfitting risk >3) | Consensus multiple sources |
| Dropout | 0.05 (specialized domains) | Medical NER studies |

**Recent empirical evidence:**

| Paper | Model | Task | F1 | Venue |
|-------|-------|------|----|-------|
| B2NER | LoRA adapters ≤50MB | Universal NER (15 datasets, 6 languages) | +6.8-12.0 F1 vs GPT-4 | COLING 2025 |
| LLaMA-3-8B Financial NER | LoRA r=128 | Financial NER | 0.894 micro-F1 | ArXiv Jan 2026 |
| Military IE | GRPO + LoRA | Information Extraction | +48.8% absolute F1 | 2025 |

**LoRA vs QLoRA Decision:**
- **LoRA**: Slightly faster speed, ~0.5% more accurate, 4× more VRAM
- **QLoRA**: Use when VRAM < 8GB or model > 1B parameters
- **For Legal-XLM-RoBERTa-base (184M)**: LoRA is viable on RTX 5060 Ti 16GB

#### 3.1.2 RandLoRA: Full-Rank PEFT

**Paper:** "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models"
**Venue:** ICLR 2025 (ArXiv: 2502.00987)

**Problem solved:**
Standard LoRA produces low-rank updates, limiting representation capacity. Increasing rank (r) does not close the gap with full fine-tuning: a performance *plateau* exists.

**Innovation:**
- Generates **non-trainable** random low-rank matrices (linearly independent bases)
- Learns only **diagonal scaling coefficients**
- Linear combination produces **full-rank** updates
- Same number of trainable parameters as LoRA, but without rank restriction

**Results:**

| Model | Task | LoRA | RandLoRA | Full FT |
|-------|------|------|----------|---------|
| DinoV2 | Vision | 85.2 | 87.1 | 87.4 |
| CLIP | Vision-language | 78.6 | 81.3 | 82.0 |
| Llama3-8B | Reasoning | 71.2 | 73.8 | 74.1 |

**Implication:** RandLoRA closes >90% of the LoRA→Full FT gap with the same trainable parameters.

### 3.2 Knowledge Distillation (LLM → Small Model)

#### 3.2.1 Multi-Perspective Distillation for NER

**Paper:** "Multi-Perspective Knowledge Distillation of LLM for NER"
**Source:** IGI Global Scientific Publishing, 2025

**Pipeline:**
1. **Teacher:** Qwen14B (14B parameters)
2. **Generation:** Chain-of-Thought (CoT) to generate intermediate reasoning about entities
3. **Alignment:** Multi-perspective knowledge (entity type, context, boundaries)
4. **Student:** Small NER model with DoRA (LoRA variant)

**Results over state of the art:**

| Metric | Improvement |
|--------|-------------|
| Precision | +3.46% |
| Recall | +5.79% |
| F1-score | +2.54% |

**Additional capability:** Strong performance in few-shot (limited data).

#### 3.2.2 Application to ContextSafe

Proposed pipeline:
```
GPT-4 / Llama-3-70B (teacher)
    ↓ Generates PII annotations with CoT reasoning
    ↓ On unannotated Spanish legal texts
Legal-XLM-RoBERTa-base (student)
    ↓ Fine-tune with DoRA/LoRA
    ↓ Using generated data + gold labels
Deployable PII model (~400MB ONNX)
```

### 3.3 Synthetic Data Generation with LLMs

#### 3.3.1 Rigorous Evaluation (EMNLP 2025)

**Paper:** "A Rigorous Evaluation of LLM Data Generation Strategies for NER"
**Venue:** EMNLP 2025 Main Conference (Paper ID: 2025.emnlp-main.418)

**Experimental Design:**
- **Languages:** 11 (including multilingual)
- **Tasks:** 3 different
- **Generator LLMs:** 4 models
- **Downstream models:** 10 (fine-tuned XLM-R)
- **Metric:** Average F1 gold vs artificial

**Key Findings:**

| Finding | Evidence |
|---------|----------|
| Quality > Quantity | Small, clean, consistent datasets outperform large noisy ones |
| Format matters | Consistent JSONL is critical for performance |
| Effective for low-resource | Synthetic data viable for languages without annotated corpus |
| Comparable to gold | In some languages/tasks, synthetic data reaches 90-95% of gold performance |

#### 3.3.2 Cross-lingual NER Zero-shot (EMNLP 2025)

**Paper:** "Zero-shot Cross-lingual NER via Mitigating Language Difference: An Entity-aligned Translation Perspective"
**Venue:** EMNLP 2025

**Technique:** Entity-aligned translation for cross-lingual transfer. Relevant for expanding ContextSafe to new languages starting from the Spanish model.

### 3.4 GLiNER: Zero-Shot NER for PII

**Paper:** "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer"
**Venue:** NAACL 2024 (PII models updated September 2025, Wordcab collaboration)

**Architecture:**
- Bidirectional Encoder (BiLM)
- Input: entity type prompts + text
- Output: parallel entity extraction (advantage over LLM sequential generation)
- Does not require predefined categories: entities specified at runtime

**Available PII models (2025):**

| Model | Size | F1 |
|-------|------|----|
| gliner-pii-edge-v1.0 | ~100MB | ~75% |
| gliner-pii-small-v1.0 | ~200MB | ~78% |
| gliner-pii-base-v1.0 | ~440MB | **80.99%** |
| gliner-pii-large-v1.0 | ~1.3GB | ~80% |

**Existing Integration:** GLiNER integrates with Microsoft Presidio (which ContextSafe already uses).

**Relevance:**
- **Immediate baseline:** 81% F1 without training, against which to measure our fine-tuned model
- **Ensemble:** Use GLiNER for rare PII categories where there is no training data
- **Cross-validation:** Compare GLiNER predictions vs Legal-XLM-R to detect errors

### 3.5 Hybrid Approaches (Transformer + Rules)

#### 3.5.1 Hybrid NER for PII in Financial Documents

**Paper:** "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
**Venue:** Nature Scientific Reports, 2025 (DOI: 10.1038/s41598-025-04971-9)

**Results:**

| Metric | Synthetic Dataset | Real Documents |
|--------|-------------------|----------------|
| Precision | **94.7%** | ~93% |
| Recall | 89.4% | ~93% |
| F1-score | 91.1% | ~93% |

**Architecture:** NLP Rules + ML + Custom NER, scalable.

#### 3.5.2 RECAP: Regex + Contextual LLM

**Paper:** Presented at NeurIPS 2025
**Methodology:** Deterministic Regex + Context-aware LLMs for multilingual PII

**Comparative Results:**

| Comparison | RECAP Improvement |
|------------|-------------------|
| vs fine-tuned NER | **+82% weighted F1** |
| vs zero-shot LLMs | **+17% weighted F1** |

**Benchmark:** nervaluate (entity-level evaluation)

**Implication for ContextSafe:** Our current pipeline (Regex + Presidio + RoBERTa) already follows this hybrid pattern. RECAP validates that this architecture is the most effective according to 2025 evidence.

### 3.6 Domain Adaptive Pre-Training (DAPT): Critical Review

#### 3.6.1 DAPT Is Not Universal

**Paper:** "Continual Pre-Training is (not) What You Need in Domain Adaptation"
**Venue:** ICLR 2025

**Key Conclusions:**

| Scenario | Does DAPT Help? | Evidence |
|----------|-----------------|----------|
| Specialized vocabulary (legal, medical) | **Yes** | Familiarizes with legal style |
| Logical reasoning (civil law) | **Yes** | Improves understanding of relationships |
| Tasks with abundant data | **Not necessarily** | Direct fine-tuning may be sufficient |
| Without catastrophe mitigation | **Detrimental** | Catastrophic forgetting degrades general performance |

**Recommended Mitigation:**
- Adapter layers / LoRA during DAPT (no full fine-tuning of backbone)
- Gradual unfreezing
- Evaluate BEFORE and AFTER DAPT on NER-PII benchmark

#### 3.6.2 ICL-APT: Efficient Alternative

**Concept:** In-Context Learning Augmented Pre-Training

**Pipeline:**
1. Sample texts from target corpus
2. Retrieve similar documents from domain (semantic retrieval)
3. Augment context with definitions, abbreviations, terminology
4. Continue pre-training with MLM on augmented context

**Advantage:** More efficient with limited corpus. Does not require millions of documents like traditional DAPT.

**Application:** For each Spanish legal document, retrieve similar sentences + add definitions of PII categories as pre-training context.

### 3.7 Spanish Legal Models (2025 Baselines)

#### 3.7.1 MEL (Modelo de Español Legal)

**Paper:** "MEL: Legal Spanish language model"
**Date:** January 2025 (ArXiv: 2501.16011)

| Aspect | Detail |
|--------|--------|
| Base | XLM-RoBERTa-large |
| Training data | BOE (Official State Gazette), congress texts |
| Tasks | Legal classification, NER |
| Macro F1 | ~0.82 (15 labels) |
| Comparison | Outperforms xlm-roberta-large, legal-xlm-roberta-large, RoBERTalex |

#### 3.7.2 3CEL Corpus

**Paper:** "3CEL: a Corpus of Legal Spanish Contract Clauses"
**Date:** January 2025 (ArXiv: 2501.15990)

Corpus of Spanish legal contract clauses with annotations. Potentially useful as training or evaluation data.

---

## 4. Mandatory Pre-readings

> **IMPORTANT:** Before executing any phase of the plan, the model must read these documents in the indicated order to understand the full context of the project, decisions made, and current state.

### 4.1 Level 0: Project Identity and Rules

| # | File | Purpose | Mandatory |
|---|------|---------|-----------|
| 0.1 | `ml/README.md` | Operational rules, file structure, workflow | **Yes** |
| 0.2 | `README.md` (project root) | Hexagonal architecture, ContextSafe domain, NER pipeline, anonymization levels | **Yes** |

### 4.2 Level 1: ML Cycle History (read in chronological order)

These documents narrate the full evolution of the NER v2 model, from baseline to current state. Without them, it is not understood why certain decisions were made.

| # | File | Key Content |
|---|------|-------------|
| 1.1 | `docs/reports/2026-01-15_estado_proyecto_ner.md` | Initial state of NER project, v1 vs v2 model |
| 1.2 | `docs/reports/2026-01-16_investigacion_pipeline_pii.md` | Investigation of existing PII pipelines |
| 1.3 | `docs/reports/2026-01-28_investigacion_hybrid_ner.md` | Architectural decision: hybrid pipeline (Regex+ML) |
| 1.4 | `docs/reports/2026-01-28_investigacion_estandares_evaluacion_ner.md` | Adoption of SemEval 2013 Task 9 (COR/INC/PAR/MIS/SPU) |
| 1.5 | `docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | **ESSENTIAL** - Full ML cycle: 5 integrated elements, final metrics (F1 0.788), lessons learned |

### 4.3 Level 2: The 5 Pipeline Elements (technical detail)

Each element documents a concrete improvement integrated into `ner_predictor.py`. Read if needing to understand or modify the pipeline.

| # | File | Element | Impact |
|---|------|---------|--------|
| 2.1 | `docs/reports/2026-02-04_text_normalizer_impacto.md` | Elem.1: Text normalization | OCR noise → clean text |
| 2.2 | `docs/reports/2026-02-04_checksum_validators_standalone.md` | Elem.2: Checksum validation | DNI, IBAN, NSS with mathematical verification |
| 2.3 | `docs/reports/2026-02-05_regex_patterns_standalone.md` | Elem.3: Spanish regex patterns | License plates, postal codes, phones |
| 2.4 | `docs/reports/2026-02-05_date_patterns_integration.md` | Elem.4: Textual dates | "12 de enero de 2024" |
| 2.5 | `docs/reports/2026-02-06_boundary_refinement_integration.md` | Elem.5: Boundary refinement | PAR→COR (16 partials corrected) |

### 4.4 Level 3: Investigations for Next Phase

These reports ground the decisions for the Legal-XLM-RoBERTa fine-tuning plan.

| # | File | Key Content |
|---|------|-------------|
| 3.1 | `docs/reports/2026-01-29_investigacion_modelos_legales_multilingues.md` | Survey of legal models: Legal-BERT, JuriBERT, Legal-XLM-R. Justification for Legal-XLM-RoBERTa-base |
| 3.2 | `docs/reports/2026-01-30_investigacion_finetuning_legal_xlm_r.md` | DAPT strategies, mDAPT, span masking, hyperparameters. Original fine-tuning plan |
| 3.3 | **This document** (`2026-01-31_mejores_practicas_ml_2026.md`) | 2025-2026 Update: LoRA, RandLoRA, synthetic data, GLiNER, selective DAPT. **Updated Plan** |

### 4.5 Level 4: Designs Pending Implementation

| # | File | Key Content |
|---|------|-------------|
| 4.1 | `docs/plans/2026-02-04_uncertainty_queue_design.md` | Human-in-the-Loop design: confidence zones (HIGH/UNCERTAIN/LOW), review queue, export block. **Do not implement in ML**, transferred to main project |

### 4.6 Level 5: Current Code (pipeline state)

| # | File | Purpose |
|---|------|---------|
| 5.1 | `scripts/inference/ner_predictor.py` | **Full NER Pipeline** - Integrates 5 elements, main predictor |
| 5.2 | `scripts/inference/text_normalizer.py` | Text normalization (Elem.1) |
| 5.3 | `scripts/inference/entity_validator.py` | Checksum validation (Elem.2) |
| 5.4 | `scripts/preprocess/boundary_refinement.py` | Boundary refinement (Elem.5) |
| 5.5 | `scripts/preprocess/checksum_validators.py` | Validators: DNI, IBAN, NSS, cards |
| 5.6 | `scripts/evaluate/test_ner_predictor_adversarial_v2.py` | Adversarial test set (35 cases, SemEval evaluation) |
| 5.7 | `scripts/download_legal_xlm_roberta.py` | Base model download script |

### 4.7 Level 6: Available Models

| # | Path | Status |
|---|------|--------|
| 6.1 | `models/checkpoints/roberta-base-bne-capitel-ner/` | Current model (RoBERTa-BNE CAPITEL NER) |
| 6.2 | `models/legal_ner_v1/` | Model v1 (deprecated) |
| 6.3 | `models/legal_ner_v2/` | Current v2 model (F1 0.788 with full pipeline) |
| 6.4 | `models/pretrained/legal-xlm-roberta-base/` | **Legal-XLM-RoBERTa-base downloaded** (184M params, 128K vocab, 1.48GB) |

### 4.8 Recommended Reading Order by Task

| If the model is going to... | Read levels |
|-----------------------------|-------------|
| Continue the fine-tuning plan | 0 → 1.5 → 3.1 → 3.2 → 3.3 (this doc) |
| Modify the NER pipeline | 0 → 1.5 → 2.x (relevant element) → 5.1 |
| Evaluate baselines (GLiNER, MEL) | 0 → 1.5 → 3.3 (section 4.2 Phase 1) → 5.6 |
| Generate synthetic data | 0 → 1.5 → 3.3 (section 3.3) |
| Implement DAPT | 0 → 3.1 → 3.2 → 3.3 (sections 3.6 + 4.2 Phase 4) |
| Implement Uncertainty Queue | 0 → 4.1 (transfer to main project) |

### 4.9 Current Project State (Snapshot Feb-04 2026)

```
Current model:    legal_ner_v2 (RoBERTa-BNE + 5 pipeline elements)
F1 strict:        0.788 (SemEval entity-level, adversarial test 35 cases)
Pass rate:        60.0% (lenient 71.4%)
Downloaded model: Legal-XLM-RoBERTa-base (184M params, ready for fine-tuning)
Next step:        Establish baselines (GLiNER + MEL) → LoRA fine-tuning
```

---

## 5. Gap Analysis and Recommendations

### 5.1 What We Are Missing (Gap Analysis)

| # | Identified Gap | Priority | Recommended Technique | Source |
|---|----------------|----------|-----------------------|--------|
| **G1** | No zero-shot baseline | **Critical** | Evaluate GLiNER-PII-base on our test set | NAACL 2024 |
| **G2** | Fine-tuning planned as Full FT | **High** | Migrate to LoRA r=128, α=256, all layers | COLING 2025, ICLR 2025 |
| **G3** | Gold labels only for training | **High** | Generate synthetic data with LLM (EMNLP 2025) | EMNLP 2025 |
| **G4** | No MEL baseline | **High** | Evaluate MEL on our test set | ArXiv Jan 2025 |
| **G5** | DAPT planned without prior evaluation | **Medium** | Evaluate NER before/after DAPT, use LoRA | ICLR 2025 |
| **G6** | RandLoRA not used | **Medium** | If LoRA plateau, migrate to RandLoRA | ICLR 2025 |
| **G7** | No knowledge distillation | **Medium** | Pipeline teacher(LLM)→student(XLM-R) with CoT | IGI Global 2025 |
| **G8** | Hybrid pipeline without formal validation | **Low** | Benchmark RECAP to validate architecture | NeurIPS 2025 |

### 5.2 Ordered Recommendations

#### Phase 1: Establish Baselines (Immediate)

1. **Evaluate GLiNER-PII-base** on our adversarial test set
   - Expected F1: ~81% (published benchmark)
   - If it beats our current model (F1 0.788): prioritize integration
   - If not: confirms our pipeline is competitive

2. **Evaluate MEL** (if available) on our test set
   - Expected F1: ~82% (published benchmark with 15 labels)
   - Establishes Spanish legal benchmark

#### Phase 2: Fine-tuning with PEFT (Next Cycle)

3. **Migrate from Full FT to LoRA**
   - Config: r=128, α=256, target=all_layers, lr=2e-4, epochs=3, dropout=0.05
   - Hardware: RTX 5060 Ti 16GB VRAM is sufficient
   - Adapter size: ~50MB (vs ~700MB full model)

4. **If plateau with LoRA → RandLoRA**
   - Same trainable parameters, full rank
   - Closes >90% of LoRA→Full FT gap

#### Phase 3: Data Augmentation (Parallel to Phase 2)

5. **Generate PII synthetic data with LLM**
   - Teacher: GPT-4 or Llama-3-70B
   - Format: Consistent CoNLL/JSONL
   - Focus: categories with few examples (IBAN, NSS, MATRICULA)
   - Validate: compare F1 with gold vs gold+synthetic

6. **Knowledge distillation (optional)**
   - Only if limited data persists after augmentation
   - Pipeline: LLM generates CoT reasoning → student learns

#### Phase 4: Selective DAPT (After Phase 2-3)

7. **Evaluate NER BEFORE DAPT** (baseline)
8. **DAPT with LoRA** (not full backbone FT) on BOE corpus
9. **Evaluate NER AFTER DAPT** (compare)
10. **Evidence-based decision:** if DAPT does not improve >2% F1, discard

---

## 6. Comparison: Original Plan vs. Updated Plan

| Aspect | Original Plan (Feb 2026) | Updated Plan (Post-Review) |
|--------|--------------------------|----------------------------|
| Fine-tuning | Full FT | **LoRA r=128 / RandLoRA** |
| Data | Manual gold labels only | **Gold + synthetic LLM** |
| DAPT | Universal, 1-2 epochs | **Selective, evaluate before/after** |
| Baseline | None | **GLiNER 81% + MEL 82%** |
| Distillation | Not considered | **Optional (if limited data)** |
| Evaluation | SemEval entity-level | **+ adversarial + cross-lingual** |
| Adapter size | ~700MB (full model) | **~50MB (LoRA adapter)** |
| VRAM required | ~8GB (Full FT small batch) | **~4GB (LoRA)** |

---

## 7. Evidence Table

| Paper | Venue | Year | Technique | Key Metric | URL |
|-------|-------|------|-----------|------------|-----|
| B2NER | COLING | 2025 | LoRA NER universal | +6.8-12.0 F1 vs GPT-4 | github.com/UmeanNever/B2NER |
| RandLoRA | ICLR | 2025 | Full-rank PEFT | >90% gap LoRA→FT closed | arxiv.org/abs/2502.00987 |
| Multi-Perspective KD | IGI Global | 2025 | Distillation NER | +2.54% F1, +5.79% Recall | igi-global.com/gateway/article/372672 |
| LLM Data Gen for NER | EMNLP | 2025 | Synthetic data | 90-95% gold performance | aclanthology.org/2025.emnlp-main.418 |
| GLiNER PII | NAACL+updates | 2024-2025 | Zero-shot PII | 80.99% F1 | huggingface.co/knowledgator/gliner-pii-base-v1.0 |
| Hybrid PII Financial | Nature Sci.Rep | 2025 | Rules+ML PII | 94.7% precision | doi.org/10.1038/s41598-025-04971-9 |
| RECAP | NeurIPS | 2025 | Regex+LLM PII | +82% vs NER fine-tuned | neurips.cc/virtual/2025/122402 |
| CPT is (not) WYNG | ICLR | 2025 | Selective DAPT | Does not uniformly improve | openreview.net/pdf?id=rpi9ARgvXc |
| MEL | ArXiv | 2025 | Legal Spanish | 82% macro F1 (15 labels) | arxiv.org/html/2501.16011 |
| 3CEL | ArXiv | 2025 | Legal Spanish Corpus | Clauses benchmark | arxiv.org/html/2501.15990 |
| Financial NER LLaMA-3 | ArXiv | 2026 | LoRA Financial NER | 0.894 micro-F1 | arxiv.org/abs/2601.10043 |

---

## 8. Conclusions

### 8.1 Paradigm Shifts 2025-2026

1. **PEFT replaces Full Fine-Tuning:** LoRA/RandLoRA is now the standard for models ≤1B parameters. Full FT is only justified if LoRA does not converge (rare in base models).

2. **LLM Synthetic Data is Viable:** EMNLP 2025 demonstrates that LLM-generated data can reach 90-95% of gold data performance for multilingual NER. This solves the manual annotation bottleneck.

3. **DAPT is not Dogma:** ICLR 2025 demonstrates that DAPT may not improve and even harm if catastrophic forgetting is not mitigated. Always evaluate before and after.

4. **Hybrid > Pure ML:** Nature and NeurIPS 2025 confirm that hybrid approaches (rules + ML) outperform pure ML for PII. ContextSafe already follows this architecture.

5. **Zero-shot NER is Competitive:** GLiNER reaches 81% F1 without training. Any fine-tuned model must significantly beat this threshold to justify the effort.

### 8.2 Impact on ContextSafe

ContextSafe's current pipeline (Regex + Presidio + RoBERTa) is **architecturally aligned** with 2025-2026 evidence. The main gaps are operational:

- **Do not use Full FT** → LoRA/RandLoRA
- **Do not rely only on gold labels** → synthetic LLM data
- **Establish baselines** → GLiNER + MEL before fine-tuning
- **Selective DAPT** → evaluate, do not assume

### 8.3 Future Work

| Task | Priority | Dependency |
|------|----------|------------|
| Evaluate GLiNER-PII on ContextSafe test set | Critical | None |
| Prepare LoRA fine-tuning script (r=128, α=256) | High | Downloaded model (completed) |
| Generate synthetic PII data with LLM | High | Define target categories |
| Evaluate MEL on ContextSafe test set | High | Download MEL model |
| Selective DAPT with pre/post evaluation | Medium | BOE corpus available |
| Implement RandLoRA if plateau | Medium | LoRA results |
| Knowledge distillation pipeline | Low | Only if insufficient data |

---

## 9. References

1. UmeanNever et al. "B2NER: Beyond Boundaries: Learning Universal Entity Taxonomy across Datasets and Languages for Open Named Entity Recognition." COLING 2025. GitHub: github.com/UmeanNever/B2NER

2. Koo et al. "RandLoRA: Full-Rank Parameter-Efficient Fine-Tuning of Large Models." ICLR 2025. ArXiv: 2502.00987

3. "Multi-Perspective Knowledge Distillation of LLM for Named Entity Recognition." IGI Global Scientific Publishing, 2025. igi-global.com/gateway/article/372672

4. "A Rigorous Evaluation of LLM Data Generation Strategies for NER." EMNLP 2025 Main Conference. Paper ID: 2025.emnlp-main.418

5. Urchade Zaratiana et al. "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer." NAACL 2024. PII Models: knowledgator/gliner-pii-base-v1.0 (updated Sep 2025).

6. "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents." Nature Scientific Reports, 2025. DOI: 10.1038/s41598-025-04971-9

7. "RECAP: Deterministic Regex + Context-Aware LLMs for Multilingual PII Detection." NeurIPS 2025. neurips.cc/virtual/2025/122402

8. "Continual Pre-Training is (not) What You Need in Domain Adaptation." ICLR 2025. openreview.net/pdf?id=rpi9ARgvXc

9. "MEL: Legal Spanish language model." ArXiv, January 2025. arxiv.org/html/2501.16011

10. "3CEL: a Corpus of Legal Spanish Contract Clauses." ArXiv, January 2025. arxiv.org/html/2501.15990

11. "Instruction Finetuning LLaMA-3-8B Model Using LoRA for Financial Named Entity Recognition." ArXiv, January 2026. arxiv.org/abs/2601.10043

12. Unsloth Documentation. "LoRA Fine-tuning Hyperparameters Guide." unsloth.ai/docs (2025).

13. Gretel.ai. "GLiNER Models for PII Detection." gretel.ai/blog (2025).

14. Microsoft Presidio. "Using GLiNER with Presidio." microsoft.github.io/presidio (2025).

---

**Date:** 2026-01-31
**Revision:** 1.1 (added section 4: Mandatory Pre-readings)
**Next step:** Establish baselines (GLiNER + MEL) before starting fine-tuning
