# Valutazione Critica: Proposta Embedding (RAG-NER) per ContextSafe

**Data:** 07-02-2026
**Obiettivo:** Valutare la validità tecnica e la necessità del Modulo A della proposta
"Miglioramenti Architetturali v2.1" — uso di `intfloat/multilingual-e5-small` per
la pre-classificazione dei documenti e la configurazione dinamica del NER.

---

## 1. Riepilogo Esecutivo

La proposta suggerisce di utilizzare embedding (`intfloat/multilingual-e5-small`, ~120MB) come
"Elemento 0" della pipeline NER per classificare i tipi di documento e adattare dinamicamente
le soglie di rilevamento. Dopo aver indagato la letteratura accademica, verificato le
specifiche del modello e confrontato con lo stato attuale della pipeline di ContextSafe,
**la conclusione è che l'idea di base ha un merito parziale, ma l'implementazione proposta
è un'ingegnerizzazione eccessiva e il termine "RAG-NER" è tecnicamente errato**.

### Verdetto

| Aspetto | Valutazione |
|---------|-------------|
| Concetto (NER consapevole del tipo di documento) | Valido e utile |
| Termine "RAG-NER" | Errato: non è RAG |
| Modello proposto (`multilingual-e5-small`) | Eccessivo per il compito |
| Necessità reale in ContextSafe | Media: alternative più semplici disponibili |
| Priorità vs altri miglioramenti | Bassa rispetto a miglioramenti HITL e audit |

---

## 2. Analisi del Termine "RAG-NER"

### Cos'è RAG nella letteratura

RAG (Retrieval-Augmented Generation) è stato introdotto da Lewis et al. (NeurIPS 2020)
e si riferisce specificamente al **recupero di documenti/passaggi da una base di
conoscenza per aumentare la generazione** di un modello linguistico.

I veri paper RAG+NER (2024-2025) sono:

| Paper | Sede | Cosa fa realmente |
|-------|------|-------------------|
| **RA-NER** (Dai et al.) | ICLR 2024 Tiny Papers | Recupera entità simili da una KB esterna per aiutare il NER |
| **RENER** (Shiraishi et al.) | arXiv 2410.13118 | Recupera esempi annotati simili come in-context learning per il NER |
| **RA-IT Open NER** | arXiv 2406.17305 | Instruction tuning con esempi recuperati per open NER |
| **IF-WRANER** | arXiv 2411.00451 | Retrieval a livello di parola per few-shot cross-domain NER |
| **RAG-BioNER** | arXiv 2508.06504 | Prompting dinamico con RAG per NER biomedico |

### Cosa propone il documento v2.1

Ciò che viene descritto NON è RAG. È **classificazione del tipo di documento + configurazione
condizionale del NER**. Non c'è recupero di documenti/esempi da una base di
conoscenza. Non c'è aumento della generazione. È un classificatore seguito da uno switch.

**Diagramma reale della proposta:**
```
Documento → Embedding (e5-small) → Similarità Coseno → Tipo rilevato → Switch config → NER
```

**Diagramma reale di RAG-NER (RA-NER, Amazon):**
```
Testo input → Recuperare entità simili da KB → Iniettare come contesto nel NER → Predizione
```

Sono architetture fondamentalmente diverse. Etichettare la proposta come "RAG-NER"
è errato e potrebbe indurre in errore nella documentazione tecnica o nelle pubblicazioni.

---

## 3. Verifica del Modello Proposto

### Specifiche reali di `intfloat/multilingual-e5-small`

| Specifica | Claim v2.1 | Valore reale | Fonte |
|-----------|------------|--------------|-------|
| Peso | ~120 MB | **448 MB (FP32), 112 MB (INT8 ONNX)** | HuggingFace |
| Parametri | Non indicato | 117.65M | HuggingFace |
| Dimensione embedding | Non indicata | 384 | Paper arXiv:2402.05672 |
| Max token | 512 | 512 (corretto) | HuggingFace |
| Latenza | <200ms su CPU | Plausibile per 512 token INT8 | - |
| Lingue | Non indicato | 94-100 lingue | HuggingFace |
| Licenza | Non indicata | MIT | HuggingFace |

**Problemi rilevati:**
- Il claim di "~120 MB" è vero solo con quantizzazione INT8 ONNX. Il modello FP32 pesa
  448 MB. Il documento non chiarisce che è richiesta la quantizzazione.
- In memoria (runtime), il modello FP32 consuma ~500MB di RAM. Con INT8, ~200MB.
- Sull'hardware target con 16GB di RAM (già caricato con RoBERTa + Presidio + spaCy),
  il margine disponibile è limitato.

### Benchmark di riferimento

| Benchmark | Risultato | Contesto |
|-----------|-----------|----------|
| Mr. TyDi (retrieval MRR@10) | 64.4 avg | Buono per retrieval multilingue |
| MTEB Classification (Amazon) | 88.7% accuratezza | Accettabile per classificazione |

Il modello è competente per compiti di embedding. La domanda è se sia necessario un
modello da 117M parametri per classificare ~5 tipi di documenti legali.

---

## 4. Analisi di Necessità: Stato Attuale vs Proposta

### Pipeline attuale di ContextSafe

Il `CompositeNerAdapter` implementa già meccanismi sofisticati di contestualizzazione:

| Meccanismo esistente | Descrizione |
|----------------------|-------------|
| **Contextual Anchors** (Fase 1) | Forza categorie secondo il contesto legale spagnolo |
| **Weighted Voting** (Fase 2) | Regex=5, RoBERTa=2, Presidio=1.5, spaCy=1 |
| **GDPR Risk Tiebreaker** (Fase 3) | Priorità: PERSON_NAME=100 → POSTAL_CODE=20 |
| **30+ False Positive Pattern** | Blocca riferimenti legali, DOI, ORCID, ISBN |
| **Filtro Stopwords Spagnole** | Evita rilevamento di articoli/pronomi |
| **Whitelist Termini Generici** | Termini mai anonimizzati (Stato, GDPR, ecc.) |
| **Matrioshka (entità nidificate)** | Gestione delle entità nidificate |

La pipeline attuale NON ha:
- Classificazione del tipo di documento
- Soglie dinamiche per categoria
- Soglie dinamiche per tipo di documento

### ContextSafe ha bisogno della classificazione dei documenti?

**Parzialmente sì**, ma non come proposto. I benefici reali sarebbero:
- Adattare la soglia IBAN nelle fatture (più rigorosa) vs sentenze (più rilassata)
- Attivare/disattivare categorie in base al contesto (es. data di nascita rilevante
  in sentenze penali, non in fatture)
- Ridurre falsi positivi di nomi propri in documenti con molte ragioni sociali

### Alternative più semplici ed efficaci

| Metodo | Dimensione | Latenza | Accuratezza stimata | Complessità |
|--------|------------|---------|---------------------|-------------|
| **Regex su intestazioni** | 0 KB (codice) | <1ms | ~95%+ | Banale |
| **TF-IDF + LogisticRegression** | ~50 KB | <5ms | ~97%+ | Bassa |
| **e5-small (INT8 ONNX)** | 112 MB | ~200ms | ~99% | Alta |
| **e5-small (FP32)** | 448 MB | ~400ms | ~99% | Alta |

Per i documenti legali spagnoli, le intestazioni sono estremamente distintive:
- `"SENTENCIA"`, `"JUZGADO"`, `"TRIBUNAL"` → Sentenza
- `"ESCRITURA"`, `"NOTARIO"`, `"PROTOCOLO"` → Atto Notarile
- `"FACTURA"`, `"BASE IMPONIBLE"`, `"IVA"` → Fattura
- `"RECURSO"`, `"APELACIÓN"`, `"CASACIÓN"` → Ricorso/Appello

Un classificatore basato su regex/keyword nei primi 200 caratteri probabilmente
raggiunge un'accuratezza >95% senza aggiungere dipendenze né latenza significativa.

---

## 5. Raccomandazione

### Cosa SI raccomanda di implementare

1. **Classificazione tipo documento** — ma con regex/keyword, non embedding
2. **Soglie dinamiche per categoria** — indipendenti dalla classificazione
3. **Configurazione condizionale NER** — attivare/disattivare regole per tipo

### Cosa NON si raccomanda

1. **Non usare embedding** per classificare ~5 tipi di documenti legali
2. **Non chiamarlo "RAG-NER"** — è classificazione + configurazione condizionale
3. **Non aggiungere 112-448MB di modello** quando la regex raggiunge lo stesso obiettivo

### Implementazione suggerita (alternativa)

```python
# Element 0: Document Type Classifier (lightweight)
class DocumentTypeClassifier:
    """Classify legal document type from header text."""

    PATTERNS = {
        DocumentType.SENTENCIA: [r"SENTENCIA", r"JUZGADO", r"TRIBUNAL", r"FALLO"],
        DocumentType.ESCRITURA: [r"ESCRITURA", r"NOTARI", r"PROTOCOLO"],
        DocumentType.FACTURA: [r"FACTURA", r"BASE IMPONIBLE", r"IVA"],
        DocumentType.RECURSO: [r"RECURSO", r"APELACI[OÓ]N", r"CASACI[OÓ]N"],
    }

    def classify(self, text: str, max_chars: int = 500) -> DocumentType:
        header = text[:max_chars].upper()
        scores = {}
        for doc_type, patterns in self.PATTERNS.items():
            scores[doc_type] = sum(1 for p in patterns if re.search(p, header))
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return DocumentType.GENERIC
```

**Costo:** 0 byte di modello, <1ms latenza, ~0 complessità aggiuntiva.
**Estendibile:** Se in futuro sarà necessaria maggiore sofisticazione, si può scalare
a TF-IDF o embedding. Ma iniziare in modo semplice.

---

## 6. Sull'"Elemento 0" nella pipeline

Se si decide di implementare la classificazione dei documenti (con il metodo semplice raccomandato),
la posizione corretta sarebbe:

```
Documento ingerito
    ↓
Element 0: classify_document_type(primi_500_caratteri)  ← NUOVO
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=tipo)
    ↓
[RoBERTa | Presidio | Regex | spaCy] con soglie adattate secondo doc_type
    ↓
Merge (voto ponderato attuale, funziona già bene)
```

Questo passaggio è coerente con l'architettura esagonale attuale e non richiede modifiche
alle porte o agli adattatori esistenti.

---

## 7. Conclusione

La proposta identifica un bisogno reale (NER consapevole del tipo di documento)
ma propone una soluzione sovraingegnerizzata con terminologia errata. Un classificatore
basato su regex sulle intestazioni dei documenti raggiungerebbe lo stesso obiettivo senza aggiungere
120-448MB di modello, 200ms di latenza aggiuntiva o complessità di manutenzione.

L'investimento di sforzi rende molto di più nel Modulo B (audit attivo e
tracciabilità HITL), dove ContextSafe ha reali lacune di conformità normativa.

---

## 8. Letteratura Consultata

| Riferimento | Sede | Rilevanza |
|-------------|------|-----------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Modello proposto |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | Vero RAG applicato a NER |
| Shiraishi et al., "RENER" | arXiv:2410.13118 (2024) | Retrieval-enhanced NER |
| arXiv 2406.17305, "RA-IT Open NER" | arXiv (2024) | Instruction tuning + retrieval |
| arXiv 2411.00451, "IF-WRANER" | arXiv (2024) | Few-shot cross-domain NER + RAG |
| arXiv 2508.06504, "RAG-BioNER" | arXiv (2025) | Dynamic prompting + RAG |
| ACL 2020 LT4Gov, "Legal-ES" | ACL Anthology | Embedding legali spagnoli |
| IEEE 2024, "Fine-grained NER Spanish legal" | IEEE Xplore | NER legale spagnolo |
| Frontiers AI 2025, "LegNER multilingual" | Frontiers | NER legale multilingue |

## Documenti Correlati

| Documento | Relazione |
|-----------|-----------|
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline NER attuale (5 elementi) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Valutazione adversarial della pipeline attuale |
| `ml/docs/reports/2026-01-31_mejores_practicas_ml_2026.md` | Best practice ML |
| `src/contextsafe/infrastructure/nlp/composite_adapter.py` | Implementazione attuale della pipeline NER |
