# Fix: Tokenizer Dataset v3 - Labels Vacíos

**Fecha:** 2026-01-22
**Autor:** AlexAlves87
**Tipo:** Debugging / Post-mortem
**Estado:** Resuelto

---

## Resumen del Problema

El dataset v3 generado con `inject_ocr_noise.py` producía todos los labels como `-100`, causando `ZeroDivisionError` durante el entrenamiento.

**Síntomas:**
```
ZeroDivisionError: division by zero
# En seqeval accuracy_score
# Porque no había labels válidos para evaluar
```

**Diagnóstico:**
```python
ds = load_from_disk('data/processed/ner_dataset_v3')
sample = ds['validation'][0]
labels = sample['labels']
non_special = [l for l in labels if l != -100]
print(f'Non-special labels: {len(non_special)}')  # Output: 0  <- ERROR
```

---

## Causa Raíz

### Problema 1: Dependencia Faltante

El tokenizer requiere `sentencepiece` para cargar correctamente los archivos de vocabulario. Sin esta dependencia:

```python
tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne", use_fast=True)
print(tokenizer.vocab_size)  # Output: 5 (solo tokens especiales!)
print(tokenizer.word_ids())  # Output: [None, None, ...] (todo None)
```

**Error subyacente:**
```
ValueError: Couldn't instantiate the backend tokenizer from one of:
(1) a `tokenizers` library serialization file,
(2) a slow tokenizer instance to convert or
(3) an equivalent slow tokenizer class to instantiate and convert.
You need to have sentencepiece or tiktoken installed to convert a slow tokenizer to a fast one.
```

### Problema 2: Modelo HuggingFace Incompleto

El modelo `PlanTL-GOB-ES/roberta-base-bne` en HuggingFace Hub no tiene los archivos del modelo/tokenizer subidos (solo `.gitattributes` y `README.md`).

---

## Solución Aplicada

### 1. Instalar dependencias faltantes

```bash
pip install sentencepiece protobuf
```

### 2. Usar checkpoint local en lugar de HuggingFace Hub

**Antes (broken):**
```python
MODEL_NAME = "PlanTL-GOB-ES/roberta-base-bne"
```

**Después (fixed):**
```python
MODEL_NAME = str(BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner")
```

El checkpoint local tiene todos los archivos necesarios:
- `config.json`
- `model.safetensors`
- `tokenizer.json` (3.6 MB con vocabulario completo)
- `tokenizer_config.json`

### 3. Regenerar dataset

```bash
python scripts/preprocess/inject_ocr_noise.py
```

---

## Verificación

**Después del fix:**
```python
tokenizer = AutoTokenizer.from_pretrained(local_path, use_fast=True)
print(tokenizer.vocab_size)  # Output: 50262 (correcto!)

encoding = tokenizer("Don José García López con DNI 12345678Z", return_offsets_mapping=True)
print(encoding.word_ids())  # Output: [None, 0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 7, None] (correcto!)
```

**Dataset v3 regenerado:**
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

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `scripts/preprocess/inject_ocr_noise.py` | `MODEL_NAME` → checkpoint local |
| `requirements.txt` (pendiente) | Añadir `sentencepiece`, `protobuf` |

---

## Lecciones Aprendidas

1. **Verificar vocab_size** después de cargar tokenizer - si es < 100, algo está mal
2. **Usar checkpoints locales** cuando HuggingFace Hub no tiene archivos completos
3. **Documentar dependencias** - `sentencepiece` es necesario para tokenizers RoBERTa
4. **Validar dataset** antes de entrenar - verificar que existan labels != -100

---

## Comandos para Entrenar

```bash
cd ml
source .venv/bin/activate

# Regenerar dataset (ya hecho)
python scripts/preprocess/inject_ocr_noise.py

# Entrenar modelo v2
python scripts/train/train_ner.py
```

**Output esperado:** `models/legal_ner_v2/`

---

**Tiempo de resolución:** ~45 min
