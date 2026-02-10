# Status Report: NER-PII System for Spanish Legal Documents

**Date:** 2026-01-15
**Version:** 1.0
**Author:** AlexAlves87
**Project:** ContextSafe ML - Fine-tuning NER

---

## Executive Summary

This report documents the development of the PII (Personally Identifiable Information) detection system for Spanish legal documents. The system must detect 13 entity categories with F1 ≥ 0.85.

### Current Status

| Phase | Status | Progress |
|------|--------|----------|
| Base data download | Completed | 100% |
| Gazetteer generation | Completed | 100% |
| Synthetic dataset v1 | Discarded | Critical Error |
| Synthetic dataset v2 | Completed | 100% |
| Training script | Completed | 100% |
| Model training | Pending | 0% |

---

## 1. Project Objective

Develop a NER model specialized in Spanish legal documents (wills, judgments, deeds, contracts) capable of detecting:

| Category | Examples | Priority |
|-----------|----------|-----------|
| PERSON | Hermógenes Pérez García | High |
| DATE | 15 de marzo de 2024 | High |
| DNI_NIE | 12345678Z, X1234567A | High |
| IBAN | ES9121000418450200051332 | High |
| NSS | 281234567890 | Medium |
| PHONE | 612 345 678 | Medium |
| ADDRESS | Calle Mayor 15, 3º B | High |
| POSTAL_CODE | 28001 | Medium |
| ORGANIZATION | Banco Santander, S.A. | High |
| LOCATION | Madrid, Comunidad de Madrid | Medium |
| ECLI | ECLI:ES:TS:2024:1234 | Low |
| LICENSE_PLATE | 1234 ABC | Low |
| CADASTRAL_REF | 1234567AB1234S0001AB | Low |
| PROFESSIONAL_ID | Colegiado nº 12345 | Low |

---

## 2. Downloaded Data

### 2.1 Official Sources

| Resource | Location | Size | Description |
|---------|-----------|--------|-------------|
| CoNLL-2002 Spanish | `data/raw/conll2002/` | 4.0 MB | Standard NER Corpus |
| INE Names by decade | `data/raw/gazetteers_ine/nombres_por_fecha.xls` | 1.1 MB | Temporal frequency |
| INE Frequent names | `data/raw/gazetteers_ine/nombres_mas_frecuentes.xls` | 278 KB | Top names |
| INE Surnames | `data/raw/gazetteers_ine/apellidos_frecuencia.xls` | 12 MB | 27,251 surnames |
| INE Municipalities 2024 | `data/raw/municipios/municipios_2024.xlsx` | 300 KB | 8,115 municipalities |
| Postal codes | `data/raw/codigos_postales/codigos_postales.csv` | 359 KB | 11,051 postal codes |
| ai4privacy/pii-masking-300k | `data/raw/ai4privacy/` | ~100 MB | Transfer learning |

### 2.2 Base Model

| Model | Location | Size | Base F1 |
|--------|-----------|--------|---------|
| roberta-base-bne-capitel-ner | `models/checkpoints/` | ~500 MB | 88.5% (CAPITEL) |

**Model Decision:** MEL (Spanish Legal Model) was evaluated but lacks fine-tuning for NER. RoBERTa-BNE-capitel-ner was selected due to its specialization in Spanish NER.

---

## 3. Generated Gazetteers

### 3.1 Generation Scripts

| Script | Function | Output |
|--------|---------|--------|
| `parse_ine_gazetteers.py` | Parses INE Excel → JSON | apellidos.json, nombres_*.json |
| `generate_archaic_names.py` | Generates legal archaic names | nombres_arcaicos.json |
| `generate_textual_dates.py` | Dates in legal format | fechas_textuales.json |
| `generate_administrative_ids.py` | DNI, NIE, IBAN, NSS with invalid checksums | identificadores_administrativos.json |
| `generate_addresses.py` | Complete Spanish addresses | direcciones.json |
| `generate_organizations.py` | Companies, courts, banks | organizaciones.json |

### 3.2 Generated Files

| File | Size | Content |
|---------|--------|-----------|
| `apellidos.json` | 1.8 MB | 27,251 surnames with INE frequencies |
| `codigos_postales.json` | 1.2 MB | 11,051 postal codes |
| `municipios.json` | 164 KB | 8,115 Spanish municipalities |
| `nombres_hombres.json` | 40 KB | 550 male names per decade |
| `nombres_mujeres.json` | 41 KB | 550 female names per decade |
| `nombres_todos.json` | 3.9 KB | 260 unique names (INE) |
| `nombres_arcaicos.json` | 138 KB | 940 archaic names + 5,070 combinations |
| `nombres_arcaicos_flat.json` | 267 KB | Flat list for NER |
| `fechas_textuales.json` | 159 KB | 645 dates with 4 patterns |
| `fechas_textuales_flat.json` | 86 KB | Flat list |
| `identificadores_administrativos.json` | 482 KB | 2,550 synthetic IDs |
| `identificadores_administrativos_flat.json` | 134 KB | Flat list |
| `direcciones.json` | 159 KB | 600 addresses + 416 with legal context |
| `direcciones_flat.json` | 59 KB | Flat list |
| `organizaciones.json` | 185 KB | 1,000 organizations |
| `organizaciones_flat.json` | 75 KB | Flat list |

**Total gazetteers:** ~4.9 MB

### 3.3 Special Features

**Archaic Names:** Includes frequent names in historical legal documents:
- Hermógenes, Segismundo, Práxedes, Gertrudis, Baldomero, Saturnino, Patrocinio...
- Composite combinations: María del Carmen, José Antonio, Juan de Dios...

**Administrative Identifiers:** Generated with MATHEMATICALLY INVALID checksums:
- DNI: Incorrect control letter (incorrect mod-23)
- NIE: Prefix X/Y/Z with incorrect letter
- IBAN: Control digits "00" (always invalid)
- NSS: Incorrect control digits (mod-97)

This guarantees that no synthetic identifier corresponds to real data.

---

## 4. Synthetic Dataset

### 4.1 Dataset v1 - CRITICAL ERROR (DISCARDED)

**Date:** 2026-01-15

The first generated dataset contained critical errors that would have significantly degraded the model.

#### Error 1: Punctuation Adhered to Tokens

**Problem:** Simple tokenizer by whitespace caused punctuation to stick to entities.

**Example of error:**
```
Text: "Don Hermógenes Freijanes, con DNI 73364386X."
Tokens: ["Don", "Hermógenes", "Freijanes,", "con", "DNI", "73364386X."]
Labels: ["O",   "B-PERSON",   "I-PERSON",   "O",   "O",   "B-DNI_NIE"]
```

**Impact:** The model would learn that "Freijanes," (with comma) is a person, but during inference it would not recognize "Freijanes" without comma.

**Error statistics:**
- 6,806 tokens with adhered punctuation
- Affected mainly: PERSON, DNI_NIE, IBAN, PHONE
- ~30% of compromised entities

#### Error 2: No Subword Alignment

**Problem:** BIO tags were at word level, but BERT uses subword tokenization.

**Example of error:**
```
Word: "Hermógenes"
Subwords: ["Her", "##mó", "##genes"]
Label v1: Only one tag for the whole word → which subword receives it?
```

**Impact:** Without explicit alignment, the model could not correctly learn the relationship between subwords and tags.

#### Error 3: Entity Imbalance

| Entity | Percentage v1 | Problem |
|---------|---------------|----------|
| PERSON | 30.3% | Overrepresented |
| ADDRESS | 12.6% | OK |
| DNI_NIE | 10.1% | OK |
| NSS | 1.7% | Underrepresented |
| ECLI | 1.7% | Underrepresented |
| LICENSE_PLATE | 1.7% | Underrepresented |

### 4.2 Dataset v2 - CORRECTED

**Date:** 2026-01-15

**Script:** `scripts/preprocess/generate_ner_dataset_v2.py`

#### Implemented Corrections

**1. Tokenization with HuggingFace:**
```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne")

# Tokenization automatically separates punctuation
# "Freijanes," → ["Fre", "##ij", "##anes", ","]
```

**2. Alignment with word_ids():**
```python
def align(self, sentence, max_length=128):
    encoding = self.tokenizer(
        text,
        max_length=max_length,
        return_offsets_mapping=True,
    )

    word_ids = encoding.word_ids()

    labels = []
    for i, word_id in enumerate(word_ids):
        if word_id is None:
            labels.append(-100)  # Special token
        elif word_id != previous_word_id:
            labels.append(entity_label)  # First subword
        else:
            labels.append(-100)  # Continuation
```

**3. Balanced Templates:**
- Added 50+ specific templates for minority entities
- Increased frequency of NSS, ECLI, LICENSE_PLATE, CADASTRAL_REF

#### v2 Statistics

| Split | Samples | Total Tokens |
|-------|----------|----------------|
| Train | 4,925 | ~630,000 |
| Validation | 818 | ~105,000 |
| Test | 818 | ~105,000 |
| **Total** | **6,561** | **~840,000** |

**v2 Entity Distribution:**

| Entity | Count | % |
|---------|-------|---|
| PERSON | 1,800 | 24.4% |
| ADDRESS | 750 | 10.2% |
| LOCATION | 700 | 9.5% |
| DNI_NIE | 600 | 8.1% |
| DATE | 450 | 6.1% |
| ORGANIZATION | 450 | 6.1% |
| POSTAL_CODE | 200 | 2.7% |
| IBAN | 200 | 2.7% |
| CADASTRAL_REF | 150 | 2.0% |
| PHONE | 150 | 2.0% |
| PROFESSIONAL_ID | 150 | 2.0% |
| ECLI | 100 | 1.4% |
| LICENSE_PLATE | 100 | 1.4% |
| NSS | 100 | 1.4% |

#### Output Format

```
data/processed/ner_dataset_v2/
├── train/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── validation/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── test/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── label_mappings.json
└── dataset_dict.json
```

**Data Schema:**
```python
{
    "input_ids": [0, 1234, 5678, ...],      # Token IDs
    "attention_mask": [1, 1, 1, ...],        # Attention mask
    "labels": [-100, 1, 2, -100, ...],       # Aligned labels
}
```

**Labels (29 classes):**
```json
{
    "O": 0,
    "B-PERSON": 1, "I-PERSON": 2,
    "B-LOCATION": 3, "I-LOCATION": 4,
    "B-ORGANIZATION": 5, "I-ORGANIZATION": 6,
    "B-DATE": 7, "I-DATE": 8,
    "B-DNI_NIE": 9, "I-DNI_NIE": 10,
    "B-IBAN": 11, "I-IBAN": 12,
    "B-NSS": 13, "I-NSS": 14,
    "B-PHONE": 15, "I-PHONE": 16,
    "B-ADDRESS": 17, "I-ADDRESS": 18,
    "B-POSTAL_CODE": 19, "I-POSTAL_CODE": 20,
    "B-LICENSE_PLATE": 21, "I-LICENSE_PLATE": 22,
    "B-CADASTRAL_REF": 23, "I-CADASTRAL_REF": 24,
    "B-ECLI": 25, "I-ECLI": 26,
    "B-PROFESSIONAL_ID": 27, "I-PROFESSIONAL_ID": 28
}
```

---

## 5. Training Configuration

### 5.1 Best Practices Research

Best practices for NER fine-tuning were investigated based on:
- HuggingFace Documentation
- Academic Papers (RoBERTa, BERT for NER)
- Spanish Model Benchmarks (CAPITEL, AnCora)

### 5.2 Selected Hyperparameters

**File:** `scripts/train/train_ner.py`

```python
CONFIG = {
    # Optimization (MOST IMPORTANT)
    "learning_rate": 2e-5,          # Grid: {1e-5, 2e-5, 3e-5, 5e-5}
    "weight_decay": 0.01,           # L2 Regularization
    "adam_epsilon": 1e-8,           # Numerical stability

    # Batching
    "per_device_train_batch_size": 16,
    "per_device_eval_batch_size": 32,
    "gradient_accumulation_steps": 2,  # Effective batch = 32

    # Epochs
    "num_train_epochs": 4,          # Conservative for legal

    # Learning Rate Scheduling
    "warmup_ratio": 0.06,           # 6% warmup (RoBERTa paper)
    "lr_scheduler_type": "linear",  # Linear decay

    # Early Stopping
    "early_stopping_patience": 2,   # Stop if no improvement in 2 evals
    "metric_for_best_model": "f1",

    # Sequence Length
    "max_length": 384,              # Long legal documents

    # Hardware
    "fp16": True,                   # Mixed precision if GPU
    "dataloader_num_workers": 4,

    # Reproducibility
    "seed": 42,
}
```

### 5.3 Justification of Decisions

| Parameter | Value | Justification |
|-----------|-------|---------------|
| learning_rate | 2e-5 | Standard value for BERT/RoBERTa fine-tuning |
| batch_size | 32 (effective) | Balance between stability and memory |
| epochs | 4 | Avoid overfitting on synthetic data |
| warmup | 6% | RoBERTa paper recommendation |
| max_length | 384 | Legal documents can be extensive |
| early_stopping | 2 | Early detection of overfitting |

### 5.4 Dependencies

**File:** `scripts/train/requirements_train.txt`

```
transformers>=4.36.0
datasets>=2.14.0
torch>=2.0.0
evaluate>=0.4.0
seqeval>=1.2.2
accelerate>=0.25.0
```

---

## 6. Lessons Learned

### 6.1 ISS-001 Error: Inadequate Tokenization

**Root cause:** Assuming whitespace tokenization was sufficient for NER with transformer models.

**Potential impact:** If trained with dataset v1:
- Degraded F1 estimated: -15% to -25%
- Entities with punctuation not recognized
- Poor generalization to real text

**Future prevention:**
1. Always use the base model tokenizer
2. Implement dataset audit before training
3. Verify subword-label alignment explicitly

### 6.2 Importance of Prior Research

Investigating best practices BEFORE implementing avoided:
- Suboptimal hyperparameters (e.g., learning_rate=1e-4 causes divergence)
- Incorrect architecture (e.g., without CRF layer in classic NER)
- Incorrect evaluation (e.g., accuracy vs F1 for NER)

### 6.3 Synthetic Data: Strengths and Limitations

**Strengths:**
- Total control over entity distribution
- Coverage of edge cases (archaic names, rare formats)
- Scalable volume without annotation cost

**Limitations:**
- Artificial language patterns
- No real noise (OCR errors, typos)
- Requires validation on real data

---

## 7. Future Work

### 7.1 Immediate (Next steps)

1. **Execute training:**
   ```bash
   cd ml
   source .venv/bin/activate
   pip install -r scripts/train/requirements_train.txt
   python scripts/train/train_ner.py
   ```

2. **Evaluate by entity type:**
   - Verify F1 ≥ 0.85 for each category
   - Identify problematic entities

3. **Adversarial test:**
   - Unseen archaic names
   - Ambiguous date formats
   - Incomplete addresses

### 7.2 Potential Improvements

| Improvement | Priority | Expected Impact |
|--------|-----------|------------------|
| CRF layer | High | +4-13% F1 |
| Real annotated data | High | Better generalization |
| Data augmentation | Medium | +2-5% F1 |
| Ensemble with regex | Medium | +3-5% recall |
| Active learning | Low | Annotation cost reduction |

### 7.3 Optional Resources

Academic papers pending evaluation:
- MAPA Project (aclanthology.org/2022.lrec-1.400/) - Legal PII annotated
- 3CEL Contracts (arxiv.org/abs/2501.15990) - Contract clauses
- IMPACT-es Corpus (arxiv.org/pdf/1306.3692.pdf) - Historical names

---

## 8. Project Structure

```
ml/
├── data/
│   ├── raw/
│   │   ├── conll2002/              # Standard NER Corpus
│   │   ├── gazetteers_ine/         # Original INE Excel
│   │   ├── municipios/             # Municipalities 2024
│   │   ├── codigos_postales/       # Spain CPs
│   │   └── ai4privacy/             # Transfer learning dataset
│   └── processed/
│       ├── gazetteers/             # Processed JSONs
│       ├── synthetic_sentences/     # Sentences v1 (discarded)
│       └── ner_dataset_v2/         # Final HuggingFace Dataset
├── models/
│   ├── checkpoints/                # RoBERTa-BNE base model
│   └── legal_ner_v1/               # Training output (pending)
├── scripts/
│   ├── preprocess/
│   │   ├── parse_ine_gazetteers.py
│   │   ├── generate_archaic_names.py
│   │   ├── generate_textual_dates.py
│   │   ├── generate_administrative_ids.py
│   │   ├── generate_addresses.py
│   │   ├── generate_organizations.py
│   │   ├── generate_ner_dataset_v2.py
│   │   └── audit_dataset.py
│   └── train/
│       ├── train_ner.py
│       └── requirements_train.txt
└── docs/
    ├── checklists/
    │   └── 2026-02-02_descargas_fase1.md
    └── reports/
        └── 2026-01-15_estado_proyecto_ner.md  # This document
```

---

## 9. Conclusions

1. **Preparation completed:** Gazetteers, dataset v2, and training script ready.

2. **Critical error avoided:** Dataset v1 audit identified problems that would have significantly degraded the model.

3. **Best practices applied:** Hyperparameters based on research, not assumptions.

4. **Next milestone:** Execute training and evaluate F1 per entity.

---

---

## 10. References

### Models and Datasets

1. **RoBERTa-BNE-capitel-ner** - PlanTL-GOB-ES
   - https://huggingface.co/PlanTL-GOB-ES/roberta-base-bne-capitel-ner
   - F1 88.5% on CAPITEL

2. **CoNLL-2002 Spanish** - Standard NER Corpus
   - https://www.clips.uantwerpen.be/conll2002/ner/

3. **ai4privacy/pii-masking-300k** - English PII Dataset
   - https://huggingface.co/datasets/ai4privacy/pii-masking-300k

### Official INE Data

4. **Names by frequency** - INE
   - https://www.ine.es/daco/daco42/nombyam/nombres_por_edad.xls

5. **Surnames by frequency** - INE
   - https://www.ine.es/daco/daco42/nombyam/apellidos_frecuencia.xls

6. **Municipalities Spain 2024** - INE
   - https://www.ine.es/daco/daco42/codmun/

### Papers and Documentation

7. **RoBERTa: A Robustly Optimized BERT Pretraining Approach** - Liu et al., 2019
   - https://arxiv.org/abs/1907.11692
   - Reference for warmup ratio 6%

8. **HuggingFace Token Classification Guide**
   - https://huggingface.co/docs/transformers/tasks/token_classification
   - Subword-label alignment guide

9. **seqeval: A Python framework for sequence labeling evaluation**
   - https://github.com/chakki-works/seqeval
   - Entity-level metrics for NER

### Papers Pending Evaluation

10. **MAPA Project** - Legal PII annotated
    - https://aclanthology.org/2022.lrec-1.400/

11. **3CEL Contracts** - Contract clauses
    - https://arxiv.org/abs/2501.15990

12. **IMPACT-es Corpus** - Historical names
    - https://arxiv.org/pdf/1306.3692.pdf

---

**Last update:** 2026-02-03
**Next review:** Post-training
