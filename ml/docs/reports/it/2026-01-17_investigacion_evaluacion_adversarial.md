# Ricerca: Migliori Pratiche per Valutazione Avversaria NER

**Data:** 2026-01-17
**Obiettivo:** Fondare la metodologia di valutazione avversaria prima di implementare gli script

---

## 1. Riepilogo Esecutivo

La letteratura accademica recente (2024-2025) stabilisce che la valutazione avversaria dei modelli NER deve considerare:

1. **Rumore Reale vs Simulato** - Il rumore reale è significativamente più difficile di quello simulato.
2. **Valutazione a Livello di Entità** - Non a livello di token.
3. **Multiple Categorie di Perturbazione** - OCR, Unicode, contesto, formato.
4. **Metriche Standard** - seqeval con F1, Precisione, Richiamo per tipo di entità.

---

## 2. Fonti Consultate

### 2.1 NoiseBench (Maggio 2024)

**Fonte:** [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609)

**Scoperte Chiave:**
- Il rumore reale (errori umani, crowdsourcing, LLM) è **significativamente più difficile** del rumore simulato.
- I modelli state-of-the-art "sono molto al di sotto del loro limite superiore teoricamente raggiungibile".
- 6 tipi di rumore reale dovrebbero essere valutati: errori di esperti, errori di crowdsourcing, errori di annotazione automatica, errori LLM.

**Applicazione al nostro progetto:**
- I nostri test includono rumore OCR reale (confusione l/I, 0/O) ✓
- Dobbiamo aggiungere test con errori di annotazione automatica.

### 2.2 Context-Aware Adversarial Training for NER (MIT TACL)

**Fonte:** [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846)

**Scoperte Chiave:**
- I modelli NER mostrano "Name Regularity Bias" - dipendono troppo dal nome e non dal contesto.
- BERT fine-tuned supera significativamente LSTM-CRF nei test di bias.
- L'addestramento avversario con vettori di rumore apprendibili migliora la capacità contestuale.

**Applicazione al nostro progetto:**
- I nostri test `negation_dni`, `example_dni`, `fictional_person` valutano la capacità contestuale ✓
- Il modello v2 (addestrato con rumore) dovrebbe essere più robusto.

### 2.3 OCR Impact on NER (HAL Science)

**Fonte:** [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document)

**Scoperte Chiave:**
- Il rumore OCR causa una perdita di ~10 punti F1 (72% vs 82% su testo pulito).
- Dovrebbe essere valutato con "vari livelli e tipi di rumore OCR".
- Primo studio sistematico dell'impatto OCR su NER multilingue.

**Applicazione al nostro progetto:**
- I nostri test OCR (5 casi) sono insufficienti - la letteratura raccomanda più livelli.
- Obiettivo realistico: accettare ~10 punti di degradazione con OCR.

### 2.4 seqeval - Metriche Standard

**Fonte:** [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval)

**Scoperte Chiave:**
- Valutazione a livello di **entità**, non token.
- Metriche: Precisione, Richiamo, F1 per tipo e media macro/micro.
- Modalità strict vs lenient per la corrispondenza.

**Applicazione al nostro progetto:**
- Il nostro script usa matching fuzzy con tolleranza ±5 caratteri (adeguato).
- Dobbiamo riportare metriche per tipo di entità, non solo superato/fallito.

### 2.5 Enterprise Robustness Benchmark (2025)

**Fonte:** [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341)

**Scoperte Chiave:**
- Perturbazioni minori possono ridurre le prestazioni fino a **40 punti percentuali**.
- Si deve valutare: modifiche del testo, cambi di formato, input multilingue, variazioni posizionali.
- I modelli da 4B-120B parametri mostrano tutti vulnerabilità.

**Applicazione al nostro progetto:**
- I nostri test coprono modifiche del testo e formattazione ✓
- Dobbiamo considerare test multilingue (nomi stranieri).

---

## 3. Tassonomia dei Test Avversari (Letteratura)

| Categoria | Sottocategoria | Esempio | Nostra Copertura |
|-----------|----------------|---------|------------------|
| **Rumore Etichetta** | Errori esperti | Annotazione errata | ❌ N/A (inferenza) |
| | Crowdsourcing | Inconsistenze | ❌ N/A (inferenza) |
| | Errori LLM | Allucinazioni | ❌ N/A (inferenza) |
| **Rumore Input** | Corruzione OCR | l/I, 0/O, spazi | ✅ 5 test |
| | Evasione Unicode | Cirillico, fullwidth | ✅ 3 test |
| | Variazione formato | D.N.I. vs DNI | ✅ Incluso |
| **Contesto** | Negazione | "NON avere DNI" | ✅ 1 test |
| | Esempio/illustrativo | "esempio: 12345678X" | ✅ 1 test |
| | Finzionale | Don Chisciotte | ✅ 1 test |
| | Riferimenti legali | Legge 15/2022 | ✅ 1 test |
| **Casi Limite** | Entità lunghe | Nomi nobiliari | ✅ 1 test |
| | Entità corte | J. García | ✅ 1 test |
| | Entità spaziate | IBAN con spazi | ✅ 2 test |
| **Mondo Reale** | Pattern documenti | Notarile, giudiziario | ✅ 10 test |

---

## 4. Metriche Raccomandate

### 4.1 Metriche Primarie (seqeval)

| Metrica | Descrizione | Uso |
|---------|-------------|-----|
| **F1 Macro** | Media F1 per tipo entità | Metrica principale |
| **F1 Micro** | F1 globale (tutte entità) | Metrica secondaria |
| **Precisione** | TP / (TP + FP) | Valutare falsi positivi |
| **Richiamo** | TP / (TP + FN) | Valutare entità perse |

### 4.2 Metriche Avversarie

| Metrica | Descrizione | Obiettivo |
|---------|-------------|----------|
| **Tasso Superamento** | Test superati / Totale | ≥70% |
| **Degradazione OCR** | F1_pulito - F1_ocr | ≤10 punti |
| **Sensibilità Contesto** | % test contestuali corretti | ≥80% |
| **Tasso FP** | Falsi positivi / Rilevamenti | ≤15% |

---

## 5. Gap Identificati nel Nostro Script

| Gap | Severità | Azione |
|-----|-----------|--------|
| Nessun report F1/Precisione/Richiamo per tipo | Media | Aggiungere metriche seqeval |
| Pochi test OCR (5) vs raccomandati (10+) | Media | Espandere nella prossima iterazione |
| Non valuta degradazione vs baseline | Alta | Confrontare con test puliti |
| Nessun test multilingue | Bassa | Aggiungere nomi stranieri |

---

## 6. Raccomandazioni per il Nostro Script

### 6.1 Miglioramenti Immediati

1. **Aggiungere metriche seqeval** - Precisione, Richiamo, F1 per tipo di entità.
2. **Calcolare degradazione** - Confrontare con versione pulita di ogni test.
3. **Riportare tasso FP** - Falsi positivi come metrica separata.

### 6.2 Miglioramenti Futuri

1. Espandere test OCR a 10+ casi con diversi livelli di corruzione.
2. Aggiungere test con nomi stranieri (John Smith, Mohammed Ali).
3. Implementare valutazione stile NoiseBench con rumore graduato.

---

## 7. Conclusione

Lo script attuale copre le categorie principali di valutazione avversaria secondo la letteratura, ma deve:

1. **Migliorare metriche** - Usare seqeval per F1/P/R per tipo.
2. **Espandere OCR** - Più livelli di corruzione.
3. **Calcolare degradazione** - vs baseline pulita.

**Lo script attuale è VALIDO per la valutazione iniziale**, ma deve essere iterato per conformarsi completamente alle migliori pratiche accademiche.

---

## Riferimenti

1. [NoiseBench: Benchmarking the Impact of Real Label Noise on NER](https://arxiv.org/abs/2405.07609) - ICLR 2024
2. [Context-aware Adversarial Training for Name Regularity Bias](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00386/102846) - MIT TACL
3. [Assessing and Minimizing the Impact of OCR Quality on NER](https://hal.science/hal-03026931/document) - HAL Science
4. [seqeval - Sequence Labeling Evaluation](https://github.com/chakki-works/seqeval) - GitHub
5. [Evaluating Robustness of LLMs in Enterprise Applications](https://arxiv.org/html/2601.06341) - arXiv 2025
6. [nervaluate - Entity-level NER Evaluation](https://github.com/MantisAI/nervaluate) - Based on SemEval'13

---

**Autor:** AlexAlves87
**Data:** 2026-01-17
