# Correctif : Dataset Tokenizer v3 - Labels Vides

**Date :** 2026-01-22
**Type :** Débogage / Post-mortem
**Statut :** Résolu

---

## Résumé du Problème

Le dataset v3 généré avec `inject_ocr_noise.py` produisait tous les labels comme `-100`, causant une `ZeroDivisionError` pendant l'entraînement.

**Symptômes :**
```
ZeroDivisionError: division by zero
# Dans seqeval accuracy_score
# Parce qu'il n'y avait pas de labels valides à évaluer
```

**Diagnostic :**
```python
ds = load_from_disk('data/processed/ner_dataset_v3')
sample = ds['validation'][0]
labels = sample['labels']
non_special = [l for l in labels if l != -100]
print(f'Non-special labels: {len(non_special)}')  # Output: 0  <- ERREUR
```

---

## Cause Racine

### Problème 1 : Dépendance Manquante

Le tokenizer nécessite `sentencepiece` pour charger correctement les fichiers de vocabulaire. Sans cette dépendance :

```python
tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne", use_fast=True)
print(tokenizer.vocab_size)  # Output: 5 (seulement tokens spéciaux !)
print(tokenizer.word_ids())  # Output: [None, None, ...] (tout à None)
```

**Erreur sous-jacente :**
```
ValueError: Couldn't instantiate the backend tokenizer from one of:
(1) a `tokenizers` library serialization file,
(2) a slow tokenizer instance to convert or
(3) an equivalent slow tokenizer class to instantiate and convert.
You need to have sentencepiece or tiktoken installed to convert a slow tokenizer to a fast one.
```

### Problème 2 : Modèle HuggingFace Incomplet

Le modèle `PlanTL-GOB-ES/roberta-base-bne` sur HuggingFace Hub n'a pas les fichiers du modèle/tokenizer téléversés (seulement `.gitattributes` et `README.md`).

---

## Solution Appliquée

### 1. Installer les dépendances manquantes

```bash
pip install sentencepiece protobuf
```

### 2. Utiliser un checkpoint local au lieu de HuggingFace Hub

**Avant (brisé) :**
```python
MODEL_NAME = "PlanTL-GOB-ES/roberta-base-bne"
```

**Après (corrigé) :**
```python
MODEL_NAME = str(BASE_DIR / "models" / "checkpoints" / "roberta-base-bne-capitel-ner")
```

Le checkpoint local contient tous les fichiers nécessaires :
- `config.json`
- `model.safetensors`
- `tokenizer.json` (3.6 Mo avec vocabulaire complet)
- `tokenizer_config.json`

### 3. Regénérer le dataset

```bash
python scripts/preprocess/inject_ocr_noise.py
```

---

## Vérification

**Après le correctif :**
```python
tokenizer = AutoTokenizer.from_pretrained(local_path, use_fast=True)
print(tokenizer.vocab_size)  # Output: 50262 (correct !)

encoding = tokenizer("Don José García López con DNI 12345678Z", return_offsets_mapping=True)
print(encoding.word_ids())  # Output: [None, 0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 7, None] (correct !)
```

**Dataset v3 regénéré :**
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

## Fichiers Modifiés

| Fichier | Changement |
|---------|--------|
| `scripts/preprocess/inject_ocr_noise.py` | `MODEL_NAME` → checkpoint local |
| `requirements.txt` (en attente) | Ajouter `sentencepiece`, `protobuf` |

---

## Leçons Apprises

1. **Vérifier vocab_size** après le chargement du tokenizer - si < 100, quelque chose ne va pas
2. **Utiliser des checkpoints locaux** quand HuggingFace Hub manque de fichiers complets
3. **Documenter les dépendances** - `sentencepiece` est requis pour les tokenizers RoBERTa
4. **Valider le dataset** avant l'entraînement - vérifier que des labels != -100 existent

---

## Commandes d'Entraînement

```bash
cd ml
source .venv/bin/activate

# Regénérer le dataset (déjà fait)
python scripts/preprocess/inject_ocr_noise.py

# Entraîner le modèle v2
python scripts/train/train_ner.py
```

**Sortie attendue :** `models/legal_ner_v2/`

---

**Temps de résolution :** ~45 min
