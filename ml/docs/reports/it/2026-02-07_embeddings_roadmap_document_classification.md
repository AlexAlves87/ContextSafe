# Embedding per ContextSafe: Roadmap e Criteri di Attivazione

**Data:** 07-02-2026
**Obiettivo:** Documentare l'approccio agli embedding valutato, le alternative implementate,
e i criteri in base ai quali sarebbe giustificabile scalare agli embedding in futuro.

---

## 1. Riepilogo Esecutivo

Sono state valutate due proposte che coinvolgono embedding:

| Proposta | Fonte | Modello | Decisione |
|----------|-------|---------|-----------|
| Classificazione documenti con embedding | Miglioramenti Architetturali v2.1, Modulo A | `intfloat/multilingual-e5-small` | **Differita** — Regex implementata |
| Gap Scanning con embedding | Strategia Safety Net A | `intfloat/multilingual-e5-small` | **Scartata** — Similarità coseno inadeguata |

**Stato attuale:** È stato implementato un classificatore basato su regex/keyword
(`DocumentTypeClassifier`) che copre i requisiti immediati con 0 byte di modello,
<1ms di latenza e ~95% di accuratezza stimata per documenti legali spagnoli.

Gli embedding restano documentati come **opzione di scalabilità futura** quando saranno soddisfatti
criteri specifici (Sezione 5).

---

## 2. Proposta Valutata: Classificazione Documenti con Embedding

### 2.1 Modello Proposto

| Specifica | Valore |
|-----------|--------|
| Modello | `intfloat/multilingual-e5-small` (Wang et al., arXiv:2402.05672) |
| Parametri | 117.65M |
| Dimensione FP32 | 448 MB |
| Dimensione INT8 ONNX | 112 MB |
| Dimensione Embedding | 384 |
| Max token | 512 |
| Latenza stimata (CPU INT8) | ~200ms |
| Lingue supportate | 94-100 |
| Licenza | MIT |
| RAM runtime (FP32) | ~500 MB |
| RAM runtime (INT8) | ~200 MB |

**Fonte di verifica:** HuggingFace model card `intfloat/multilingual-e5-small`.

### 2.2 Architettura Proposta

```
Documento → Embedding (e5-small) → Similarità Coseno vs centroidi → Tipo → Config NER
```

Questo NON è RAG-NER (il termine usato nella proposta v2.1 è errato).
È **classificazione di documenti + configurazione condizionale**
(vedi `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md`, Sezione 2).

### 2.3 Perché è Stata Differita

| Fattore | Embedding | Regex (implementata) |
|---------|-----------|----------------------|
| Dimensione | 112-448 MB | 0 byte |
| Latenza | ~200ms | <1ms |
| Accuratezza stimata | ~99% | ~95%+ |
| Complessità | Alta (runtime ONNX, quantizzazione) | Banale |
| RAM aggiuntiva | 200-500 MB | 0 |
| Manutenzione | Modello versionato, aggiornamenti | Pattern modificabili |

Per ~7 tipi di documenti legali con intestazioni altamente distintive, la regex è
sufficiente. Il 4% aggiuntivo di accuratezza non giustifica 200MB di modello né la complessità
di manutenzione.

---

## 3. Proposta Valutata: Gap Scanning con Embedding

### 3.1 Concetto

Usare embedding per rilevare frammenti "sospetti" non identificati dal NER:

```
Testo completo → Segmentare in chunk → Embedding di ogni chunk
    → Confrontare vs "centroide di rischio PII" → Avvisare se similarità alta
```

### 3.2 Perché è Stata Scartata

1. **La similarità coseno non rileva PII**: La similarità semantica misura la vicinanza tematica,
   non la presenza di dati personali. "Juan García vive a Madrid" e "L'azienda opera
   a Madrid" hanno alta similarità semantica ma solo uno contiene PII nominale.

2. **Non esiste un "centroide di rischio PII"**: I dati personali (nomi, DNI, IBAN,
   indirizzi) occupano regioni semantiche completamente disgiunte. Non c'è un punto nello
   spazio degli embedding che rappresenti "questo contiene PII"
   (vedi Ethayarajh, EMNLP 2019, sull'anisotropia degli embedding).

3. **Paper di riferimento**: Netflix/Cornell 2024 documenta i limiti della similarità coseno
   per la rilevazione di caratteristiche discrete vs continue. La PII è intrinsecamente
   discreta (presente o assente).

4. **Alternativa implementata**: I Sanity Check deterministici (`ExportValidator`,
   `src/contextsafe/domain/document_processing/services/export_validator.py`) coprono
   il caso dei falsi negativi per tipo di documento in modo più affidabile e senza
   dipendenze aggiuntive.

---

## 4. Alternativa Implementata: Classificatore Regex

### 4.1 Implementazione

```
src/contextsafe/domain/document_processing/services/document_classifier.py
```

| Caratteristica | Dettaglio |
|----------------|-----------|
| Tipi supportati | SENTENCIA, ESCRITURA, FACTURA, RECURSO, DENUNCIA, CONTRATO, GENERIC |
| Metodo | Regex sui primi 500 caratteri (maiuscolo) |
| Pattern per tipo | 4-8 keyword distintive |
| Fallback | Nome del file se il testo non classifica |
| Confidenza | Rapporto pattern trovati / totale per tipo |
| Latenza | <1ms |
| Dipendenze | 0 (solo `re` della stdlib) |

### 4.2 Pattern Chiave

| Tipo | Pattern principali |
|------|--------------------|
| SENTENCIA | `SENTENCIA`, `JUZGADO`, `TRIBUNAL`, `FALLO`, `MAGISTRAD[OA]` |
| ESCRITURA | `ESCRITURA`, `NOTAR[IÍ]`, `PROTOCOLO`, `OTORGAMIENTO` |
| FACTURA | `FACTURA`, `BASE IMPONIBLE`, `IVA`, `TOTAL FACTURA` |
| RECURSO | `RECURSO`, `APELACI[OÓ]N`, `CASACI[OÓ]N` |
| DENUNCIA | `DENUNCIA`, `ATESTADO`, `DILIGENCIAS PREVIAS` |
| CONTRATO | `CONTRATO`, `CL[AÁ]USULA`, `ESTIPULACIONES` |

### 4.3 Integrazione con Sanity Check

Il classificatore alimenta le regole di validazione dell'esportazione:

```
Documento → DocumentTypeClassifier → tipo
                                       ↓
ExportValidator.validate(tipo, ...) → Applica regole SC-001..SC-004
```

| Regola | Tipo | Categorie minime | Severità |
|--------|------|------------------|----------|
| SC-001 | ESCRITURA | PERSON_NAME ≥1, DNI_NIE ≥1 | CRITICA |
| SC-002 | SENTENCIA | DATE ≥1 | AVVISO |
| SC-003 | FACTURA | ORGANIZATION ≥1 | AVVISO |
| SC-004 | DENUNCIA | PERSON_NAME ≥1 | AVVISO |

---

## 5. Criteri di Attivazione per Scalare agli Embedding

Gli embedding dovrebbero essere riconsiderati SOLO se sono soddisfatti **almeno 2** di questi criteri:

### 5.1 Criteri Funzionali

| # | Criterio | Soglia |
|---|----------|--------|
| CF-1 | L'accuratezza regex scende sotto il 90% | Misurare con corpus di validazione |
| CF-2 | Aggiunti >15 tipi di documento | Regex diventa ingestibile |
| CF-3 | Documenti senza intestazione standardizzata | OCR degradato, scanner vari |
| CF-4 | Requisito di classificazione multilingue | Documenti in catalano, basco, gallego |

### 5.2 Criteri Infrastrutturali

| # | Criterio | Soglia |
|---|----------|--------|
| CI-1 | RAM disponibile in produzione | ≥32 GB (attualmente target è 16 GB) |
| CI-2 | La pipeline usa già ONNX Runtime | Evita di aggiungere nuova dipendenza |
| CI-3 | Latenza attuale della pipeline | <2s totale (margine per +200ms) |

### 5.3 Percorso di Implementazione (se attivato)

```
Passo 1: Raccogliere corpus di validazione (50+ doc per tipo)
Passo 2: Valutare accuratezza attuale regex con corpus
Passo 3: Se accuratezza < 90%, valutare prima TF-IDF + LogReg (~50KB, <5ms)
Passo 4: Solo se TF-IDF < 95%, scalare a e5-small INT8 ONNX
Passo 5: Generare centroidi per tipo con corpus etichettato
Passo 6: Validare con test adversarial (documenti misti, OCR degradato)
```

### 5.4 Modello Raccomandato (se si scala)

| Opzione | Dimensione | Latenza | Caso d'uso |
|---------|------------|---------|------------|
| TF-IDF + LogReg | ~50 KB | <5ms | Primo passo di scalabilità |
| `intfloat/multilingual-e5-small` INT8 | 112 MB | ~200ms | Classificazione multilingue |
| `BAAI/bge-small-en-v1.5` INT8 | 66 MB | ~150ms | Solo inglese/spagnolo |

**Nota:** `intfloat/multilingual-e5-small` rimane la migliore opzione per il multilingue
se necessario. Ma TF-IDF è il passo intermedio corretto prima degli embedding neurali.

---

## 6. Impatto sulla Pipeline NER

### 6.1 Stato Attuale (implementato)

```
Documento ingerito
    ↓
DocumentTypeClassifier.classify(primi_500_char)         ← REGEX
    ↓
ConfidenceZone.classify(score, categoria, checksum)     ← TRIAGE
    ↓
CompositeNerAdapter.detect_entities(text)               ← NER
    ↓
ExportValidator.validate(tipo, entità, revisioni)       ← CHIUSURA DI SICUREZZA
    ↓
[Esportazione consentita o bloccata]
```

### 6.2 Stato Futuro (se embedding attivati)

```
Documento ingerito
    ↓
DocumentTypeClassifier.classify(primi_500_char)         ← REGEX (fallback)
    ↓
EmbeddingClassifier.classify(primi_512_token)           ← EMBEDDING
    ↓
merge_classifications(risultato_regex, risultato_emb)   ← FUSIONE
    ↓
CompositeNerAdapter.detect_entities(text, doc_type=tipo) ← NER CONTESTUALE
    ↓
ExportValidator.validate(tipo, entità, revisioni)       ← CHIUSURA DI SICUREZZA
```

L'interfaccia del classificatore (`DocumentClassification` dataclass) è già progettata per
essere sostituibile senza modifiche al resto della pipeline.

---

## 7. Conclusione

L'approccio attuale (regex) è la decisione corretta per lo stato presente del progetto.
Gli embedding rappresentano un miglioramento incrementale che è giustificato solo a fronte di una crescita
significativa nei tipi di documento o degradazione misurabile dell'accuratezza.

L'architettura esagonale permette di scalare senza refactoring: il `DocumentTypeClassifier`
può essere sostituito da un `EmbeddingClassifier` che implementi la stessa interfaccia
(`DocumentClassification`), senza impatto sul resto della pipeline.

---

## Documenti Correlati

| Documento | Relazione |
|-----------|-----------|
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Valutazione critica della proposta RAG-NER |
| `ml/docs/reports/2026-02-03_ciclo_ml_completo_5_elementos.md` | Pipeline NER attuale (5 elementi) |
| `ml/docs/reports/2026-02-06_adversarial_v2_academic_r7.md` | Valutazione adversarial della pipeline |
| `src/contextsafe/domain/document_processing/services/document_classifier.py` | Classificatore regex implementato |
| `src/contextsafe/domain/document_processing/services/export_validator.py` | Chiusura di Sicurezza + Sanity Check |
| `src/contextsafe/domain/entity_detection/services/confidence_zone.py` | Triage per zone di confidenza |

## Riferimenti

| Riferimento | Sede | Rilevanza |
|-------------|------|-----------|
| Wang et al., "Multilingual E5 Text Embeddings" | arXiv:2402.05672 (2024) | Modello valutato |
| Ethayarajh, "How Contextual are Contextualized Word Representations?" | EMNLP 2019 | Anisotropia embedding |
| Netflix/Cornell, "Limitations of Cosine Similarity" | arXiv (2024) | Limitazioni per rilevamento discreto |
| Lewis et al., "Retrieval-Augmented Generation" | NeurIPS 2020 | Definizione corretta di RAG |
| Dai et al., "RA-NER" | ICLR 2024 Tiny Papers | Vero RAG applicato a NER |
