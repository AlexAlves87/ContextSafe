# Ricerca: Lacune del Pipeline Ibrido NER-PII

**Data:** 30-01-2026
**Autor:** AlexAlves87
**Obiettivo:** Analizzare le lacune critiche nel pipeline ibrido basandosi sulla letteratura accademica 2024-2026
**Versione:** 2.0.0 (riscritta con fondamenti accademici)

---

## 1. Riepilogo Esecutivo

Sono state identificate cinque lacune nel pipeline ibrido NER-PII di ContextSafe. Per ogni lacuna è stata condotta una revisione della letteratura accademica in fonti di primo livello (ACL, EMNLP, COLING, NAACL, TACL, Nature Scientific Reports, Springer, arXiv). Le raccomandazioni proposte si basano su prove pubblicate, non sull'intuizione.

| Lacuna | Priorità | Paper Revisionati | Raccomandazione Principale |
|--------|----------|-------------------|----------------------------|
| Strategia di Unione | **ALTA** | 7 | Pipeline a 3 fasi (RECAP) + priorità per tipo |
| Calibrazione Confidenza | **ALTA** | 5 | Previsione Conforme + BRB per regex |
| Benchmark Comparativo | **MEDIA** | 3 | nervaluate (SemEval'13) con corrispondenza parziale |
| Latenza/Memoria | **MEDIA** | 4 | ONNX Runtime + Quantizzazione INT8 |
| Gazzettieri | **BASSA** | 5 | Integrazione stile GAIN come post-filtro |

---

## 2. Letteratura Revisionata

| Paper/Sistema | Sede/Fonte | Anno | Scoperta Rilevante |
|---------------|------------|------|--------------------|
| RECAP: Hybrid PII Detection | arXiv 2510.07551 | 2025 | Pipeline a 3 fasi: rilevamento → disambiguazione multi-label → consolidamento span |
| Hybrid rule-based NLP + ML for PII (Mishra et al.) | Nature Scientific Reports | 2025 | F1 0.911 su doc finanziari, unione sovrapposizioni con min(start)/max(end) |
| Conformal Prediction for NER | arXiv 2601.16999 | 2026 | Insiemi di previsione con garanzie di copertura ≥95%, calibrazione stratificata |
| JCLB: Contrastive Learning + BRB | Springer Cybersecurity | 2024 | Belief Rule Base assegna confidenza appresa a regex, D-CMA-ES ottimizza parametri |
| CMiNER | Expert Systems with Applications | 2025 | Stimatori di confidenza a livello di entità per dati rumorosi |
| B2NER | COLING 2025 | 2025 | Benchmark NER unificato, 54 dataset, adattatori LoRA ≤50MB, supera GPT-4 |
| nervaluate (SemEval'13 Task 9) | GitHub/MantisAI | 2024 | Metriche COR/INC/PAR/MIS/SPU con corrispondenza parziale |
| T2-NER | TACL | 2023 | Framework a 2 stadi basato su span per entità sovrapposte e discontinue |
| GNNer | ACL SRW 2022 | 2022 | Graph Neural Networks per ridurre span sovrapposti |
| GAIN: Gazetteer-Adapted Integration | SemEval-2022 | 2022 | Divergenza KL per adattare rete gazzettiere al language model, 1º in 3 track |
| Presidio | Microsoft Open Source | 2025 | `_remove_duplicates`: confidenza più alta vince, contenimento → span più grande |
| Soft Gazetteers | ACL 2020 | 2020 | Entity linking interlinguistico per gazzettieri in risorse limitate |
| SPLR (span-based nested NER) | J. Supercomputing | 2025 | F1 87.5 su ACE2005 con Funzione di Conoscenza Precedente |
| HuggingFace Optimum + ONNX | MarkTechPost/HuggingFace | 2025 | Benchmark PyTorch vs ONNX Runtime vs INT8 quantizzato |
| PyDeID | PHI De-identification | 2025 | regex + spaCy NER, F1 87.9% su note cliniche, 0.48s/nota |

---

## 3. Lacuna 1: Strategia di Unione (ALTA)

### 3.1 Problema

Quando il transformer NER e Regex rilevano la stessa entità con limiti o tipi diversi, quale preferire?

```
Testo: "Don José García con DNI 12 345 678 Z"

NER rileva:   "José García con DNI 12 345 678" (PERSON esteso, parziale)
Regex rileva: "12 345 678 Z" (DNI_NIE, completo)
```

### 3.2 Stato dell'Arte

#### 3.2.1 Framework RECAP (arXiv 2510.07551, 2025)

Il framework più recente e completo per l'unione PII ibrida implementa **tre fasi**:

1.  **Fase I - Rilevamento base:** Regex per PII strutturate (ID, telefoni) + LLM per non strutturate (nomi, indirizzi). Produce multi-label, sovrapposizioni e falsi positivi.

2.  **Fase II - Disambiguazione Multi-label:** Per entità con etichette multiple, testo, span e etichette candidate passano a un LLM con prompt contestuale che seleziona l'etichetta corretta.

3.  **Fase III - Consolidamento:** Due filtri:
    *   **Risoluzione deterministica sovrapposizioni:** Entità a priorità inferiore completamente contenute in span più lunghi vengono rimosse.
    *   **Filtraggio contestuale falsi positivi:** Sequenze numeriche brevi verificate con contesto della frase circostante.

**Risultato:** F1 medio 0.657 su 13 localizzazioni, superando NER puro (0.360) dell'82% e zero-shot LLM (0.558) del 17%.

#### 3.2.2 Microsoft Presidio (2025)

Presidio implementa `__remove_duplicates()` con regole semplici:
*   **Punteggio di confidenza più alto vince** tra rilevamenti sovrapposti
*   **Contenimento:** Se una PII è contenuta in un'altra, si usa quella col **testo più lungo**
*   **Intersezione parziale:** Entrambe restituite concatenate
*   Nessuna priorità per tipo, solo per punteggio

#### 3.2.3 Mishra et al. (Nature Scientific Reports, 2025)

Per documenti finanziari, unione sovrapposizioni:
*   `start = min(start1, start2)`
*   `end = max(end1, end2)`
*   La sovrapposizione viene fusa in una singola entità consolidata

**Limitazione:** Non distingue i tipi — inutile quando NER rileva PERSON e Regex rileva DNI nello stesso span.

#### 3.2.4 T2-NER (TACL, 2023)

Framework a 2 stadi basato su span:
1.  Estrarre tutti gli span di entità (sovrapposti e piatti)
2.  Classificare coppie di span per risolvere discontinuità

**Intuizione applicabile:** Separare il rilevamento degli span dalla loro classificazione consente di gestire le sovrapposizioni in modo modulare.

#### 3.2.5 GNNer (ACL Student Research Workshop, 2022)

Usa Graph Neural Networks per ridurre span sovrapposti in NER basato su span. Gli span candidati sono nodi in un grafo, e la GNN impara a rimuovere quelli sovrapposti.

**Intuizione applicabile:** La sovrapposizione non è sempre un errore — le entità annidate (nome dentro indirizzo) sono legittime.

### 3.3 Implementazione Attuale di ContextSafe

File: `scripts/inference/ner_predictor.py`, metodo `_merge_regex_detections()`

```python
# Strategia attuale (righe 430-443):
for ner_ent in ner_entities:
    replaced = False
    for match in regex_matches:
        if overlaps(match, ner_ent):
            if regex_len > ner_len * 1.2:  # Regex 20% più lungo
                replaced = True
                break
    if not replaced:
        ner_to_keep.append(ner_ent)
```

**Regola attuale:** Se regex è ≥20% più lungo di NER e c'è sovrapposizione → preferire regex.

### 3.4 Analisi Comparativa

| Sistema | Strategia | Gestisce Annidato | Usa Tipo | Usa Confidenza |
|---------|-----------|-------------------|----------|----------------|
| RECAP | 3 fasi + LLM | ✅ | ✅ | Implicito |
| Presidio | Punteggio più alto | ❌ | ❌ | ✅ |
| Mishra et al. | unione min/max | ❌ | ❌ | ❌ |
| ContextSafe attuale | Regex più lungo vince | ❌ | ❌ | ❌ |
| **Proposto** | **Priorità tipo + validazione** | **✅** | **✅** | **✅** |

### 3.5 Raccomandazione Basata su Prove

Ispirato da RECAP (3 fasi) ma senza dipendere da LLM (il nostro requisito è inferenza CPU senza LLM), proponiamo:

**Fase 1: Rilevamento Indipendente**
*   Transformer NER rileva entità semantiche (PERSON, ORGANIZATION, LOCATION)
*   Regex rileva entità strutturali (DNI, IBAN, PHONE, DATE)

**Fase 2: Risoluzione Sovrapposizioni per Priorità di Tipo**

Basato su prove RECAP (regex eccelle in PII strutturate, NER in semantiche):

```python
MERGE_PRIORITY = {
    # Tipo → (priorità, fonte_preferita)
    # Regex con checksum = massima confidenza (prova: Mishra et al. 2025)
    "DNI_NIE": (10, "regex"),      # Checksum verificabile
    "IBAN": (10, "regex"),         # Checksum verificabile
    "NSS": (10, "regex"),          # Checksum verificabile
    "PHONE": (8, "regex"),         # Formato ben definito
    "POSTAL_CODE": (8, "regex"),   # 5 cifre esatte
    "LICENSE_PLATE": (8, "regex"), # Formato ben definito
    # NER eccelle in entità semantiche (RECAP, PyDeID)
    "DATE": (6, "any"),            # Entrambi validi
    "PERSON": (4, "ner"),          # NER meglio con contesto
    "ORGANIZATION": (4, "ner"),    # NER meglio con contesto
    "LOCATION": (4, "ner"),        # NER meglio con contesto
    "ADDRESS": (4, "ner"),         # NER meglio con contesto
}
```

**Fase 3: Consolidamento**
*   Entità **contenute** di tipi diversi: mantenere entrambe (annidato legittimo, come in GNNer)
*   Entità **contenute** dello stesso tipo: preferire la più specifica (fonte preferita)
*   Sovrapposizione **parziale**: preferire tipo a priorità più alta
*   Nessuna sovrapposizione: mantenere entrambe

| Situazione | Regola | Prova |
|------------|--------|-------|
| Nessuna sovrapposizione | Mantenere entrambe | Standard |
| Sovrapposizione, tipi div. | Priorità più alta vince | RECAP Fase III |
| Contenimento, tipi div. | Mantenere entrambe (annidato) | GNNer, T2-NER |
| Contenimento, stesso tipo | Fonte preferita per tabella | Presidio (span più grande) |
| Sovrapposizione parziale, stesso tipo | Confidenza più alta vince | Presidio |

---

## 4. Lacuna 2: Calibrazione Confidenza (ALTA)

### 4.1 Problema

Regex restituisce confidenza fissa (0.95), NER restituisce probabilità softmax. Non sono direttamente confrontabili.

### 4.2 Stato dell'Arte

#### 4.2.1 Previsione Conforme per NER (arXiv 2601.16999, Gennaio 2026)

**Paper più recente e rilevante.** Introduce framework per produrre **insiemi di previsione** con garanzie di copertura:

*   Dato livello di confidenza `1-α`, genera insiemi di previsione garantiti per contenere l'etichetta corretta
*   Usa **punteggi di non conformità**:
    *   `nc1`: `1 - P̂(y|x)` — basato su probabilità, penalizza bassa confidenza
    *   `nc2`: probabilità cumulativa in sequenze classificate
    *   `nc3`: basato sul rango, produce insiemi di dimensione fissa

**Scoperte Chiave:**
*   `nc1` supera sostanzialmente `nc2` (che produce insiemi "estremamente grandi")
*   **Calibrazione stratificata per lunghezza** corregge miscalibrazione sistematica in sequenze lunghe
*   **Calibrazione per lingua** migliora copertura (Inglese: 93.82% → 96.24% dopo stratificazione)
*   Correzione di Šidák per entità multiple: confidenza per entità = `(1-α)^(1/s)` per `s` entità

**Applicabilità a ContextSafe:** La calibrazione stratificata per lunghezza è direttamente applicabile. Testi lunghi (contratti) possono avere punteggi sistematicamente diversi da testi brevi.

#### 4.2.2 JCLB: Belief Rule Base (Springer Cybersecurity, 2024)

Introduce un approccio per **assegnare confidenza a regole regex** in modo appreso:

*   Le regole regex sono formalizzate come una **Belief Rule Base (BRB)**
*   Ogni regola ha **gradi di credenza** ottimizzati da D-CMA-ES
*   La BRB filtra categorie di entità e valuta la loro correttezza simultaneamente
*   I parametri BRB sono ottimizzati contro dati di addestramento

**Intuizione chiave:** Le regole regex NON dovrebbero avere confidenza fissa. La loro confidenza deve essere appresa/calibrata contro dati reali.

#### 4.2.3 CMiNER (Expert Systems with Applications, 2025)

Progetta **stimatori di confidenza a livello di entità** che:
*   Valutano qualità iniziale di dataset rumorosi
*   Assistono durante l'addestramento regolando pesi

**Intuizione applicabile:** La confidenza a livello di entità (non token) è più utile per decisioni di unione.

#### 4.2.4 Conf-MPU (Zhou et al., 2022)

Classificazione binaria a livello token per prevedere probabilità che ogni token sia un'entità, poi usa punteggi di confidenza per stima del rischio.

**Intuizione applicabile:** Separare "è questa un'entità?" da "che tipo?" consente di calibrare in due fasi.

### 4.3 Implementazione Attuale di ContextSafe

```python
# Regex patterns (spanish_id_patterns.py):
RegexMatch(..., confidence=0.95)  # Valore fisso hardcoded

# Modello NER:
confidence = softmax(logits).max()  # Probabilità reale [0.5-0.99]

# Aggiustamento checksum (ner_predictor.py, righe 473-485):
if is_valid:
    final_confidence = min(match.confidence * 1.1, 0.99)
elif checksum_conf < 0.5:
    final_confidence = match.confidence * 0.5
```

### 4.4 Analisi del Problema

| Fonte | Confidenza | Calibrata | Problema |
|-------|------------|-----------|----------|
| NER softmax | 0.50-0.99 | ✅ | Può essere miscalibrata per testi lunghi (CP 2026) |
| Regex senza checksum | 0.95 fissa | ❌ | Sovraconfidenza in match ambigui |
| Regex con checksum valido | 0.99 | ⚠️ | Appropriata per ID con checksum |
| Regex con checksum invalido | 0.475 | ✅ | Penalità appropriata |

### 4.5 Raccomandazione Basata su Prove

#### Livello 1: Confidenza base differenziata per tipo (ispirato da JCLB/BRB)

Non usare confidenza fissa. Assegnare **confidenza base** secondo il livello di validazione disponibile:

```python
REGEX_BASE_CONFIDENCE = {
    # Con checksum verificabile (massima confidenza, Mishra et al. 2025)
    "DNI_NIE":  {"checksum_valid": 0.98, "checksum_invalid": 0.35, "format_only": 0.70},
    "IBAN":     {"checksum_valid": 0.99, "checksum_invalid": 0.30, "format_only": 0.65},
    "NSS":      {"checksum_valid": 0.95, "checksum_invalid": 0.35, "format_only": 0.65},

    # Senza checksum, con formato ben definito
    "PHONE":         {"with_prefix": 0.90, "without_prefix": 0.75},
    "POSTAL_CODE":   {"valid_province": 0.85, "format_only": 0.70},
    "LICENSE_PLATE": {"modern_format": 0.90, "old_format": 0.80},

    # Ambiguo
    "DATE":  {"full_textual": 0.85, "partial": 0.60, "ambiguous": 0.50},
    "EMAIL": {"standard": 0.95},
}
```

**Giustificazione:** JCLB ha mostrato che la confidenza delle regole dovrebbe essere appresa/differenziata, non fissa. Senza accesso a dati di addestramento per ottimizzare BRB (come D-CMA-ES in JCLB), usiamo euristiche basate sul livello di validazione disponibile (checksum > formato > match semplice).

#### Livello 2: Calibrazione stratificata (ispirato da CP 2026)

Per Transformer NER, considerare calibrazione per lunghezza testo:
*   Testi brevi (1-10 token): soglia confidenza minima 0.60
*   Testi medi (11-50 token): soglia 0.50
*   Testi lunghi (51+ token): soglia 0.45

**Giustificazione:** Paper Previsione Conforme (2026) ha mostrato che testi lunghi hanno copertura sistematicamente diversa. Stratificare per lunghezza corregge questa miscalibrazione.

#### Livello 3: Soglia confidenza operativa

Basato su RECAP e PyDeID:
*   **≥0.80:** Anonimizzazione automatica
*   **0.50-0.79:** Anonimizzazione con flag "revisionare"
*   **<0.50:** Non anonimizzare, segnalare come "dubbio"

---

## 5. Lacuna 3: Benchmark Comparativo (MEDIA)

### 5.1 Stato dell'Arte in Valutazione NER

#### 5.1.1 Metriche: seqeval vs nervaluate

| Framework | Tipo | Match Parziale | Livello | Standard |
|-----------|------|----------------|---------|----------|
| **seqeval** | Strict entity-level | ❌ | Entità completa | CoNLL eval |
| **nervaluate** | Multi-scenario | ✅ | COR/INC/PAR/MIS/SPU | SemEval'13 Task 9 |

**seqeval** (standard CoNLL):
*   Precision, Recall, F1 a livello entità completa
*   Solo match esatto: tipo corretto E span completo
*   Media Micro/macro per tipo

**nervaluate** (SemEval'13 Task 9):
*   4 scenari: strict, exact, partial, type
*   5 categorie: COR (corretto), INC (tipo errato), PAR (span parziale), MIS (perso), SPU (spurio)
*   Corrispondenza parziale: `Precision = (COR + 0.5 × PAR) / ACT`

**Raccomandazione:** Usare **entrambe** le metriche. seqeval per comparabilità con letteratura (CoNLL), nervaluate per analisi errori più fine.

#### 5.1.2 Benchmark B2NER (COLING 2025)

*   54 dataset, 400+ tipi entità, 6 lingue
*   Benchmark unificato per Open NER
*   Adattatori LoRA ≤50MB superano GPT-4 di 6.8-12.0 F1

**Applicabilità:** B2NER conferma che LoRA è fattibile per NER specializzato, ma richiede dati di qualità (54 dataset raffinati).

### 5.2 Dati ContextSafe Disponibili

| Configurazione | F1 Strict | Tasso Passaggio | Fonte |
|----------------|-----------|-----------------|-------|
| Solo NER (legal_ner_v2 base) | 0.464 | 28.6% | Baseline |
| NER + Normalizzatore | 0.492 | 34.3% | Ciclo ML |
| NER + Regex | 0.543 | 45.7% | Ciclo ML |
| **Pipeline Completa (5 elem)** | **0.788** | **60.0%** | Ciclo ML |
| LoRA fine-tuning puro | 0.016 | 5.7% | Esp. 2026-02-04 |
| GLiNER zero-shot | 0.325 | 11.4% | Esp. 2026-02-04 |

### 5.3 Benchmark In Sospeso

| Test | Metrica | Stato |
|------|---------|-------|
| Valutare con nervaluate (match parziale) | COR/INC/PAR/MIS/SPU | In sospeso |
| Solo Regex (senza NER) | F1 strict + parziale | In sospeso |
| NER + Checksum (senza pattern regex) | F1 strict + parziale | In sospeso |
| Confronto scomposizione tipo entità | F1 per tipo | In sospeso |

### 5.4 Raccomandazione

Creare script `scripts/evaluate/benchmark_nervaluate.py` che:
1.  Esegua pipeline completa contro adversarial test set
2.  Riporti metriche seqeval (strict, per comparabilità)
3.  Riporti metriche nervaluate (4 scenari, per analisi errori)
4.  Suddivida per tipo di entità
5.  Confronti ablazioni (solo NER, solo Regex, Ibrido)

---

## 6. Lacuna 4: Latenza/Memoria (MEDIA)

### 6.1 Obiettivo

| Metrica | Obiettivo | Giustificazione |
|---------|-----------|-----------------|
| Latenza | <500ms par pagina A4 (~600 token) | UX reattiva |
| Memoria | <2GB modello in RAM | Deployment su 16GB |
| Throughput | >10 pagine/secondo (batch) | Elaborazione massiva |

### 6.2 Stato dell'Arte in Ottimizzazione Infernza

#### 6.2.1 ONNX Runtime + Quantizzazione (HuggingFace Optimum, 2025)

HuggingFace Optimum consente:
*   Export in ONNX
*   Ottimizzazione grafo (fusione operatori, eliminazione nodi ridondanti)
*   Quantizzazione INT8 (dinamica o statica)
*   Benchmarking integrato: PyTorch vs torch.compile vs ONNX vs ONNX quantizzato

**Risultati Riportati:**
*   Ottimizzato TensorRT: fino a 432 inferenze/secondo (ResNet-50, non NER)
*   ONNX Runtime: speedup tipico 2-4x su PyTorch vanilla su CPU

#### 6.2.2 PyDeID (2025)

Sistema ibrido regex + spaCy NER per de-identificazione:
*   **0.48 secondi/nota** vs 6.38 secondi/nota del sistema base
*   Fattore speedup 13x con regex ottimizzato + NER
*   F1 87.9% con il pipeline veloce

**Applicabilità diretta:** PyDeID dimostra che un pipeline ibrido regex+NER può processare 1 documento in <0.5s.

#### 6.2.3 Pipeline Ottimizzazione Transformer

```
PyTorch FP32 → Export ONNX → Ottimizzazione Grafo → Quantizzazione INT8
    baseline        2x              2-3x                 3-4x
```

### 6.3 Stima Teorica per ContextSafe

| Componente | CPU (PyTorch) | CPU (ONNX INT8) | Memoria |
|------------|---------------|-----------------|---------|
| TextNormalizer | <1ms | <1ms | ~0 |
| NER (RoBERTa-BNE ~125M) | ~200-400ms | ~50-100ms | ~500MB → ~200MB |
| Validatori Checksum | <1ms | <1ms | ~0 |
| Pattern Regex | <5ms | <5ms | ~0 |
| Pattern Data | <2ms | <2ms | ~0 |
| Raffinamento Limiti | <1ms | <1ms | ~0 |
| **Totale** | **~210-410ms** | **~60-110ms** | **~500MB → ~200MB** |

**Conclusione:** Con ONNX INT8 dovrebbe soddisfare <500ms/pagina con ampio margine.

### 6.4 Raccomandazione

1.  **Prima misurare** latenza attuale con PyTorch (script `benchmark_latency.py`)
2.  **Se soddisfa** <500ms su CPU: documentare e rimandare ottimizzazione ONNX
3.  **Se fallisce**: export ONNX + quantizzazione INT8 (prioritizzare)
4.  **Documentare** processo per replicabilità in altre lingue

---

## 7. Lacuna 5: Gazzettieri (BASSA)

### 7.1 Stato dell'Arte

#### 7.1.1 GAIN: Gazetteer-Adapted Integration Network (SemEval-2022)

*   **Adattamento divergenza KL:** Rete Gazzettiere si adatta al language model minimizzando divergenza KL
*   **2 stadi:** Prima adattare gazzettiere al modello, poi addestrare NER supervisionato
*   **Risultato:** 1º in 3 track (Cinese, Code-mixed, Bangla), 2º in 10 track
*   **Intuizione:** Gazzettieri sono più utili se integrati come feature aggiuntiva, non come lookup diretto

#### 7.1.2 Gazetteer-Enhanced Attentive Neural Networks (EMNLP 2019)

*   Rete ausiliaria che codifica "regolarità nome" usando solo gazzettieri
*   Incorporata nel NER principale per miglior riconoscimento
*   **Riduce requisiti dati addestramento** significativamente

#### 7.1.3 Soft Gazetteers per Low-Resource NER (ACL 2020)

*   In lingue senza gazzettieri esaustivi, usare entity linking interlinguistico
*   Wikipedia come fonte di conoscenza
*   Sperimentato in 4 lingue a risorse limitate

#### 7.1.4 Riduzione Match Spurio

*   Gazzettieri grezzi generano **molti falsi positivi** (match spurio)
*   Filtrare per "popolarità entità" migliora F1 del +3.70%
*   **Gazzettieri Puliti > Gazzettieri Completi**

### 7.2 Gazzettieri Disponibili in ContextSafe

| Gazzettiere | Record | Fonte | In Pipeline |
|-------------|--------|-------|-------------|
| Cognomi | 27,251 | INE | ❌ |
| Nomi uomini | 550 | INE | ❌ |
| Nomi donne | 550 | INE | ❌ |
| Nomi arcaici | 6,010 | Generato | ❌ |
| Comuni | 8,115 | INE | ❌ |
| Codici postali | 11,051 | INE | ❌ |

### 7.3 Raccomandazione Basata su Prove

**Non integrare gazzettieri nel pipeline principale** per le seguenti ragioni basate sulla letteratura:

1.  **Match spurio** (EMNLP 2019): Senza filtro popolarità, i gazzettieri generano falsi positivi
2.  **Pipeline funziona già** (F1 0.788): Beneficio marginale dei gazzettieri è basso
3.  **Complessità replicabilità**: I gazzettieri sono specifici per lingua, ogni lingua necessita di fonti diverse

**Uso raccomandato come post-filtro:**
*   **Validazione nome:** Se NER rileva PERSON, verificare se nome/cognome è nel gazzettiere → boost confidenza +0.05
*   **Validazione Codice Postale:** Se regex rileva POSTAL_CODE 28001, verificare se corrisponde a comune reale → boost confidenza +0.10
*   **NON usare per rilevamento:** Non cercare nomi gazzettiere direttamente nel testo (rischio match spurio)

---

## 8. Piano d'Azione

### 8.1 Azioni Immediate (Alta Priorità)

| Azione | Base Accademica | File |
|--------|-----------------|------|
| Implementare strategia unione 3 fasi | RECAP (2025) | `ner_predictor.py` |
| Rimuovere confidenza fissa 0.95 in regex | JCLB/BRB (2024) | `spanish_id_patterns.py` |
| Aggiungere tabella priorità per tipo | RECAP, Presidio | `ner_predictor.py` |

### 8.2 Azioni di Miglioramento (Media Priorità)

| Azione | Base Accademica | File |
|--------|-----------------|------|
| Valutare con nervaluate (match parziale) | SemEval'13 Task 9 | `benchmark_nervaluate.py` |
| Creare benchmark latenza | PyDeID (2025) | `benchmark_latency.py` |
| Documentare calibrazione lunghezza | CP NER (2026) | Guida replicabilità |

### 8.3 Azioni Differite (Bassa Priorità)

| Azione | Base Accademica | File |
|--------|-----------------|------|
| Gazzettieri come post-filtro | GAIN (2022) | `ner_predictor.py` |
| Export ONNX + INT8 | HuggingFace Optimum | `scripts/export/` |

---

## 9. Conclusioni

### 9.1 Scoperte Principali della Ricerca

1.  **Il pipeline ibrido è SOTA per PII** — RECAP (2025), PyDeID (2025), e Mishra et al. (2025) confermano che regex + NER supera ogni componente separatamente.

2.  **La confidenza regex non dovrebbe essere fissa** — JCLB (2024) ha dimostrato che assegnare confidenza appresa alle regole migliora significativamente le prestazioni.

3.  **La calibrazione per lunghezza testo è importante** — Previsione Conforme (2026) ha dimostrato miscalibrazione sistematica in sequenze lunghe.

4.  **nervaluate completa seqeval** — SemEval'13 Task 9 offre metriche di match parziale che catturano errori di limite che seqeval ignora.

5.  **ONNX INT8 è fattibile per latenza <500ms** — PyDeID ha dimostrato <0.5s/documento con pipeline ibrido ottimizzato.

### 9.2 Stato dei Modelli Valutati

| Modello | Valutazione | F1 Adversarial | Stato |
|---------|-------------|----------------|-------|
| **RoBERTa-BNE CAPITEL NER** (`legal_ner_v2`) | Pipeline completa 5 elementi | **0.788** | **ATTIVO** |
| GLiNER-PII (zero-shot) | Valutato su 35 test adversarial | 0.325 | Scartato (inferiore) |
| LoRA Legal-XLM-R-base (`lora_ner_v1`) | Valutato su 35 test adversarial | 0.016 | Scartato (overfitting) |
| MEL (Modello Legale Spagnolo) | Investigato | N/A (no versione NER) | Scartato |
| Legal-XLM-R-base (joelniklaus) | Investigato per multilingue | N/A | In sospeso per espansione futura |

> **Nota:** Il modello base del pipeline è `roberta-base-bne-capitel-ner` (RoBERTa-BNE, ~125M params, vocab 50,262),
> fine-tuned con dati sintetici v3 (30% iniezione rumore). **NON** è XLM-RoBERTa.

### 9.3 Raccomandazioni per Replicabilità

Per replicare in altre lingue, gli adattatori sono:

| Componente | Spagna (ES) | Francia (FR) | Italia (IT) | Adattamento |
|------------|-------------|--------------|-------------|-------------|
| Modello NER | RoBERTa-BNE CAPITEL | JuriBERT/CamemBERT | Legal-BERT-IT | Fine-tune NER per lingua |
| NER Multilingue (alternativa) | Legal-XLM-R | Legal-XLM-R | Legal-XLM-R | Singolo modello multilingue |
| Pattern Regex | DNI/NIE, IBAN ES | CNI, IBAN FR | CF, IBAN IT | Nuovo file regex |
| Validator Checksum | mod-23 (DNI) | mod-97 (IBAN) | Codice Fiscale | Nuovo validatore |
| Priorità Unione | Tabella 3.5 | Stessa struttura | Stessa struttura | Regolare tipi |
| Calibrazione Confidenza | Tabella 4.5 | Stessa struttura | Stessa struttura | Calibrare per tipo locale |
| Gazzettieri | INE | INSEE | ISTAT | Fonti nazionali |

---

**Generato da:** AlexAlves87
**Data:** 30-01-2026
**Versione:** 2.0.0 — Riscritto con ricerca accademica (v1.0 mancava di fondamento)
