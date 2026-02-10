# Fix: Tokenizer Dataset v3 - Leere Labels

**Datum:** 2026-01-22
**Autor:** AlexAlves87
**Typ:** Debugging / Post-mortem
**Status:** Behoben

---

## Zusammenfassung des Problems

Der mit `inject_ocr_noise.py` generierte Datensatz v3 erzeugte alle Labels als `-100`, was zu `ZeroDivisionError` während des Trainings führte.

**Symptome:**
```
ZeroDivisionError: division by zero
# In seqeval accuracy_score
# Weil keine gültigen Labels zum Bewerten vorhanden waren
```

**Diagnose:**
```python
ds = load_from_disk('data/processed/ner_dataset_v3')
sample = ds['validation'][0]
labels = sample['labels']
non_special = [l for l in labels if l != -100]
print(f'Non-special labels: {len(non_special)}')  # Output: 0  <- FEHLER
```

---

## Grundursache

### Problem 1: Fehlende Abhängigkeit

Der Tokenizer benötigt `sentencepiece`, um Vokabulardateien korrekt zu laden. Ohne diese Abhängigkeit:

```python
tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne", use_fast=True)
print(tokenizer.vocab_size)  # Output: 5 (nur spezielle Token!)
print(tokenizer.word_ids())  # Output: [None, None, ...] (alles None)
```

**Zugrundeliegender Fehler:**
```
ValueError: Couldn't instantiate the backend tokenizer from one of:
(1) a `tokenizers` library serialization file,
(2) a slow tokenizer instance to convert or
(3) an equivalent slow tokenizer class to instantiate and convert.
You need to have sentencepiece or tiktoken installed to convert a slow tokenizer to a fast one.
```

### Problem 2: Unvollständiges HuggingFace-Modell

Das Modell `PlanTL-GOB-ES/roberta-base-bne` auf HuggingFace Hub hat die Modell-/Tokenizer-Dateien nicht hochgeladen (nur `.gitattributes` und `README.md`).

---

## Angewandte Lösung

### 1. Fehlende Abhängigkeiten installieren

```bash
pip install sentencepiece protobuf
```

### 2. Lokalen Checkpoint statt HuggingFace Hub verwenden

**Vorher (kaputt):**
```python
MODEL_NAME = "PlanTL-GOB-ES/roberta-base-bne"
```

**Nachher (repariert):**
```python
MODEL_NAME = str(BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner")
```

Der lokale Checkpoint enthält alle notwendigen Dateien:
- `config.json`
- `model.safetensors`
- `tokenizer.json` (3,6 MB mit vollständigem Vokabular)
- `tokenizer_config.json`

### 3. Datensatz neu generieren

```bash
python scripts/preprocess/inject_ocr_noise.py
```

---

## Verifizierung

**Nach dem Fix:**
```python
tokenizer = AutoTokenizer.from_pretrained(local_path, use_fast=True)
print(tokenizer.vocab_size)  # Output: 50262 (korrekt!)

encoding = tokenizer("Don José García López con DNI 12345678Z", return_offsets_mapping=True)
print(encoding.word_ids())  # Output: [None, 0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 7, None] (korrekt!)
```

**Neu generierter Datensatz v3:**
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

## Modifizierte Dateien

| Datei | Änderung |
|---------|--------|
| `scripts/preprocess/inject_ocr_noise.py` | `MODEL_NAME` → lokaler Checkpoint |
| `requirements.txt` (ausstehend) | `sentencepiece`, `protobuf` hinzufügen |

---

## Gelernte Lektionen

1. **vocab_size prüfen** nach dem Laden des Tokenizers - wenn < 100, stimmt etwas nicht
2. **Lokale Checkpoints verwenden**, wenn HuggingFace Hub keine vollständigen Dateien hat
3. **Abhängigkeiten dokumentieren** - `sentencepiece` ist für RoBERTa-Tokenizer erforderlich
4. **Datensatz validieren** vor dem Training - überprüfen, ob Labels != -100 existieren

---

## Trainingsbefehle

```bash
cd ml
source .venv/bin/activate

# Datensatz neu generieren (bereits erledigt)
python scripts/preprocess/inject_ocr_noise.py

# Modell v2 trainieren
python scripts/train/train_ner.py
```

**Erwartete Ausgabe:** `models/legal_ner_v2/`

---

**Lösungszeit:** ~45 Min
