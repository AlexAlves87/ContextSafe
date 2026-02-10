# Ricerca: Standard Accademici per la Valutazione NER

**Data:** 2026-01-28
**Autor:** AlexAlves87
**Tipo:** Revisione della Letteratura Accademica
**Stato:** Completato

---

## 1. Riepilogo Esecutivo

Questa ricerca documenta gli standard accademici per la valutazione dei sistemi NER, con enfasi su:
1. Metriche a livello di entità (SemEval 2013 Task 9)
2. Valutazione avversaria (RockNER, NoiseBench)
3. Framework di valutazione (seqeval, nervaluate)
4. Best practices per test di robustezza

### Scoperte Principali

| Scoperta | Fonte | Impatto |
|----------|-------|---------|
| 4 modalità di valutazione: strict, exact, partial, type | SemEval 2013 | **CRITICO** |
| seqeval è lo standard de facto per F1 a livello di entità | CoNLL, HuggingFace | Alto |
| RockNER: perturbazioni a livello entità + livello contesto | EMNLP 2021 | Alto |
| NoiseBench: rumore reale >> rumore simulato in difficoltà | EMNLP 2024 | Alto |
| nervaluate fornisce metriche più granulari di seqeval | MantisAI | Medio |

---

## 2. Metodologia

### 2.1 Fonti Consultate

| Fonte | Tipo | Anno | Rilevanza |
|-------|------|------|-----------|
| SemEval 2013 Task 9 | Shared Task | 2013 | Definizione metriche |
| RockNER (EMNLP 2021) | Paper ACL | 2021 | Valutazione avversaria |
| NoiseBench (EMNLP 2024) | Paper ACL | 2024 | Rumore realistico |
| seqeval | Libreria | 2018+ | Implementazione standard |
| nervaluate | Libreria | 2020+ | Metriche estese |
| David Batista Blog | Tutorial | 2018 | Spiegazione dettagliata |

### 2.2 Criteri di Ricerca

- "adversarial NER evaluation benchmark methodology"
- "NER robustness testing framework seqeval entity level"
- "SemEval 2013 task 9 entity level metrics"
- "RockNER adversarial NER EMNLP methodology"
- "NoiseBench NER evaluation realistic noise"

---

## 3. Standard di Valutazione a Livello di Entità

### 3.1 SemEval 2013 Task 9: Le 4 Modalità di Valutazione

**Fonte:** [Named-Entity evaluation metrics based on entity-level](https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/)

Lo standard SemEval 2013 definisce **4 modalità** di valutazione:

| Modalità | Confine | Tipo | Descrizione |
|----------|---------|------|-------------|
| **Strict** | Esatto | Esatto | Confine E tipo devono corrispondere |
| **Exact** | Esatto | Ignorato | Solo confine esatto |
| **Partial** | Sovrapposizione | Ignorato | Basta sovrapposizione parziale |
| **Type** | Sovrapposizione | Esatto | Sovrapposizione + tipo corretto |

#### 3.1.1 Definizione Metriche Base

| Metrica | Definizione |
|---------|-------------|
| **COR** (Corretto) | Sistema e gold sono identici |
| **INC** (Incorretto) | Sistema e gold non corrispondono |
| **PAR** (Parziale) | Sistema e gold hanno sovrapposizione parziale |
| **MIS** (Mancante) | Gold non catturato dal sistema (FN) |
| **SPU** (Spurio) | Sistema produce qualcosa non nel gold (FP) |
| **POS** (Possibile) | COR + INC + PAR + MIS = totale gold |
| **ACT** (Attuale) | COR + INC + PAR + SPU = totale sistema |

#### 3.1.2 Formule di Calcolo

**Per modalità esatte (strict, exact):**
```
Precision = COR / ACT
Recall = COR / POS
F1 = 2 * (P * R) / (P + R)
```

**Per modalità parziali (partial, type):**
```
Precision = (COR + 0.5 × PAR) / ACT
Recall = (COR + 0.5 × PAR) / POS
F1 = 2 * (P * R) / (P + R)
```

### 3.2 seqeval: Implementazione Standard

**Fonte:** [seqeval GitHub](https://github.com/chakki-works/seqeval)

seqeval è il framework standard per la valutazione di sequence labeling, validato contro lo script Perl `conlleval` di CoNLL-2000.

#### Caratteristiche

| Funzionalità | Descrizione |
|--------------|-------------|
| Formato | CoNLL (tag BIO/BIOES) |
| Metriche | Precision, Recall, F1 per tipo e globale |
| Modalità default | Simula conlleval (indulgente con B/I) |
| Modalità strict | Solo corrispondenze esatte |

#### Uso Corretto

```python
from seqeval.metrics import classification_report, f1_score
from seqeval.scheme import IOB2

# Modalità strict (raccomandata per valutazione rigorosa)
f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
report = classification_report(y_true, y_pred, mode='strict', scheme=IOB2)
```

**IMPORTANTE:** La modalità di default di seqeval è indulgente. Per valutazione rigorosa, usare `mode='strict'`.

### 3.3 nervaluate: Metriche Estese

**Fonte:** [nervaluate GitHub](https://github.com/MantisAI/nervaluate)

nervaluate implementa completamente tutte e 4 le modalità di SemEval 2013.

#### Vantaggi su seqeval

| Aspetto | seqeval | nervaluate |
|---------|---------|------------|
| Modalità | 2 (default, strict) | 4 (strict, exact, partial, type) |
| Granularità | Per tipo entità | Per tipo + per scenario |
| Metriche | P/R/F1 | P/R/F1 + COR/INC/PAR/MIS/SPU |

#### Uso

```python
from nervaluate import Evaluator

evaluator = Evaluator(true_labels, pred_labels, tags=['PER', 'ORG', 'LOC'])
results, results_per_tag = evaluator.evaluate()

# Accedere a modalità strict
strict_f1 = results['strict']['f1']

# Accedere a metriche dettagliate
cor = results['strict']['correct']
inc = results['strict']['incorrect']
par = results['partial']['partial']
```

---

## 4. Valutazione Avversaria: Standard Accademici

### 4.1 RockNER (EMNLP 2021)

**Fonte:** [RockNER - ACL Anthology](https://aclanthology.org/2021.emnlp-main.302/)

RockNER propone un framework sistematico per creare esempi avversari naturali.

#### Tassonomia delle Perturbazioni

| Livello | Metodo | Descrizione |
|---------|--------|-------------|
| **Livello Entità** | Sostituzione Wikidata | Sostituire entità con altre della stessa classe semantica |
| **Livello Contesto** | BERT MLM | Generare sostituzioni di parole con LM |
| **Combinato** | Entrambi | Applicare entrambi per massima avversarità |

#### OntoRock Benchmark

- Derivato da OntoNotes
- Applica perturbazioni sistematiche
- Misura degradazione di F1

#### Scoperta Chiave

> "Even the best model has a significant performance drop... models seem to memorize in-domain entity patterns instead of reasoning from the context."

### 4.2 NoiseBench (EMNLP 2024)

**Fonte:** [NoiseBench - ACL Anthology](https://aclanthology.org/2024.emnlp-main.1011/)

NoiseBench dimostra che il rumore simulato è **significativamente più facile** del rumore reale.

#### Tipi di Rumore Reale

| Tipo | Fonte | Descrizione |
|------|-------|-------------|
| Errori esperti | Annotatori esperti | Errori di fatica, interpretazione |
| Crowdsourcing | Amazon Turk, ecc. | Errori di non esperti |
| Annotazione automatica | Regex, euristiche | Errori sistematici |
| Errori LLM | GPT, ecc. | Allucinazioni, incoerenze |

#### Scoperta Chiave

> "Real noise is significantly more challenging than simulated noise, and current state-of-the-art models for noise-robust learning fall far short of their theoretically achievable upper bound."

### 4.3 Tassonomia delle Perturbazioni per NER

Basato sulla letteratura, le perturbazioni avversarie sono classificate in:

| Categoria | Esempi | Paper |
|-----------|--------|-------|
| **Livello carattere** | Typos, errori OCR, omoglifi | RockNER, NoiseBench |
| **Livello token** | Sinonimi, flessioni | RockNER |
| **Livello entità** | Sostituzione con entità simili | RockNER |
| **Livello contesto** | Modificare contesto circostante | RockNER |
| **Livello formato** | Spazi, punteggiatura, casing | NoiseBench |
| **Livello semantico** | Negazioni, esempi fittizi | Custom |

---

## 5. Revisione dei Test Attuali vs Standard

### 5.1 Test Avversari Attuali

Il nostro script `test_ner_predictor_adversarial.py` ha:

| Categoria | Test | Copertura |
|-----------|------|-----------|
| edge_case | 9 | Condizioni limite |
| adversarial | 8 | Confusione semantica |
| ocr_corruption | 5 | Errori OCR |
| unicode_evasion | 3 | Evasione Unicode |
| real_world | 10 | Documenti reali |

### 5.2 Gap Identificati

| Gap | Standard | Stato Attuale | Severità |
|-----|----------|---------------|----------|
| Modalità strict vs default | seqeval strict | Non specificato | **CRITICO** |
| 4 modalità SemEval | nervaluate | Solo 1 modalità | ALTO |
| Perturbazioni livello entità | RockNER | Non sistematico | ALTO |
| Metriche COR/INC/PAR/MIS/SPU | SemEval 2013 | Non riportate | MEDIO |
| Rumore reale vs simulato | NoiseBench | Solo simulato | MEDIO |
| Perturbazioni livello contesto | RockNER | Parziale | MEDIO |

### 5.3 Metriche Attuali vs Richieste

| Metrica | Attuale | Richiesto | Gap |
|---------|---------|-----------|-----|
| F1 overall | ✅ | ✅ | OK |
| Precision/Recall | ✅ | ✅ | OK |
| F1 per tipo entità | ❌ | ✅ | **MANCANTE** |
| Modalità strict | ❓ | ✅ | **VERIFICARE** |
| COR/INC/PAR/MIS/SPU | ❌ | ✅ | **MANCANTE** |
| 4 modalità SemEval | ❌ | ✅ | **MANCANTE** |

---

## 6. Raccomandazioni di Miglioramento

### 6.1 Priorità CRITICA

1. **Verificare modalità strict in seqeval**
   ```python
   # Cambiare da:
   f1 = f1_score(y_true, y_pred)
   # A:
   f1 = f1_score(y_true, y_pred, mode='strict', scheme=IOB2)
   ```

2. **Riportare metriche per tipo entità**
   ```python
   report = classification_report(y_true, y_pred, mode='strict')
   ```

### 6.2 Priorità ALTA

3. **Implementare le 4 modalità di SemEval**
   - Usare nervaluate invece di (o in aggiunta a) seqeval
   - Riportare strict, exact, partial, type

4. **Aggiungere perturbazioni livello entità (stile RockNER)**
   - Sostituire nomi con altri nomi spagnoli
   - Sostituire ID con altri ID validi
   - Mantenere contesto, cambiare entità

### 6.3 Priorità MEDIA

5. **Riportare COR/INC/PAR/MIS/SPU**
   - Permette analisi più fine degli errori
   - Distingue tra errori di confine ed errori di tipo

6. **Aggiungere perturbazioni livello contesto**
   - Modificare verbi/aggettivi circostanti
   - Usare BERT/spaCy per sostituzioni naturali

---

## 7. Checklist di Valutazione Accademica

### 7.1 Prima di Riportare Risultati

- [ ] Specificare modalità di valutazione (strict/default)
- [ ] Usare formato CoNLL standard (BIO/BIOES)
- [ ] Riportare F1, Precision, Recall
- [ ] Riportare metriche per tipo entità
- [ ] Documentare versione di seqeval/nervaluate usata
- [ ] Includere intervalli di confidenza se c'è varianza

### 7.2 Per Valutazione Avversaria

- [ ] Categorizzare perturbazioni (Carattere, Token, Entità, Contesto)
- [ ] Misurare degradazione relativa (F1_clean - F1_adversarial)
- [ ] Riportare pass rate per categoria di difficoltà
- [ ] Includere analisi errori con esempi
- [ ] Confrontare con baseline (modello non modificato)

### 7.3 Per Pubblicazione/Documentazione

- [ ] Descrivere metodologia riproducibile
- [ ] Pubblicare dataset di test (o generatore)
- [ ] Riportare tempo di esecuzione
- [ ] Includere analisi statistica se applicabile

---

## 8. Conclusioni

### 8.1 Azioni Immediate

1. **Revisionare script avversario** per verificare modalità strict
2. **Aggiungere nervaluate** per metriche complete
3. **Riorganizzare test** secondo tassonomia RockNER

### 8.2 Impatto sui Risultati Attuali

I risultati attuali (F1=0.784, 54.3% pass rate) potrebbero cambiare se:
- La modalità non era strict (risultati sarebbero inferiori in strict)
- Le metriche per tipo rivelano debolezze specifiche
- Le 4 modalità mostrano comportamento diverso in confine vs tipo

---

## 9. Riferimenti

### Paper Accademici

1. **RockNER: A Simple Method to Create Adversarial Examples for Evaluating the Robustness of Named Entity Recognition Models**
   - Lin et al., EMNLP 2021
   - URL: https://aclanthology.org/2021.emnlp-main.302/

2. **NoiseBench: Benchmarking the Impact of Real Label Noise on Named Entity Recognition**
   - Merdjanovska et al., EMNLP 2024
   - URL: https://aclanthology.org/2024.emnlp-main.1011/

3. **SemEval-2013 Task 9: Extraction of Drug-Drug Interactions from Biomedical Texts**
   - Segura-Bedmar et al., SemEval 2013
   - Definizione metriche a livello entità

### Strumenti e Librerie

4. **seqeval**
   - URL: https://github.com/chakki-works/seqeval

5. **nervaluate**
   - URL: https://github.com/MantisAI/nervaluate

6. **Named-Entity Evaluation Metrics Based on Entity-Level**
   - David Batista, 2018
   - URL: https://www.davidsbatista.net/blog/2018/05/09/Named_Entity_Evaluation/

---

**Tempo di ricerca:** 45 min
**Generato da:** AlexAlves87
**Data:** 2026-01-28
