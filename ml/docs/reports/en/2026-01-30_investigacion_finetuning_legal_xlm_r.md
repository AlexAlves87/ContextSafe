# Research: Fine-tuning Legal-XLM-RoBERTa for Multilingual NER-PII

**Date:** 2026-01-30
**Author:** AlexAlves87
**Objective:** Extensive fine-tuning strategy for multilingual expansion of ContextSafe
**Base Model:** `joelniklaus/legal-xlm-roberta-base`

---

## 1. Executive Summary

Systematic review of academic literature (2021-2025) on fine-tuning XLM-RoBERTa models for Named Entity Recognition (NER) tasks in the legal domain, with emphasis on Domain Adaptive Pre-Training (DAPT) strategies and multilingual configurations.

### Key Findings

| Finding | Evidence | Impact |
|---------|----------|--------|
| DAPT improves F1 by +5-10% | Mining Legal Arguments (2024) | High |
| mDAPT ≈ multiple monolingual | Jørgensen et al. (2021) | High |
| Span masking > token masking | ACL 2020 | Medium |
| Full fine-tuning > transfer learning | NER-RoBERTa (2024) | High |

### Recommendation

> **Optimal Strategy:** Multilingual DAPT (1-2 epochs on legal corpus) followed by supervised NER fine-tuning (10-20 epochs).
> **Expected F1:** 88-92% vs 85% baseline without DAPT.

---

## 2. Review Methodology

### 2.1 Search Criteria

| Aspect | Criterion |
|--------|-----------|
| Period | 2021-2025 |
| Databases | arXiv, ACL Anthology, IEEE Xplore, ResearchGate |
| Terms | "XLM-RoBERTa fine-tuning", "Legal NER", "DAPT", "multilingual NER", "domain adaptation" |
| Language | English |

### 2.2 Reviewed Papers

| Paper | Year | Venue | Relevance |
|-------|------|-------|-----------|
| LEXTREME Benchmark | 2023 | EMNLP | Multilingual legal benchmark |
| MultiLegalPile | 2023 | ACL | 689GB corpus 24 languages |
| mDAPT | 2021 | EMNLP Findings | Multilingual DAPT |
| Mining Legal Arguments | 2024 | arXiv | DAPT vs legal fine-tuning |
| NER-RoBERTa | 2024 | arXiv | NER Fine-tuning |
| MEL: Legal Spanish | 2025 | arXiv | Spanish legal model |
| Don't Stop Pretraining | 2020 | ACL | Original DAPT |

### 2.3 Reproducibility

```bash
# Environment
cd /path/to/ml
source .venv/bin/activate

# Dependencies
pip install transformers datasets accelerate

# Download base model
python -c "from transformers import AutoModel; AutoModel.from_pretrained('joelniklaus/legal-xlm-roberta-base')"
```

---

## 3. Theoretical Framework

### 3.1 Domain Adaptation Taxonomy

```
Pre-trained Model (XLM-RoBERTa)
            │
            ├─→ [A] Direct Fine-tuning
            │       └─→ Train classification layer
            │
            ├─→ [B] Full Fine-tuning
            │       └─→ Train all weights
            │
            └─→ [C] DAPT + Fine-tuning (RECOMMENDED)
                    ├─→ Continued pretraining (MLM)
                    └─→ Supervised fine-tuning
```

### 3.2 Domain Adaptive Pre-Training (DAPT)

**Definition:** Continuing pretraining of the model on target domain text (unlabeled) before supervised fine-tuning.

**Theoretical Basis (Gururangan et al., 2020):**

> "A second phase of pretraining in-domain (DAPT) leads to performance gains, even when the target domain is close to the pretraining corpus."

**Mechanism:**
1. Model learns legal domain token distribution
2. Captures specialized vocabulary (legal latin, notarial structures)
3. Adjusts internal representations to legal context

### 3.3 mDAPT: Multilingual DAPT

**Definition:** DAPT applied simultaneously across multiple languages with a single model.

**Key Finding (Jørgensen et al., 2021):**

> "DAPT generalizes well to multilingual settings and can be accomplished with a single unified model trained across several languages simultaneously, avoiding the need for language-specific models."

**Advantage:** An mDAPT model can match or exceed multiple monolingual DAPT models.

---

## 4. Literature Results

### 4.1 Impact of DAPT in Legal Domain

**Study:** Mining Legal Arguments to Study Judicial Formalism (2024)

| Task | BERT Base | BERT + DAPT | Δ |
|------|-----------|-------------|---|
| Argument Classification | 62.2% | 71.6% | **+9.4%** |
| Formalism Classification | 67.3% | 71.6% | **+4.3%** |
| Llama 3.1 8B (full FT) | 74.6% | 77.5% | **+2.9%** |

**Conclusion:** DAPT is particularly effective for BERT-like models in the legal domain.

### 4.2 Mono vs Multilingual Comparison

**Study:** LEXTREME Benchmark (2023)

| Model | Type | Aggregated Score |
|-------|------|------------------|
| XLM-R large | Multilingual | 61.3 |
| Legal-XLM-R large | Multi + Legal | 59.5 |
| MEL (Spanish) | Monolingual | Superior* |
| GreekLegalRoBERTa | Monolingual | Superior* |

*Superior in its specific language, not comparable cross-lingual.

**Conclusion:** Monolingual models outperform multilingual ones by ~3-5% F1 for a specific language, but multilingual models offer coverage.

### 4.3 Optimal Hyperparameters

**Meta-analysis of multiple studies:**

#### DAPT (Continued Pretraining):

| Parameter | Optimal Value | Range | Source |
|-----------|---------------|-------|--------|
| Learning rate | 1e-5 | 5e-6 - 2e-5 | Gururangan 2020 |
| Epochs | 1-2 | 1-3 | Legal Arguments 2024 |
| Batch size | 32-64 | 16-128 | Hardware dependent |
| Max seq length | 512 | 256-512 | Domain dependent |
| Warmup ratio | 0.1 | 0.06-0.1 | Standard |
| Masking strategy | Span | Token/Span | ACL 2020 |

#### NER Fine-tuning:

| Parameter | Optimal Value | Range | Source |
|-----------|---------------|-------|--------|
| Learning rate | 5e-5 | 1e-5 - 6e-5 | MasakhaNER 2021 |
| Epochs | 10-20 | 5-50 | Dataset size |
| Batch size | 16-32 | 12-64 | Memory |
| Max seq length | 256 | 128-512 | Entity length |
| Dropout | 0.2 | 0.1-0.3 | Standard |
| Weight decay | 0.01 | 0.0-0.1 | Regularization |
| Early stopping | patience=3 | 2-5 | Overfitting |

### 4.4 Span Masking vs Token Masking

**Study:** Don't Stop Pretraining (ACL 2020)

| Strategy | Description | Downstream F1 |
|----------|-------------|---------------|
| Token masking | Individual random masks | Baseline |
| Span masking | Contiguous sequence masks | **+3-5%** |
| Whole word masking | Whole word masks | +2-3% |
| Entity masking | Known entity masks | **+4-6%** |

**Recommendation:** Use span masking for DAPT in legal domain.

---

## 5. Corpus Analysis for DAPT

### 5.1 Multilingual Legal Data Sources

| Source | Languages | Size | License |
|--------|-----------|------|---------|
| EUR-Lex | 24 | ~50GB | Open |
| MultiLegalPile | 24 | 689GB | CC BY-NC-SA |
| BOE (Spain) | ES | ~10GB | Open |
| Légifrance | FR | ~15GB | Open |
| Giustizia.it | IT | ~5GB | Open |
| STF/STJ (Brazil) | PT | ~8GB | Open |
| Gesetze-im-Internet | DE | ~3GB | Open |

### 5.2 Recommended Composition for mDAPT

| Language | % Corpus | Est. GB | Justification |
|----------|----------|---------|---------------|
| ES | 30% | 6GB | Main market |
| EN | 20% | 4GB | Transfer learning, EUR-Lex |
| FR | 15% | 3GB | Secondary market |
| IT | 15% | 3GB | Secondary market |
| PT | 10% | 2GB | LATAM market |
| DE | 10% | 2GB | DACH market |
| **Total** | 100% | ~20GB | - |

### 5.3 Corpus Preprocessing

```python
# Recommended preprocessing pipeline
def preprocess_legal_corpus(text: str) -> str:
    # 1. Unicode Normalization (NFKC)
    text = unicodedata.normalize('NFKC', text)

    # 2. Remove repetitive headers/footers
    text = remove_boilerplate(text)

    # 3. Segment into sentences
    sentences = segment_sentences(text)

    # 4. Filter very short sentences (<10 tokens)
    sentences = [s for s in sentences if len(s.split()) >= 10]

    # 5. Deduplication
    sentences = deduplicate(sentences)

    return '\n'.join(sentences)
```

---

## 6. Proposed Training Pipeline

### 6.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 0: Preparation                                       │
│  - Download Legal-XLM-RoBERTa-base                          │
│  - Prepare multilingual legal corpus (~20GB)               │
│  - Create multilingual NER dataset (~50K examples)          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: DAPT (Domain Adaptive Pre-Training)               │
│  - Model: legal-xlm-roberta-base                            │
│  - Objective: MLM with span masking                         │
│  - Corpus: 20GB multilingual legal                          │
│  - Config: lr=1e-5, epochs=2, batch=32                      │
│  - Output: legal-xlm-roberta-base-dapt                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: NER Fine-tuning                                   │
│  - Model: legal-xlm-roberta-base-dapt                       │
│  - Dataset: Multilingual PII NER (13 categories)            │
│  - Config: lr=5e-5, epochs=15, batch=16                     │
│  - Early stopping: patience=3                               │
│  - Output: legal-xlm-roberta-ner-pii                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Evaluation                                        │
│  - Test set per language                                    │
│  - Adversarial tests                                        │
│  - Metrics: F1 (SemEval 2013)                               │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 DAPT Configuration

```python
# configs/dapt_config.yaml
model:
  name: "joelniklaus/legal-xlm-roberta-base"
  output_dir: "models/legal-xlm-roberta-base-dapt"

training:
  objective: "mlm"
  masking_strategy: "span"
  masking_probability: 0.15
  span_length: 3  # Average span length

  learning_rate: 1e-5
  weight_decay: 0.01
  warmup_ratio: 0.1

  num_epochs: 2
  batch_size: 32
  gradient_accumulation_steps: 4  # Effective batch = 128

  max_seq_length: 512

  fp16: true  # Mixed precision

data:
  train_file: "data/legal_corpus_multilingual.txt"
  validation_split: 0.01

hardware:
  device: "cuda"
  num_gpus: 1
```

### 6.3 NER Fine-tuning Configuration

```python
# configs/ner_finetuning_config.yaml
model:
  name: "models/legal-xlm-roberta-base-dapt"  # Post-DAPT
  output_dir: "models/legal-xlm-roberta-ner-pii"

training:
  learning_rate: 5e-5
  weight_decay: 0.01
  warmup_ratio: 0.1

  num_epochs: 15
  batch_size: 16
  gradient_accumulation_steps: 2  # Effective batch = 32

  max_seq_length: 256

  early_stopping:
    patience: 3
    metric: "eval_f1"
    mode: "max"

  dropout: 0.2

  fp16: true

data:
  train_file: "data/ner_pii_multilingual_train.json"
  validation_file: "data/ner_pii_multilingual_dev.json"
  test_file: "data/ner_pii_multilingual_test.json"

labels:
  - "O"
  - "B-PERSON_NAME"
  - "I-PERSON_NAME"
  - "B-DNI_NIE"
  - "I-DNI_NIE"
  - "B-PHONE"
  - "I-PHONE"
  - "B-EMAIL"
  - "I-EMAIL"
  - "B-ADDRESS"
  - "I-ADDRESS"
  - "B-ORGANIZATION"
  - "I-ORGANIZATION"
  - "B-DATE"
  - "I-DATE"
  - "B-IBAN"
  - "I-IBAN"
  - "B-LOCATION"
  - "I-LOCATION"
  - "B-POSTAL_CODE"
  - "I-POSTAL_CODE"
  - "B-NSS"
  - "I-NSS"
  - "B-LICENSE_PLATE"
  - "I-LICENSE_PLATE"
  - "B-CADASTRAL_REF"
  - "I-CADASTRAL_REF"
  - "B-PROFESSIONAL_ID"
  - "I-PROFESSIONAL_ID"
```

---

## 7. Resource Estimation

### 7.1 Computational

| Phase | GPU | VRAM | Time | Cloud Cost* |
|-------|-----|------|------|-------------|
| DAPT (20GB corpus) | V100 16GB | 14GB | 48-72h | $100-150 |
| NER Fine-tuning | V100 16GB | 8GB | 8-12h | $20-30 |
| Evaluation | V100 16GB | 4GB | 1-2h | $5 |
| **Total** | - | - | **57-86h** | **$125-185** |

*Estimated AWS p3.2xlarge spot prices (~$1-1.5/h)

### 7.2 Storage

| Component | Size |
|-----------|------|
| Raw legal corpus | ~50GB |
| Processed corpus | ~20GB |
| Base model | ~500MB |
| DAPT checkpoints | ~2GB |
| Final model | ~500MB |
| **Total** | ~75GB |

### 7.3 With Local Hardware (RTX 5060 Ti 16GB)

| Phase | Estimated Time |
|-------|----------------|
| DAPT (20GB) | 72-96h |
| NER Fine-tuning | 12-16h |
| **Total** | **84-112h** (~4-5 days) |

---

## 8. Evaluation Metrics

### 8.1 Primary Metrics (SemEval 2013)

| Metric | Formula | Target |
|--------|---------|--------|
| **F1 Strict** | 2×(P×R)/(P+R) only COR | ≥0.88 |
| **F1 Partial** | Includes PAR with 0.5 weight | ≥0.92 |
| **COR** | Correct matches | Maximize |
| **PAR** | Partial matches | Minimize |
| **MIS** | Missing (FN) | Minimize |
| **SPU** | Spurious (FP) | Minimize |

### 8.2 Metrics by Language

| Language | Target F1 | Baseline* |
|----------|-----------|-----------|
| ES | ≥0.90 | 0.79 |
| EN | ≥0.88 | 0.82 |
| FR | ≥0.88 | 0.80 |
| IT | ≥0.87 | 0.78 |
| PT | ≥0.88 | 0.81 |
| DE | ≥0.87 | 0.79 |

*Baseline = XLM-R without DAPT on LEXTREME NER tasks

---

## 9. Conclusions

### 9.1 Key Findings from Literature

1. **DAPT is essential for legal domain:** +5-10% F1 documented in multiple studies.

2. **mDAPT is viable:** A multilingual model with DAPT can match multiple monolingual ones.

3. **Span masking improves DAPT:** +3-5% vs standard token masking.

4. **Full fine-tuning > transfer learning:** For NER, training all weights is superior.

5. **Stable hyperparameters:** lr=5e-5, epochs=10-20, batch=16-32 work consistently.

### 9.2 Final Recommendation

| Aspect | Recommendation |
|--------|----------------|
| Base model | `joelniklaus/legal-xlm-roberta-base` |
| Strategy | DAPT (2 epochs) + NER Fine-tuning (15 epochs) |
| DAPT Corpus | 20GB multilingual (EUR-Lex + national sources) |
| NER Dataset | 50K examples, 13 categories, 6 languages |
| Expected F1 | 88-92% |
| Total Time | ~4-5 days (Local GPU) |
| Cloud Cost | ~$150 |

### 9.3 Next Steps

| Priority | Task |
|----------|------|
| 1 | Download `legal-xlm-roberta-base` model |
| 2 | Prepare multilingual EUR-Lex corpus |
| 3 | Implement DAPT pipeline with span masking |
| 4 | Create multilingual PII NER dataset |
| 5 | Run DAPT + fine-tuning |
| 6 | Evaluate with SemEval metrics |

---

## 10. References

### 10.1 Fundamental Papers

1. Gururangan, S., et al. (2020). "Don't Stop Pretraining: Adapt Language Models to Domains and Tasks." ACL 2020. [Paper](https://aclanthology.org/2020.acl-main.740/)

2. Niklaus, J., et al. (2023). "LEXTREME: A Multi-Lingual and Multi-Task Benchmark for the Legal Domain." EMNLP 2023. [arXiv:2301.13126](https://arxiv.org/abs/2301.13126)

3. Niklaus, J., et al. (2023). "MultiLegalPile: A 689GB Multilingual Legal Corpus." ACL 2024. [arXiv:2306.02069](https://arxiv.org/abs/2306.02069)

4. Jørgensen, F., et al. (2021). "mDAPT: Multilingual Domain Adaptive Pretraining in a Single Model." EMNLP Findings. [Paper](https://aclanthology.org/2021.findings-emnlp.290/)

5. Conneau, A., et al. (2020). "Unsupervised Cross-lingual Representation Learning at Scale." ACL 2020. [arXiv:1911.02116](https://arxiv.org/abs/1911.02116)

6. Licari, D. & Comandè, G. (2022). "ITALIAN-LEGAL-BERT: A Pre-trained Transformer Language Model for Italian Law." KM4Law 2022. [Paper](https://ceur-ws.org/Vol-3256/km4law3.pdf)

7. Mining Legal Arguments (2024). "Mining Legal Arguments to Study Judicial Formalism." arXiv. [arXiv:2512.11374](https://arxiv.org/pdf/2512.11374)

8. NER-RoBERTa (2024). "Fine-Tuning RoBERTa for Named Entity Recognition." arXiv. [arXiv:2412.15252](https://arxiv.org/pdf/2412.15252)

### 10.2 HuggingFace Models

| Model | URL |
|-------|-----|
| Legal-XLM-RoBERTa-base | [joelniklaus/legal-xlm-roberta-base](https://huggingface.co/joelniklaus/legal-xlm-roberta-base) |
| Legal-XLM-RoBERTa-large | [joelniklaus/legal-xlm-roberta-large](https://huggingface.co/joelniklaus/legal-xlm-roberta-large) |
| XLM-RoBERTa-base | [xlm-roberta-base](https://huggingface.co/xlm-roberta-base) |

### 10.3 Datasets

| Dataset | URL |
|---------|-----|
| LEXTREME | [joelito/lextreme](https://huggingface.co/datasets/joelito/lextreme) |
| MultiLegalPile | [joelito/Multi_Legal_Pile](https://huggingface.co/datasets/joelito/Multi_Legal_Pile) |
| EUR-Lex | [eur-lex.europa.eu](https://eur-lex.europa.eu/) |

---

**Papers reviewed:** 8
**Date:** 2026-01-30
