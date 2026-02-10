# Ricerca: Embedding per Disambiguazione dei Tipi di Entità in NER

**Data:** 07-02-2026
**Obiettivo:** Risolvere gli errori di classificazione del tipo di entità nel sistema NER di ContextSafe (es: "Alejandro Alvarez" classificato come ORGANIZATION invece di PERSON_NAME)

---

## 1. Riepilogo Esecutivo

1. **Problema identificato**: Il modello NER attuale confonde i tipi di entità, classificando nomi di persone come organizzazioni, date come organizzazioni e parole comuni in maiuscolo come PII.

2. **Soluzione proposta**: Validatore post-NER basato su embedding che confronta ogni rilevamento con centroidi semantici per tipo di entità.

3. **Modello raccomandato**: `intfloat/multilingual-e5-large` (1.1GB) con possibile upgrade a `Legal-Embed` per il dominio legale.

4. **Tecnica principale**: Classificazione basata su centroidi con soglia di riclassificazione (soglia 0.75, margine 0.1).

5. **Riduzione degli errori prevista**: ~4.5% secondo la letteratura (benchmark WNUT17).

---

## 2. Letteratura Esaminata

| Paper | Sede | Anno | Risultato Rilevante |
|-------|------|------|---------------------|
| NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings | arXiv (2509.04011) | 2025 | I layer intermedi (layer 17) catturano meglio le informazioni sul tipo rispetto agli output finali. MLP con contrastive loss raggiunge zero-shot su tipi non visti. |
| CEPTNER: Contrastive Learning Enhanced Prototypical Network for Few-shot NER | Knowledge-Based Systems (ScienceDirect) | 2024 | Reti prototipiche con apprendimento contrastivo separano efficacemente i tipi di entità con pochi esempi (50-100). |
| Recent Advances in Named Entity Recognition: A Comprehensive Survey | arXiv (2401.10825) | 2024 | Approcci ibridi (regole + ML + embedding) superano costantemente i modelli singoli. |
| Redundancy-Enhanced Framework for Error Correction in NER | OpenReview | 2025 | Post-processore con Transformer refiner + entity-tag embedding raggiunge una riduzione degli errori del 4.48% in WNUT17. |
| Multilingual E5 Text Embeddings: A Technical Report | arXiv (2402.05672) | 2024 | Il modello multilingual-e5-large supporta 100 lingue con prestazioni eccellenti in spagnolo. Richiede il prefisso "query:" per gli embedding di ricerca. |

---

## 3. Best Practice Identificate

1. **Includere il contesto**: Incorporare l'entità CON il suo contesto circostante (10-15 parole) migliora significativamente la disambiguazione.

2. **Usare layer intermedi**: Le rappresentazioni dai layer medi (layer 15-17) contengono più informazioni sul tipo rispetto agli output finali.

3. **Contrastive learning**: L'addestramento con perdita contrastiva separa meglio i tipi nello spazio degli embedding.

4. **Soglia con margine**: Non riclassificare solo per maggiore similarità; richiedere un margine minimo (>0.1) per evitare falsi positivi.

5. **Esempi per tipo**: 50-100 esempi confermati per categoria sono sufficienti per costruire centroidi robusti.

6. **Dominio specifico**: Modelli fine-tuned per il dominio (legale nel nostro caso) migliorano le prestazioni.

7. **Flagging per HITL**: Quando le similarità sono vicine (<0.05 differenza), contrassegnare per revisione umana invece di riclassificare automaticamente.

---

## 4. Raccomandazione per ContextSafe

### 4.1 Architettura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline NER Attuale                         │
│  (RoBERTa + SpaCy + Regex → Merge Intelligente)                 │
60 └─────────────────────┬───────────────────────────────────────────┘
                      │ Rilevamenti con tipo assegnato
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Entity Type Validator (NUOVO)                       │
│                                                                  │
│  1. Estrarre entità + contesto (±15 token)                      │
│  2. Generare embedding con multilingual-e5-large                │
│  3. Calcolare similarità coseno con centroidi per tipo          │
│  4. Decisione:                                                  │
│     - Se miglior_tipo ≠ tipo_NER AND similarità > 0.75          │
│       AND margine > 0.1 → RICLASSIFICARE                        │
│     - Se margine < 0.05 → CONTRASSEGNARE PER HITL               │
│     - Altrimenti → MANTENERE tipo NER                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Rilevamenti validati/corretti
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Glossario & Anonimizzazione                      │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Modello Selezionato

**Principale**: `intfloat/multilingual-e5-large`
- Dimensione: 1.1GB
- Lingue: 100 (eccellente spagnolo)
- Latenza: ~50-100ms per embedding
- Richiede prefisso "query:" per embedding

**Alternativa (valutare)**: `Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct`
- Fine-tuned per dominio legale
- Stessa dimensione base
- Potenzialmente migliore per documenti legali spagnoli

### 4.3 Costruzione dei Centroidi

Categorie prioritarie (confusione frequente):

| Categoria | Esempi Necessari | Fonte |
|-----------|------------------|-------|
| PERSON_NAME | 100 | Nomi da auditoria.md + gazzette |
| ORGANIZATION | 100 | Aziende, istituzioni da documenti legali |
| DATE | 50 | Date in formati DD/MM/YYYY, DD-MM-YYYY |
| LOCATION | 50 | Città, province spagnole |

**Formato di esempio** (con contesto):
```
"query: L'avvocato Alejandro Alvarez è comparso come testimone nel processo"
"query: La società Telefónica S.A. ha presentato ricorso per cassazione"
"query: In data 10/10/2025 è stata emessa sentenza"
```

### 4.4 Integrazione con Pipeline Esistente

Posizione proposta: `src/contextsafe/infrastructure/nlp/validators/entity_type_validator.py`

```python
class EntityTypeValidator:
    """
    Post-processor that validates/corrects NER entity type assignments
    using embedding similarity to type centroids.

    Based on: NER Retriever (arXiv 2509.04011), CEPTNER (KBS 2024)
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        centroids_path: Path = None,
        reclassify_threshold: float = 0.75,
        margin_threshold: float = 0.10,
        hitl_margin: float = 0.05,
    ):
        ...

    def validate(
        self,
        entity_text: str,
        context: str,
        predicted_type: str,
    ) -> ValidationResult:
        """
        Returns ValidationResult with:
        - corrected_type: str
        - confidence: float
        - action: 'KEEP' | 'RECLASSIFY' | 'FLAG_HITL'
        """
        ...
```

### 4.5 Metriche di Successo

| Metrica | Obiettivo | Misurazione |
|---------|-----------|-------------|
| Riduzione errori di tipo | ≥4% | Confrontare prima/dopo su set di validazione |
| Latenza aggiuntiva | <100ms/entità | Benchmark su CPU 16GB |
| Falsi positivi riclassificazione | <2% | Revisione manuale delle riclassificazioni |
| Copertura HITL | <10% flaggati | Percentuale contrassegnata per revisione umana |

---

## 5. Riferimenti

1. **NER Retriever**: Zhang et al. (2025). "NER Retriever: Zero-Shot Named Entity Retrieval with Type-Aware Embeddings." arXiv:2509.04011. https://arxiv.org/abs/2509.04011

2. **CEPTNER**: Wang et al. (2024). "CEPTNER: Contrastive learning Enhanced Prototypical network for Two-stage Few-shot Named Entity Recognition." Knowledge-Based Systems. https://doi.org/10.1016/j.knosys.2024.111512

3. **NER Survey**: Li et al. (2024). "Recent Advances in Named Entity Recognition: A Comprehensive Survey and Comparative Study." arXiv:2401.10825. https://arxiv.org/abs/2401.10825

4. **Error Correction Framework**: Chen et al. (2025). "A Redundancy-Enhanced Framework for Error Correction in Named Entity Recognition." OpenReview. https://openreview.net/forum?id=2jFWhxJE5pQ

5. **Multilingual E5**: Wang et al. (2024). "Multilingual E5 Text Embeddings: A Technical Report." arXiv:2402.05672. https://arxiv.org/abs/2402.05672

6. **Legal-Embed**: Wasserstoff-AI. (2024). "Legal-Embed-intfloat-multilingual-e5-large-instruct." HuggingFace. https://huggingface.co/Wasserstoff-AI/Legal-Embed-intfloat-multilingual-e5-large-instruct

---

## 6. Errori di Classificazione Identificati (Audit)

Analisi del file `auditoria.md` dal documento STSJ ICAN 3407/2025:

| Entità | Tipo Assegnato | Tipo Corretto | Pattern |
|--------|----------------|---------------|---------|
| `"10/10/2025"` | ORGANIZATION (Org_038) | DATE | Data confusa con codice |
| `"05-11-2024"` | ORGANIZATION | DATE | Data nel formato DD-MM-YYYY |
| `"Pura"` | LOCATION (Lugar_001) | PERSON_NAME | Nome corto senza onorifico |
| `"Finalmente"` | ORGANIZATION (Org_012) | NON PII | Avverbio in maiuscolo |
| `"Terminaba"` | ORGANIZATION (Org_017) | NON PII | Verbo in maiuscolo |
| `"Quien"` | ORGANIZATION | NON PII | Pronome in maiuscolo |
| `"Whatsapp"` | PERSON | ORGANIZATION/PLATFORM | Nome piattaforma |

**Pattern principale identificato**: Il modello RoBERTa classifica come ORGANIZATION qualsiasi parola in maiuscolo all'inizio di frase che non riconosce chiaramente come un altro tipo.

---

## Documenti Correlati

| Documento | Relazione |
|-----------|-----------|
| `auditoria.md` | Fonte degli errori di classificazione analizzati |
| `docs/PLAN_CORRECCION_AUDITORIA.md` | Piano di correzione precedente (7 problemi identificati) |
| `ml/docs/reports/2026-02-07_evaluacion_propuesta_embeddings_ragnr.md` | Valutazione precedente degli embedding (classificazione documenti) |
| `ml/docs/reports/2026-02-07_embeddings_roadmap_document_classification.md` | Roadmap degli embedding per classificazione |
| `ml/README.md` | Istruzioni ML (formato report) |

---

## Prossimi Passi

1. [ ] Scaricare modello `intfloat/multilingual-e5-large` (~1.1GB)
2. [ ] Costruire dataset di esempi per tipo (PERSON_NAME, ORGANIZATION, DATE, LOCATION)
3. [ ] Implementare `EntityTypeValidator` in `infrastructure/nlp/validators/`
4. [ ] Calcolare e persistere centroidi per tipo
5. [ ] Integrare validatore nella pipeline NER esistente
6. [ ] Valutare riduzione errori su set di validazione
7. [ ] (Opzionale) Valutare `Legal-Embed` vs `multilingual-e5-large`

---

```
Versione: 1.0.0
Autor: AlexAlves87
Tempo di ricerca: ~15 min
```
