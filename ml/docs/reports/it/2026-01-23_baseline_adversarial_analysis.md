# Analisi Avversaria Baseline: legal_ner_v2

**Data:** 2026-01-23
**Autor:** AlexAlves87
**Versione:** 1.0.0
**Modello Valutato:** `legal_ner_v2` (RoBERTalex fine-tuned)

---

## 1. Riepilogo Esecutivo

Questo documento presenta i risultati della valutazione avversaria del modello `legal_ner_v2` per il rilevamento di PII in testi legali spagnoli. L'obiettivo è stabilire una baseline di robustezza prima di implementare miglioramenti.

### Scoperte Principali

| Metrica | Valore | Interpretazione |
|---------|-------|----------------|
| F1-Score (livello entità) | **0.784** | Baseline accettabile |
| Precisione | 0.845 | Modello conservativo |
| Richiamo | 0.731 | Area di miglioramento prioritaria |
| Degradazione da rumore | 0.080 | Entro la soglia attesa (≤0.10) |
| Tasso superamento test | 54.3% (19/35) | Livello 4 non superato |

### Conclusione

Il modello **NON supera** il Livello 4 di validazione (avversario). Sono richiesti miglioramenti in:
1. Normalizzazione input (Unicode, spazi)
2. Riconoscimento date in formato testuale spagnolo
3. Pattern specifici per NSS e CIF

---

## 2. Metodologia

### 2.1 Disegno Sperimentale

Sono stati progettati 35 casi di test avversari distribuiti in 5 categorie:

| Categoria | Test | Scopo |
|-----------|-------|-----------|
| `edge_case` | 9 | Condizioni limite (nomi lunghi, formati varianti) |
| `adversarial` | 8 | Casi progettati per confondere (negazioni, esempi) |
| `ocr_corruption` | 5 | Simulazione errori OCR |
| `unicode_evasion` | 3 | Tentativi di evasione con caratteri simili |
| `real_world` | 10 | Estratti da documenti legali reali |

### 2.2 Livelli di Difficoltà

| Livello | Criterio di Successo | Test |
|-------|-------------------|-------|
| `easy` | Rilevare tutte le entità attese | 4 |
| `medium` | Rilevare tutte le entità attese | 12 |
| `hard` | Rilevare tutte le entità E zero falsi positivi | 19 |

### 2.3 Metriche Utilizzate

1. **F1 livello entità** (stile seqeval): Precisione, Richiamo, F1 calcolati a livello di entità completa, non token.

2. **Punteggio Sovrapposizione**: Rapporto caratteri corrispondenti tra entità attesa e rilevata (Jaccard su caratteri).

3. **Degradazione da Rumore** (stile NoiseBench): Differenza di F1 tra categorie "pulite" (`edge_case`, `adversarial`, `real_world`) e "rumorose" (`ocr_corruption`, `unicode_evasion`).

### 2.4 Ambiente di Esecuzione

| Componente | Specifica |
|------------|----------------|
| Hardware | CUDA (GPU) |
| Modello | `legal_ner_v2` (RoBERTalex) |
| Framework | PyTorch 2.0+, Transformers |
| Tempo caricamento | 1.6s |
| Tempo valutazione | 1.5s (35 test) |

### 2.5 Riproducibilità

```bash
cd ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

Lo script genera automaticamente un report in `docs/reports/`.

---

## 3. Risultati

### 3.1 Metriche Aggregate

| Metrica | Valore |
|---------|-------|
| Veri Positivi | 49 |
| Falsi Positivi | 9 |
| Falsi Negativi | 18 |
| **Precisione** | 0.845 |
| **Richiamo** | 0.731 |
| **F1-Score** | 0.784 |
| Punteggio Sovrapposizione Medio | 0.935 |

### 3.2 Risultati per Categoria

| Categoria | Tasso Superamento | TP | FP | FN | F1 |
|-----------|-----------|----|----|----|----|
| adversarial | 75.0% | 5 | 2 | 0 | 0.833 |
| edge_case | 66.7% | 9 | 1 | 3 | 0.818 |
| ocr_corruption | 40.0% | 5 | 0 | 4 | 0.714 |
| real_world | 40.0% | 26 | 5 | 9 | 0.788 |
| unicode_evasion | 33.3% | 4 | 1 | 2 | 0.727 |

### 3.3 Risultati per Difficoltà

| Difficoltà | Superati | Totale | Tasso |
|------------|---------|-------|------|
| easy | 3 | 4 | 75.0% |
| medium | 9 | 12 | 75.0% |
| hard | 7 | 19 | 36.8% |

### 3.4 Analisi Resistenza al Rumore

| Metrica | Valore | Riferimento |
|---------|-------|------------|
| F1 (testo pulito) | 0.800 | - |
| F1 (con rumore) | 0.720 | - |
| **Degradazione** | 0.080 | ≤0.10 (HAL Science) |
| Stato | **OK** | Entro la soglia |

---

## 4. Analisi Errori

### 4.1 Tassonomia dei Fallimenti

Sono stati identificati 5 pattern di fallimento ricorrenti:

#### Pattern 1: Date in Formato Testuale Spagnolo

| Test | Entità Mancata |
|------|-----------------|
| `date_roman_numerals` | "XV de marzo del año MMXXIV" |
| `notarial_header` | "quince de marzo de dos mil veinticuatro" |
| `judicial_sentence_header` | "diez de enero de dos mil veinticuatro" |

**Causa radice:** Il modello è stato addestrato principalmente con date in formato numerico (GG/MM/AAAA). Le date scritte in stile notarile spagnolo non sono rappresentate nel corpus di addestramento.

**Impatto:** Alto in documenti notarili e giudiziari dove questo formato è standard.

#### Pattern 2: Corruzione OCR Estrema

| Test | Entità Mancata |
|------|-----------------|
| `ocr_extra_spaces` | "1 2 3 4 5 6 7 8 Z", "M a r í a" |
| `ocr_missing_spaces` | "12345678X" (in testo concatenato) |
| `ocr_zero_o_confusion` | "ES91 21O0 0418 45O2 OOO5 1332" |

**Causa radice:** Il tokenizzatore di RoBERTa non gestisce bene testo con spaziatura anomala. La confusione O/0 rompe pattern regex IBAN.

**Impatto:** Medio. Documenti scansionati di bassa qualità.

#### Pattern 3: Evasione Unicode

| Test | Entità Mancata |
|------|-----------------|
| `fullwidth_numbers` | "１２３４５６７８Z" (U+FF11-U+FF18) |

**Causa radice:** Nessuna normalizzazione Unicode prima del NER. Le cifre fullwidth (U+FF10-U+FF19) non sono riconosciute come numeri.

**Impatto:** Basso in produzione, ma critico per sicurezza (evasione intenzionale).

#### Pattern 4: Identificatori Specifici Spagnoli

| Test | Entità Mancata |
|------|-----------------|
| `social_security` | "281234567890" (NSS) |
| `bank_account_clause` | "A-98765432" (CIF) |
| `professional_ids` | "12345", "67890" (numeri collegiali) |

**Causa radice:** Pattern poco frequenti nel corpus di addestramento. L'NSS spagnolo ha un formato specifico (12 cifre) che non è stato appreso.

**Impatto:** Alto per documenti lavorativi e commerciali.

#### Pattern 5: Falsi Positivi Contestuali

| Test | Entità Falsa |
|------|---------------|
| `example_dni` | "12345678X" (contesto: "esempio illustrativo") |
| `fictional_person` | "Don Quijote de la Mancha" |

**Causa radice:** Il modello rileva pattern senza considerare il contesto semantico (negazioni, esempi, finzione).

**Impatto:** Medio. Causa anonimizzazione non necessaria.

### 4.2 Matrice di Confusione per Tipo Entità

| Tipo | TP | FP | FN | Osservazione |
|------|----|----|----|----|
| PERSON | 15 | 2 | 2 | Buono, fallisce su finzione |
| DNI_NIE | 8 | 1 | 4 | Fallisce su formati varianti |
| LOCATION | 6 | 0 | 2 | Fallisce su CAP isolati |
| DATE | 3 | 0 | 4 | Fallisce su formato testuale |
| IBAN | 2 | 0 | 1 | Fallisce con OCR |
| ORGANIZATION | 5 | 2 | 0 | Confonde con tribunali |
| NSS | 0 | 0 | 1 | Non rileva |
| PROFESSIONAL_ID | 0 | 0 | 2 | Non rileva |
| Altri | 10 | 4 | 2 | - |

---

## 5. Conclusioni

### 5.1 Stato Attuale

Il modello `legal_ner_v2` presenta un **F1 di 0.784** in valutazione avversaria, con le seguenti caratteristiche:

- **Punti di Forza:**
  - Alta precisione (0.845) - pochi falsi positivi
  - Buona resistenza al rumore (degradazione 0.080)
  - Eccellente su nomi composti e indirizzi

- **Debolezze:**
  - Richiamo insufficiente (0.731) - perde entità
  - Non riconosce date in formato testuale spagnolo
  - Vulnerabile a evasione Unicode (fullwidth)
  - Non rileva NSS né numeri collegiali

### 5.2 Livello Validazione

| Livello | Stato | Criterio |
|-------|--------|----------|
| Livello 1: Unit Test | ✅ | Funzioni individuali |
| Livello 2: Integrazione | ✅ | Pipeline completa |
| Livello 3: Benchmark | ✅ | F1 > 0.75 |
| **Livello 4: Avversario** | ❌ | Tasso superamento < 70% |
| Livello 5: Simile a Prod | ⏸️ | In sospeso |

**Conclusione:** Il modello **NON è pronto per la produzione** secondo criteri del progetto (Livello 4 obbligatorio).

### 5.3 Lavoro Futuro

#### Priorità ALTA (impatto stimato > 3pts F1)

1. **Normalizzazione Unicode in pre-elaborazione**
   - Convertire fullwidth a ASCII
   - Rimuovere caratteri larghezza zero
   - Normalizzare O/0 in contesti numerici

2. **Aumento dati testuali**
   - Generare varianti: "primero de enero", "XV de marzo"
   - Includere numeri romani
   - Fine-tune con corpus aumentato

3. **Pattern regex per NSS/CIF**
   - Aggiungere a CompositeNerAdapter
   - NSS: `\d{12}` in contesto "Seguridad Social"
   - CIF: `[A-Z]-?\d{8}` in contesto azienda

#### Priorità MEDIA (impatto stimato 1-3pts F1)

4. **Normalizzazione spazi OCR**
   - Rilevare e collassare spazi eccessivi
   - Ricostruire token frammentati

5. **Filtro post-processo per contesti "esempio"**
   - Rilevare frasi: "por esempio", "illustrativo", "formato"
   - Sopprimere entità in questi contesti

#### Priorità BASSA (casi limite)

6. **Gazzettino personaggi fittizi**
   - Don Quijote, Sancho Panza, ecc.
   - Filtro post-processo

7. **Date con numeri romani**
   - Regex specifico per vecchio stile notarile

---

## 6. Riferimenti

1. **seqeval** - Metriche valutazione livello entità per etichettatura sequenza. https://github.com/chakki-works/seqeval

2. **NoiseBench (ICLR 2024)** - Benchmark per valutare modelli NLP sotto condizioni di rumore realistiche.

3. **HAL Science** - Studio su impatto OCR in task NER. Stabilisce degradazione attesa di ~10pti F1.

4. **RoBERTalex** - Modello RoBERTa dominio legale spagnolo. Base del modello valutato.

5. **Linee guida del progetto v1.0.0** - Metodologia di preparazione ML per ContextSafe.

---

## Appendici

### A. Configurazione Test

```yaml
total_tests: 35
categories:
  edge_case: 9
  adversarial: 8
  ocr_corruption: 5
  unicode_evasion: 3
  real_world: 10
difficulty_distribution:
  easy: 4
  medium: 12
  hard: 19
```

### B. Comando Riproduzione

```bash
cd /home/alexalves87/projects/generador\ LAIDA/outputs/test_backup/contextsafe_project/ml
source .venv/bin/activate
python scripts/evaluate/test_ner_predictor_adversarial.py
```

### C. File Generati

- Report automatico: `docs/reports/2026-01-23_adversarial_ner_v2.md`
- Analisi accademica: `docs/reports/2026-01-23_baseline_adversarial_analysis.md` (questo documento)

---

**Tempo esecuzione totale:** 3.1s (caricamento + valutazione)
**Generato da:** AlexAlves87
**Data:** 2026-01-23
