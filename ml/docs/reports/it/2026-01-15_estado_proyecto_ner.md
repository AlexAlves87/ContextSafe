# Rapporto di Stato: Sistema NER-PII per Documenti Legali Spagnoli

**Data:** 2026-01-15
**Versione:** 1.0
**Autor:** AlexAlves87
**Progetto:** ContextSafe ML - Fine-tuning NER

---

## Riepilogo Esecutivo

Questo rapporto documenta lo sviluppo del sistema di rilevamento di PII (Personally Identifiable Information) per documenti legali spagnoli. Il sistema deve rilevare 13 categorie di entità con F1 ≥ 0.85.

### Stato Attuale

| Fase | Stato | Progresso |
|------|--------|----------|
| Download dati base | Completato | 100% |
| Generazione di gazetteer | Completato | 100% |
| Dataset sintetico v1 | Scartato | Errore Critico |
| Dataset sintetico v2 | Completato | 100% |
| Script di addestramento | Completato | 100% |
| Addestramento del modello | In attesa | 0% |

---

## 1. Obiettivo del Progetto

Sviluppare un modello NER specializzato in documenti legali spagnoli (testamenti, sentenze, atti, contratti) in grado di rilevare:

| Categoria | Esempi | Priorità |
|-----------|----------|-----------|
| PERSON | Hermógenes Pérez García | Alta |
| DATE | 15 de marzo de 2024 | Alta |
| DNI_NIE | 12345678Z, X1234567A | Alta |
| IBAN | ES9121000418450200051332 | Alta |
| NSS | 281234567890 | Media |
| PHONE | 612 345 678 | Media |
| ADDRESS | Calle Mayor 15, 3º B | Alta |
| POSTAL_CODE | 28001 | Media |
| ORGANIZATION | Banco Santander, S.A. | Alta |
| LOCATION | Madrid, Comunidad de Madrid | Media |
| ECLI | ECLI:ES:TS:2024:1234 | Bassa |
| LICENSE_PLATE | 1234 ABC | Bassa |
| CADASTRAL_REF | 1234567AB1234S0001AB | Bassa |
| PROFESSIONAL_ID | Colegiado nº 12345 | Bassa |

---

## 2. Dati Scaricati

### 2.1 Fonti Ufficiali

| Risorsa | Posizione | Dimensione | Descrizione |
|---------|-----------|--------|-------------|
| CoNLL-2002 Spanish | `data/raw/conll2002/` | 4.0 MB | Corpus NER standard |
| INE Nomi per decade | `data/raw/gazetteers_ine/nombres_por_fecha.xls` | 1.1 MB | Frequenza temporale |
| INE Nomi frequenti | `data/raw/gazetteers_ine/nombres_mas_frecuentes.xls` | 278 KB | Top nomi |
| INE Cognomi | `data/raw/gazetteers_ine/apellidos_frecuencia.xls` | 12 MB | 27.251 cognomi |
| INE Comuni 2024 | `data/raw/municipios/municipios_2024.xlsx` | 300 KB | 8.115 comuni |
| Codici postali | `data/raw/codigos_postales/codigos_postales.csv` | 359 KB | 11.051 CP |
| ai4privacy/pii-masking-300k | `data/raw/ai4privacy/` | ~100 MB | Transfer learning |

### 2.2 Modello Base

| Modello | Posizione | Dimensione | F1 Base |
|--------|-----------|--------|---------|
| roberta-base-bne-capitel-ner | `models/checkpoints/` | ~500 MB | 88.5% (CAPITEL) |

**Decisione del modello:** È stato valutato MEL (Modello Legale Spagnolo) ma manca di fine-tuning NER. RoBERTa-BNE-capitel-ner è stato selezionato per la sua specializzazione in NER spagnolo.

---

## 3. Gazetteer Generati

### 3.1 Script di Generazione

| Script | Funzione | Output |
|--------|---------|--------|
| `parse_ine_gazetteers.py` | Parsa INE Excel → JSON | apellidos.json, nombres_*.json |
| `generate_archaic_names.py` | Genera nomi arcaici legali | nombres_arcaicos.json |
| `generate_textual_dates.py` | Date in formato legale | fechas_textuales.json |
| `generate_administrative_ids.py` | DNI, NIE, IBAN, NSS con checksum non validi | identificadores_administrativos.json |
| `generate_addresses.py` | Indirizzi spagnoli completi | direcciones.json |
| `generate_organizations.py` | Aziende, tribunali, banche | organizaciones.json |

### 3.2 File Generati

| File | Dimensione | Contenuto |
|---------|--------|-----------|
| `apellidos.json` | 1.8 MB | 27.251 cognomi con frequenze INE |
| `codigos_postales.json` | 1.2 MB | 11.051 codici postali |
| `municipios.json` | 164 KB | 8.115 comuni spagnoli |
| `nombres_hombres.json` | 40 KB | 550 nomi maschili per decade |
| `nombres_mujeres.json` | 41 KB | 550 nomi femminili per decade |
| `nombres_todos.json` | 3.9 KB | 260 nomi unici (INE) |
| `nombres_arcaicos.json` | 138 KB | 940 nomi arcaici + 5.070 combinazioni |
| `nombres_arcaicos_flat.json` | 267 KB | Lista piatta per NER |
| `fechas_textuales.json` | 159 KB | 645 date con 41 pattern legali |
| `fechas_textuales_flat.json` | 86 KB | Lista piatta |
| `identificadores_administrativos.json` | 482 KB | 2.550 ID sintetici |
| `identificadores_administrativos_flat.json` | 134 KB | Lista piatta |
| `direcciones.json` | 159 KB | 600 indirizzi + 416 con contesto legale |
| `direcciones_flat.json` | 59 KB | Lista piatta |
| `organizaciones.json` | 185 KB | 1.000 organizzazioni |
| `organizaciones_flat.json` | 75 KB | Lista piatta |

**Totale gazetteer:** ~4.9 MB

### 3.3 Caratteristiche Speciali

**Nomi Arcaici:** Include nomi frequenti in documenti legali storici:
- Hermógenes, Segismundo, Práxedes, Gertrudis, Baldomero, Saturnino, Patrocinio...
- Combinazioni composte: María del Carmen, José Antonio, Juan de Dios...

**Identificatori Amministrativi:** Generati con checksum MATEMATICAMENTE NON VALIDI:
- DNI: Lettera di controllo errata (mod-23 errato)
- NIE: Prefisso X/Y/Z con lettera errata
- IBAN: Cifre di controllo "00" (sempre non valido)
- NSS: Cifre di controllo errate (mod-97)

Ciò garantisce che nessun identificatore sintetico corrisponda a dati reali.

---

## 4. Dataset Sintetico

### 4.1 Dataset v1 - ERRORE CRITICO (SCARTATO)

**Data:** 2026-01-15

Il primo dataset generato conteneva errori critici che avrebbero degradato significativamente il modello.

#### Errore 1: Punteggiatura Aderente ai Token

**Problema:** La tokenizzazione semplice tramite spazi bianchi causava l'aderenza della punteggiatura alle entità.

**Esempio dell'errore:**
```
Testo: "Don Hermógenes Freijanes, con DNI 73364386X."
Token: ["Don", "Hermógenes", "Freijanes,", "con", "DNI", "73364386X."]
Label: ["O",   "B-PERSON",   "I-PERSON",   "O",   "O",   "B-DNI_NIE"]
```

**Impatto:** Il modello imparerebbe che "Freijanes," (con virgola) è una persona, ma durante l'inferenza non riconoscerebbe "Freijanes" senza virgola.

**Statistiche dell'errore:**
- 6.806 token con punteggiatura aderente
- Colpiva principalmente: PERSON, DNI_NIE, IBAN, PHONE
- ~30% delle entità compromesse

#### Errore 2: Nessun Allineamento di Subword

**Problema:** I tag BIO erano a livello di parola, ma BERT utilizza la tokenizzazione in subword.

**Esempio dell'errore:**
```
Parola: "Hermógenes"
Subword: ["Her", "##mó", "##genes"]
Label v1: Solo un tag per l'intera parola → quale subword lo riceve?
```

**Impatto:** Senza allineamento esplicito, il modello non potrebbe apprendere correttamente la relazione tra subword e tag.

#### Errore 3: Squilibrio delle Entità

| Entità | Percentuale v1 | Problema |
|---------|---------------|----------|
| PERSON | 30.3% | Sovrarappresentato |
| ADDRESS | 12.6% | OK |
| DNI_NIE | 10.1% | OK |
| NSS | 1.7% | Sottorappresentato |
| ECLI | 1.7% | Sottorappresentato |
| LICENSE_PLATE | 1.7% | Sottorappresentato |

### 4.2 Dataset v2 - CORRETTO

**Data:** 2026-01-15

**Script:** `scripts/preprocess/generate_ner_dataset_v2.py`

#### Correzioni Implementate

**1. Tokenizzazione con HuggingFace:**
```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne")

# La tokenizzazione separa automaticamente la punteggiatura
# "Freijanes," → ["Fre", "##ij", "##anes", ","]
```

**2. Allineamento con word_ids():**
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
            labels.append(-100)  # Token speciale
        elif word_id != previous_word_id:
            labels.append(entity_label)  # Prima subword
        else:
            labels.append(-100)  # Continuazione
```

**3. Template Bilanciati:**
- Aggiunti 50+ template specifici per entità minoritarie
- Aumentata frequenza di NSS, ECLI, LICENSE_PLATE, CADASTRAL_REF

#### Statistiche v2

| Split | Campioni | Token Totali |
|-------|----------|----------------|
| Train | 4.925 | ~630.000 |
| Validation | 818 | ~105.000 |
| Test | 818 | ~105.000 |
| **Totale** | **6.561** | **~840.000** |

**Distribuzione delle entità v2:**

| Entità | Conteggio | % |
|---------|-------|---|
| PERSON | 1.800 | 24.4% |
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

#### Formato di Uscita

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

**Schema dei dati:**
```python
{
    "input_ids": [0, 1234, 5678, ...],      # Token IDs
    "attention_mask": [1, 1, 1, ...],        # Maschera di attenzione
    "labels": [-100, 1, 2, -100, ...],       # Label allineate
}
```

**Label (29 classi):**
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

## 5. Configurazione dell'Addestramento

### 5.1 Ricerca delle Migliori Pratiche

Le migliori pratiche per il fine-tuning di NER sono state investigate basandosi su:
- Documentazione HuggingFace
- Paper accademici (RoBERTa, BERT per NER)
- Benchmark di modelli spagnoli (CAPITEL, AnCora)

### 5.2 Iperparametri Selezionati

**File:** `scripts/train/train_ner.py`

```python
CONFIG = {
    # Ottimizzazione (PIÙ IMPORTANTE)
    "learning_rate": 2e-5,          # Grid: {1e-5, 2e-5, 3e-5, 5e-5}
    "weight_decay": 0.01,           # Regolarizzazione L2
    "adam_epsilon": 1e-8,           # Stabilità numerica

    # Batching
    "per_device_train_batch_size": 16,
    "per_device_eval_batch_size": 32,
    "gradient_accumulation_steps": 2,  # Batch effettivo = 32

    # Epoche
    "num_train_epochs": 4,          # Conservativo per il legale

    # Scheduling del Learning Rate
    "warmup_ratio": 0.06,           # 6% warmup (paper RoBERTa)
    "lr_scheduler_type": "linear",  # Decadimento lineare

    # Early Stopping
    "early_stopping_patience": 2,   # Stop se nessun miglioramento in 2 eval
    "metric_for_best_model": "f1",

    # Lunghezza della Sequenza
    "max_length": 384,              # Documenti legali lunghi

    # Hardware
    "fp16": True,                   # Precisione mista se GPU
    "dataloader_num_workers": 4,

    # Riproducibilità
    "seed": 42,
}
```

### 5.3 Giustificazione delle Decisioni

| Parametro | Valore | Giustificazione |
|-----------|-------|---------------|
| learning_rate | 2e-5 | Valore standard per fine-tuning BERT/RoBERTa |
| batch_size | 32 (effettivo) | Bilanciamento tra stabilità e memoria |
| epochs | 4 | Evitare overfitting su dati sintetici |
| warmup | 6% | Raccomandazione paper RoBERTa |
| max_length | 384 | I documenti legali possono essere estesi |
| early_stopping | 2 | Rilevamento precoce dell'overfitting |

### 5.4 Dipendenze

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

## 6. Lezioni Apprese

### 6.1 Errore ISS-001: Tokenizzazione Inadeguata

**Causa radice:** Assumere che la tokenizzazione per spazi bianchi fosse sufficiente per NER con modelli transformer.

**Impatto potenziale:** Se addestrato con il dataset v1:
- F1 degradato stimato: -15% a -25%
- Entità con punteggiatura non riconosciute
- Generalizzazione scarsa su testo reale

**Prevenzione futura:**
1. Usare sempre il tokenizer del modello base
2. Implementare audit del dataset prima di addestrare
3. Verificare allineamento subword-label esplicitamente

### 6.2 Importanza della Ricerca Precedente

Investigare le migliori pratiche PRIMA di implementare ha evitato:
- Iperparametri subottimali (es: learning_rate=1e-4 causa divergenza)
- Architettura errata (es: senza strato CRF in NER classico)
- Valutazione errata (es: accuracy vs F1 per NER)

### 6.3 Dati Sintetici: Punti di Forza e Limitazioni

**Punti di Forza:**
- Controllo totale sulla distribuzione delle entità
- Copertura di casi limite (nomi arcaici, formati rari)
- Volume scalabile senza costo di annotazione

**Limitazioni:**
- Pattern linguistici artificiali
- Nessun rumore reale (errori OCR, refusi)
- Richiede validazione su dati reali

---

## 7. Lavoro Futuro

### 7.1 Immediato (Prossimi passi)

1. **Eseguire addestramento:**
   ```bash
   cd ml
   source .venv/bin/activate
   pip install -r scripts/train/requirements_train.txt
   python scripts/train/train_ner.py
   ```

2. **Valutare per tipo di entità:**
   - Verificare F1 ≥ 0.85 per ogni categoria
   - Identificare entità problematiche

3. **Test adversarial:**
   - Nomi arcaici non visti
   - Formati di data ambigui
   - Indirizzi incompleti

### 7.2 Miglioramenti Potenziali

| Miglioramento | Priorità | Impatto Atteso |
|--------|-----------|------------------|
| Strato CRF | Alta | +4-13% F1 |
| Dati reali annotati | Alta | Migliore generalizzazione |
| Data augmentation | Media | +2-5% F1 |
| Ensemble con regex | Media | +3-5% recall |
| Active learning | Bassa | Riduzione costo annotazione |

### 7.3 Risorse Opzionali

Paper accademici in attesa di valutazione:
- MAPA Project (aclanthology.org/2022.lrec-1.400/) - Legal PII annotato
- 3CEL Contracts (arxiv.org/abs/2501.15990) - Clausole contrattuali
- IMPACT-es Corpus (arxiv.org/pdf/1306.3692.pdf) - Nomi storici

---

## 8. Struttura del Progetto

```
ml/
├── data/
│   ├── raw/
│   │   ├── conll2002/              # Corpus NER standard
│   │   ├── gazetteers_ine/         # Excel INE originali
│   │   ├── municipios/             # Comuni 2024
│   │   ├── codigos_postales/       # CP Spagna
│   │   └── ai4privacy/             # Dataset transfer learning
│   └── processed/
│       ├── gazetteers/             # JSON processati
│       ├── synthetic_sentences/     # Frasi v1 (scartato)
│       └── ner_dataset_v2/         # Dataset finale HuggingFace
├── models/
│   ├── checkpoints/                # Modello base RoBERTa-BNE
│   └── legal_ner_v1/               # Output addestramento (in attesa)
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
        └── 2026-01-15_estado_proyecto_ner.md  # Questo documento
```

---

## 9. Conclusioni

1. **Preparazione completata:** Gazetteer, dataset v2, e script di addestramento pronti.

2. **Errore critico evitato:** L'audit del dataset v1 ha identificato problemi che avrebbero degradato significativamente il modello.

3. **Migliori pratiche applicate:** Iperparametri basati sulla ricerca, non su supposizioni.

4. **Prossima pietra miliare:** Eseguire addestramento e valutare F1 per entità.

---

---

## 10. Riferimenti

### Modelli e Dataset

1. **RoBERTa-BNE-capitel-ner** - PlanTL-GOB-ES
   - https://huggingface.co/PlanTL-GOB-ES/roberta-base-bne-capitel-ner
   - F1 88.5% su CAPITEL

2. **CoNLL-2002 Spanish** - Corpus NER standard
   - https://www.clips.uantwerpen.be/conll2002/ner/

3. **ai4privacy/pii-masking-300k** - Dataset PII inglese
   - https://huggingface.co/datasets/ai4privacy/pii-masking-300k

### Dati Ufficiali INE

4. **Nomi per frequenza** - INE
   - https://www.ine.es/daco/daco42/nombyam/nombres_por_edad.xls

5. **Cognomi per frequenza** - INE
   - https://www.ine.es/daco/daco42/nombyam/apellidos_frecuencia.xls

6. **Comuni Spagna 2024** - INE
   - https://www.ine.es/daco/daco42/codmun/

### Paper e Documentazione

7. **RoBERTa: A Robustly Optimized BERT Pretraining Approach** - Liu et al., 2019
   - https://arxiv.org/abs/1907.11692
   - Riferimento per warmup ratio 6%

8. **HuggingFace Token Classification Guide**
   - https://huggingface.co/docs/transformers/tasks/token_classification
   - Guida all'allineamento subword-label

9. **seqeval: A Python framework for sequence labeling evaluation**
   - https://github.com/chakki-works/seqeval
   - Metriche entity-level per NER

### Paper in Attesa di Valutazione

10. **MAPA Project** - Legal PII annotato
    - https://aclanthology.org/2022.lrec-1.400/

11. **3CEL Contracts** - Clausole contrattuali
    - https://arxiv.org/abs/2501.15990

12. **IMPACT-es Corpus** - Nomi storici
    - https://arxiv.org/pdf/1306.3692.pdf

---

**Ultimo aggiornamento:** 2026-02-03
**Prossima revisione:** Post-addestramento
