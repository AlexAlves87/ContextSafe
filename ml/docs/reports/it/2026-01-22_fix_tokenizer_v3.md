# Fix: Dataset Tokenizer v3 - Etichette Vuote

**Data:** 2026-01-22
**Autor:** AlexAlves87
**Tipo:** Debugging / Post-mortem
**Stato:** Risolto

---

## Riepilogo del Problema

Il dataset v3 generato con `inject_ocr_noise.py` produceva tutte le etichette come `-100`, causando `ZeroDivisionError` durante l'addestramento.

**Sintomi:**
```
ZeroDivisionError: division by zero
# In seqeval accuracy_score
# Perché non c'erano etichette valide da valutare
```

**Diagnosi:**
```python
ds = load_from_disk('data/processed/ner_dataset_v3')
sample = ds['validation'][0]
labels = sample['labels']
non_special = [l for l in labels if l != -100]
print(f'Non-special labels: {len(non_special)}')  # Output: 0  <- ERRORE
```

---

## Causa Radice

### Problema 1: Dipendenza Mancante

Il tokenizer richiede `sentencepiece` per caricare correttamente i file di vocabolario. Senza questa dipendenza:

```python
tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne", use_fast=True)
print(tokenizer.vocab_size)  # Output: 5 (solo token speciali!)
print(tokenizer.word_ids())  # Output: [None, None, ...] (tutto None)
```

**Errore sottostante:**
```
ValueError: Couldn't instantiate the backend tokenizer from one of:
(1) a `tokenizers` library serialization file,
(2) a slow tokenizer instance to convert or
(3) an equivalent slow tokenizer class to instantiate and convert.
You need to have sentencepiece or tiktoken installed to convert a slow tokenizer to a fast one.
```

### Problema 2: Modello HuggingFace Incompleto

Il modello `PlanTL-GOB-ES/roberta-base-bne` su HuggingFace Hub non ha i file del modello/tokenizer caricati (solo `.gitattributes` e `README.md`).

---

## Soluzione Applicata

### 1. Installare dipendenze mancanti

```bash
pip install sentencepiece protobuf
```

### 2. Usare checkpoint locale invece di HuggingFace Hub

**Prima (rotto):**
```python
MODEL_NAME = "PlanTL-GOB-ES/roberta-base-bne"
```

**Dopo (fissato):**
```python
MODEL_NAME = str(BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner")
```

Il checkpoint locale ha tutti i file necessari:
- `config.json`
- `model.safetensors`
- `tokenizer.json` (3.6 MB con vocabolario completo)
- `tokenizer_config.json`

### 3. Rigenerare dataset

```bash
python scripts/preprocess/inject_ocr_noise.py
```

---

## Verifica

**Dopo il fix:**
```python
tokenizer = AutoTokenizer.from_pretrained(local_path, use_fast=True)
print(tokenizer.vocab_size)  # Output: 50262 (corretto!)

encoding = tokenizer("Don José García López con DNI 12345678Z", return_offsets_mapping=True)
print(encoding.word_ids())  # Output: [None, 0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 7, None] (corretto!)
```

**Dataset v3 rigenerato:**
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

## File Modificati

| File | Modifica |
|---------|--------|
| `scripts/preprocess/inject_ocr_noise.py` | `MODEL_NAME` → checkpoint locale |
| `requirements.txt` (in sospeso) | Aggiungere `sentencepiece`, `protobuf` |

---

## Lezioni Apprese

1. **Verificare vocab_size** dopo il caricamento del tokenizer - se < 100, qualcosa non va
2. **Usare checkpoint locali** quando HuggingFace Hub manca di file completi
3. **Documentare dipendenze** - `sentencepiece` è richiesto per i tokenizer RoBERTa
4. **Validare dataset** prima dell'addestramento - verificare che esistano etichette != -100

---

## Comandi per Addestrare

```bash
cd ml
source .venv/bin/activate

# Rigenerare dataset (già fatto)
python scripts/preprocess/inject_ocr_noise.py

# Addestrare modello v2
python scripts/train/train_ner.py
```

**Output atteso:** `models/legal_ner_v2/`

---

**Tempo di risoluzione:** ~45 min
