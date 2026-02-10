# Fix: Tokenizer Dataset v3 - Empty Labels

**Date:** 2026-01-22
**Author:** AlexAlves87
**Type:** Debugging / Post-mortem
**Status:** Resolved

---

## Issue Summary

The dataset v3 generated with `inject_ocr_noise.py` produced all labels as `-100`, causing `ZeroDivisionError` during training.

**Symptoms:**
```
ZeroDivisionError: division by zero
# In seqeval accuracy_score
# Because there were no valid labels to evaluate
```

**Diagnosis:**
```python
ds = load_from_disk('data/processed/ner_dataset_v3')
sample = ds['validation'][0]
labels = sample['labels']
non_special = [l for l in labels if l != -100]
print(f'Non-special labels: {len(non_special)}')  # Output: 0  <- ERROR
```

---

## Root Cause

### Problem 1: Missing Dependency

The tokenizer requires `sentencepiece` to correctly load vocabulary files. Without this dependency:

```python
tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne", use_fast=True)
print(tokenizer.vocab_size)  # Output: 5 (only special tokens!)
print(tokenizer.word_ids())  # Output: [None, None, ...] (all None)
```

**Underlying error:**
```
ValueError: Couldn't instantiate the backend tokenizer from one of:
(1) a `tokenizers` library serialization file,
(2) a slow tokenizer instance to convert or
(3) an equivalent slow tokenizer class to instantiate and convert.
You need to have sentencepiece or tiktoken installed to convert a slow tokenizer to a fast one.
```

### Problem 2: Incomplete HuggingFace Model

The model `PlanTL-GOB-ES/roberta-base-bne` on HuggingFace Hub does not have the model/tokenizer files uploaded (only `.gitattributes` and `README.md`).

---

## Applied Solution

### 1. Install missing dependencies

```bash
pip install sentencepiece protobuf
```

### 2. Use local checkpoint instead of HuggingFace Hub

**Before (broken):**
```python
MODEL_NAME = "PlanTL-GOB-ES/roberta-base-bne"
```

**After (fixed):**
```python
MODEL_NAME = str(BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner")
```

The local checkpoint has all necessary files:
- `config.json`
- `model.safetensors`
- `tokenizer.json` (3.6 MB with complete vocabulary)
- `tokenizer_config.json`

### 3. Regenerate dataset

```bash
python scripts/preprocess/inject_ocr_noise.py
```

---

## Verification

**After the fix:**
```python
tokenizer = AutoTokenizer.from_pretrained(local_path, use_fast=True)
print(tokenizer.vocab_size)  # Output: 50262 (correct!)

encoding = tokenizer("Don José García López con DNI 12345678Z", return_offsets_mapping=True)
print(encoding.word_ids())  # Output: [None, 0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 7, None] (correct!)
```

**Regenerated Dataset v3:**
```
train:
  Non-special labels: 48
  Entity labels (>0): 30

validation:
  Non-special labels: 18
  Entity labels (>0): 7

test:
  Non-special labels: 45
  Entity labels (>0): 33
```

---

## Modified Files

| File | Change |
|---------|--------|
| `scripts/preprocess/inject_ocr_noise.py` | `MODEL_NAME` → local checkpoint |
| `requirements.txt` (pending) | Add `sentencepiece`, `protobuf` |

---

## Lessons Learned

1. **Check vocab_size** after loading tokenizer - if < 100, something is wrong
2. **Use local checkpoints** when HuggingFace Hub lacks complete files
3. **Document dependencies** - `sentencepiece` is required for RoBERTa tokenizers
4. **Validate dataset** before training - verify that labels != -100 exist

---

## Training Commands

```bash
cd ml
source .venv/bin/activate

# Regenerate dataset (already done)
python scripts/preprocess/inject_ocr_noise.py

# Train model v2
python scripts/train/train_ner.py
```

**Expected output:** `models/legal_ner_v2/`

---

**Resolution time:** ~45 min
