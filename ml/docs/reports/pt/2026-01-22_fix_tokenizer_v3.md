# Correção: Dataset Tokenizer v3 - Etiquetas Vazias

**Data:** 22-01-2026
**Autor:** AlexAlves87
**Tipo:** Debugging / Post-mortem
**Estado:** Resolvido

---

## Resumo do Problema

O dataset v3 gerado com `inject_ocr_noise.py` produzia todas as etiquetas como `-100`, causando `ZeroDivisionError` durante o treino.

**Sintomas:**
```
ZeroDivisionError: division by zero
# Em seqeval accuracy_score
# Porque não havia etiquetas válidas para avaliar
```

**Diagnóstico:**
```python
ds = load_from_disk('data/processed/ner_dataset_v3')
sample = ds['validation'][0]
labels = sample['labels']
non_special = [l for l in labels if l != -100]
print(f'Non-special labels: {len(non_special)}')  # Output: 0  <- ERRO
```

---

## Causa Raiz

### Problema 1: Dependência em Falta

O tokenizer requer `sentencepiece` para carregar corretamente ficheiros de vocabulário. Sem esta dependência:

```python
tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne", use_fast=True)
print(tokenizer.vocab_size)  # Output: 5 (apenas tokens especiais!)
print(tokenizer.word_ids())  # Output: [None, None, ...] (tudo None)
```

**Erro subjacente:**
```
ValueError: Couldn't instantiate the backend tokenizer from one of:
(1) a `tokenizers` library serialization file,
(2) a slow tokenizer instance to convert or
(3) an equivalent slow tokenizer class to instantiate and convert.
You need to have sentencepiece or tiktoken installed to convert a slow tokenizer to a fast one.
```

### Problema 2: Modelo HuggingFace Incompleto

O modelo `PlanTL-GOB-ES/roberta-base-bne` no HuggingFace Hub não tem os ficheiros do modelo/tokenizer carregados (apenas `.gitattributes` e `README.md`).

---

## Solução Aplicada

### 1. Instalar dependências em falta

```bash
pip install sentencepiece protobuf
```

### 2. Usar checkpoint local em vez de HuggingFace Hub

**Antes (quebrado):**
```python
MODEL_NAME = "PlanTL-GOB-ES/roberta-base-bne"
```

**Depois (corrigido):**
```python
MODEL_NAME = str(BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner")
```

O checkpoint local tem todos os ficheiros necessários:
- `config.json`
- `model.safetensors`
- `tokenizer.json` (3.6 MB com vocabulário completo)
- `tokenizer_config.json`

### 3. Regenerar dataset

```bash
python scripts/preprocess/inject_ocr_noise.py
```

---

## Verificação

**Após a correção:**
```python
tokenizer = AutoTokenizer.from_pretrained(local_path, use_fast=True)
print(tokenizer.vocab_size)  # Output: 50262 (correto!)

encoding = tokenizer("Don José García López con DNI 12345678Z", return_offsets_mapping=True)
print(encoding.word_ids())  # Output: [None, 0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 7, None] (correto!)
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

## Ficheiros Modificados

| Ficheiro | Alteração |
|---------|--------|
| `scripts/preprocess/inject_ocr_noise.py` | `MODEL_NAME` → checkpoint local |
| `requirements.txt` (pendente) | Adicionar `sentencepiece`, `protobuf` |

---

## Lições Aprendidas

1. **Verificar vocab_size** após carregar o tokenizer - se < 100, algo está errado
2. **Usar checkpoints locais** quando o HuggingFace Hub não tem ficheiros completos
3. **Documentar dependências** - `sentencepiece` é necessário para tokenizers RoBERTa
4. **Validar dataset** antes de treinar - verificar que existem etiquetas != -100

---

## Comandos para Treinar

```bash
cd ml
source .venv/bin/activate

# Regenerar dataset (já feito)
python scripts/preprocess/inject_ocr_noise.py

# Treinar modelo v2
python scripts/train/train_ner.py
```

**Output esperado:** `models/legal_ner_v2/`

---

**Tempo de resolução:** ~45 min
