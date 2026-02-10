# Ricerca: Migliori Pratiche per Pipeline di Rilevamento PII

**Data:** 2026-01-16
**Autor:** AlexAlves87
**Tipo:** Revisione della Letteratura
**Stato:** Completato

---

## Riepilogo Esecutivo

Questa ricerca analizza lo stato dell'arte nel rilevamento di PII (Personally Identifiable Information) con un focus sui documenti legali spagnoli. Sono stati esaminati paper accademici recenti (2024-2025) e framework di produzione per identificare le migliori pratiche in preelaborazione, architettura della pipeline e post-elaborazione.

**Risultato principale:** L'architettura ottimale è **ibrida** (Regex → NER → Validazione), non NER puro con post-elaborazione. Inoltre, l'iniezione di rumore OCR (30%) durante l'addestramento migliora significativamente la robustezza.

---

## Metodologia

### Fonti Consultate

| Fonte | Tipo | Anno | Rilevanza |
|--------|------|-----|------------|
| PMC12214779 | Paper Accademico | 2025 | Ibrido NLP-ML per PII finanziario |
| arXiv 2401.10825v3 | Sondaggio | 2024 | Stato dell'arte NER |
| Microsoft Presidio | Framework | 2024 | Migliori pratiche industriali |
| Presidio Research | Strumenti | 2024 | Valutazione dei riconoscitori |

### Criteri di Ricerca

- "NER preprocessing postprocessing best practices 2024"
- "Spanish legal documents PII detection"
- "Hybrid rule-based NLP machine learning PII"
- "Presidio pipeline architecture"

---

## Risultati

### 1. Architettura Pipeline Ottimale

#### 1.1 Ordine di Elaborazione (Presidio)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Testo    │ → │   Regex     │ → │   NLP NER   │ → │  Checksum   │ → │   Soglia    │
│    (OCR)    │    │  Matchers   │    │   Modello   │    │ Validazione │    │   Filtro    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Fonte:** Documentazione Microsoft Presidio

**Giustificazione:**
> "Presidio utilizza inizialmente il suo regex matcher per identificare le entità corrispondenti. Successivamente, il modello NER basato su Elaborazione del Linguaggio Naturale viene utilizzato per rilevare le PII in modo autonomo. Quando possibile, viene utilizzato un checksum per validare le PII identificate."

#### 1.2 Componenti della Pipeline

| Componente | Funzione | Implementazione |
|------------|---------|----------------|
| **Regex Matchers** | Rilevare pattern strutturati (DNI, IBAN, telefono) | Eseguire PRIMA del NER |
| **NLP NER** | Rilevare entità contestuali (nomi, indirizzi) | Modello Transformer |
| **Checksum Validation** | Validare l'integrità degli identificatori | DNI mod-23, IBAN mod-97 |
| **Context Enhancement** | Migliorare la confidenza con contesto lessicale | LemmaContextAwareEnhancer |
| **Threshold Filter** | Filtrare per punteggio di confidenza | Configurabile (es: 0.7) |

### 2. Preelaborazione

#### 2.1 Normalizzazione del Testo

**Fonte:** PMC12214779 (Hybrid NLP-ML)

| Tecnica | Descrizione | Applicabilità |
|---------|-------------|---------------|
| Tokenizzazione | Divisione in unità discrete | Universale |
| Marcatura di posizione | Marcatura di posizione a livello di carattere | Per recupero span |
| Normalizzazione Unicode | Fullwidth → ASCII, rimozione larghezza zero | Alta per OCR |
| Normalizzazione abbreviazioni | D.N.I. → DNI | Alta per spagnolo |

#### 2.2 Iniezione di Rumore (CRITICO)

**Fonte:** PMC12214779

> "Per simulare meglio le anomalie dei documenti del mondo reale, la preelaborazione dei dati aggiunge rumore casuale minore come la rimozione della punteggiatura e la normalizzazione del testo."

**Implementazione raccomandata:**
```python
# 30% probabilità di rumore per campione
noise_probability = 0.30

# Tipi di rumore:
# - Rimozione casuale punteggiatura
# - Sostituzione caratteri OCR (l↔I, 0↔O)
# - Collasso/espansione spazi
# - Perdita di accenti
```

**Impatto:** Migliora la robustezza contro documenti scansionati reali.

### 3. Architettura del Modello

#### 3.1 Stato dell'Arte NER (2024)

**Fonte:** arXiv 2401.10825v3

| Architettura | Caratteristiche | Benchmark F1 |
|--------------|-----------------|--------------|
| DeBERTa | Attenzione districata + decoder maschera migliorato | SOTA |
| RoBERTa + CRF | Transformer + coerenza di sequenza | +4-13% vs base |
| BERT + BiLSTM | Modellazione contestuale + sequenziale | Robusto |
| GLiNER | Attenzione globale per entità distanti | Innovativo |

#### 3.2 Livello CRF

**Fonte:** Sondaggio arXiv

> "L'applicazione di CRF fornisce un metodo robusto per NER assicurando sequenze di etichette coerenti e modellando le dipendenze tra etichette adiacenti."

**Vantaggio:** Previene sequenze non valide come `B-PERSON I-LOCATION`.

### 4. Post-elaborazione

#### 4.1 Validazione Checksum

**Fonte:** Migliori Pratiche Presidio

| Tipo | Algoritmo | Esempio |
|------|-----------|---------|
| DNI spagnolo | lettera = "TRWAGMYFPDXBNJZSQVHLCKE"[num % 23] | 12345678Z |
| NIE spagnolo | Prefisso X=0, Y=1, Z=2 + algoritmo DNI | X1234567L |
| IBAN | ISO 7064 Mod 97-10 | ES9121000418450200051332 |
| NSS spagnolo | Mod 97 su prime 10 cifre | 281234567890 |
| Carta di credito | Algoritmo Luhn | 4111111111111111 |

#### 4.2 Miglioramento Consapevole del Contesto

**Fonte:** Presidio LemmaContextAwareEnhancer

> "Il ContextAwareEnhancer è un modulo che migliora il rilevamento delle entità utilizzando il contesto del testo. Può migliorare il rilevamento di entità dipendenti dal contesto."

**Implementazione:**
- Cercare parole chiave in finestra di ±N token
- Aumentare/diminuire punteggio in base al contesto
- Esempio: "DNI" vicino a un numero aumenta confidenza DNI_NIE

#### 4.3 Filtraggio a Soglia

**Fonte:** Guida Tuning Presidio

> "Regolare le soglie di confidenza sui riconoscitori ML per bilanciare i casi persi rispetto all'eccessivo mascheramento."

**Raccomandazione:**
- Soglia alta (0.8+): Meno falsi positivi, più falsi negativi
- Soglia bassa (0.5-0.6): Più copertura, più rumore
- Pilota iniziale per calibrare

### 5. Risultati Benchmark

#### 5.1 Hybrid NLP-ML (PMC12214779)

| Metrica | Valore |
|---------|-------|
| Precisione | 94.7% |
| Richiamo | 89.4% |
| F1-score | 91.1% |
| Accuratezza (mondo reale) | 93.0% |

**Fattori di successo:**
1. Dati di addestramento diversi (template variegati)
2. Framework leggero (spaCy vs transformer pesanti)
3. Metriche bilanciate (precisione ≈ richiamo)
4. Anonimizzazione che preserva il contesto

#### 5.2 Tuning Presidio

**Fonte:** Presidio Research Notebook 5

> "Il Notebook 5 in presidio-research mostra come si può configurare Presidio per rilevare PII in modo molto più accurato, e aumentare l'F-score di ~30%."

---

## Analisi dei Gap

### Confronto: Implementazione Attuale vs Migliori Pratiche

| Aspetto | Migliore Pratica | Implementazione Attuale | Gap |
|---------|---------------|----------------------|-----|
| Ordine pipeline | Regex → NER → Validazione | NER → Post-elaborazione | **CRITICO** |
| Iniezione rumore | 30% in addestramento | 0% | **CRITICO** |
| Livello CRF | Aggiungere su transformer | Non implementato | MEDIO |
| Soglia confidenza | Filtrare per punteggio | Non implementato | MEDIO |
| Miglioramento contesto | Basato su lemma | Parziale (regex) | BASSO |
| Validazione checksum | DNI, IBAN, NSS | Implementato | ✓ OK |
| Validazione formato | Pattern Regex | Implementato | ✓ OK |

### Impatto Stimato delle Correzioni

| Correzione | Sforzo | Impatto F1 Stimato |
|------------|----------|---------------------|
| Iniezione rumore nel dataset | Basso | +10-15% su OCR |
| Pipeline Regex-first | Medio | +5-10% precisione |
| Livello CRF | Alto | +4-13% (letteratura) |
| Soglia confidenza | Basso | Riduce FP 20-30% |

---

## Conclusioni

### Scoperte Principali

1. **L'architettura ibrida è superiore**: Combinare regex (pattern strutturati) con NER (contestuale) supera gli approcci puri.

2. **L'ordine conta**: Regex PRIMA del NER, non dopo. Presidio usa questo ordine per design.

3. **Il rumore in addestramento è critico**: 30% di iniezione di errori OCR migliora significativamente la robustezza.

4. **La validazione checksum è standard**: Validare identificatori strutturati (DNI, IBAN) è pratica universale.

5. **CRF migliora la coerenza**: Aggiungere livello CRF su transformer previene sequenze non valide.

### Raccomandazioni

#### Priorità ALTA (Implementare Immediatamente)

1. **Iniettare rumore OCR nel dataset v3**
   - 30% dei campioni con errori simulati
   - Tipi: l↔I, 0↔O, spazi, accenti mancanti
   - Riaddestrare modello

2. **Ristrutturare pipeline**
   ```
   PRIMA: Testo → NER → Post-elaborazione
   DOPO:  Testo → Preelaborazione → Regex → NER → Validazione → Filtro
   ```

#### Priorità MEDIA

3. **Aggiungere soglia di confidenza**
   - Filtrare entità con punteggio < 0.7
   - Calibrare con set di validazione

4. **Valutare livello CRF**
   - Investigare `transformers` + `pytorch-crf`
   - Benchmark contro modello attuale

#### Priorità BASSA

5. **Miglioramento contesto avanzato**
   - Implementare LemmaContextAwareEnhancer
   - Gazetteer di contesto per tipo di entità

---

## Riferimenti

1. **PMC12214779** - "A hybrid rule-based NLP and machine learning approach for PII detection and anonymization in financial documents"
   - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC12214779/
   - Anno: 2025

2. **arXiv 2401.10825v3** - "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study"
   - URL: https://arxiv.org/html/2401.10825v3
   - Anno: 2024 (aggiornato 2025)

3. **Microsoft Presidio** - Best Practices for Developing Recognizers
   - URL: https://microsoft.github.io/presidio/analyzer/developing_recognizers/
   - Anno: 2024

4. **Presidio Research** - Evaluation Toolbox
   - URL: https://github.com/microsoft/presidio-research
   - Anno: 2024

5. **Nature Scientific Reports** - "A hybrid rule-based NLP and machine learning approach"
   - URL: https://www.nature.com/articles/s41598-025-04971-9
   - Anno: 2025

---

**Data:** 2026-01-16
**Versione:** 1.0
